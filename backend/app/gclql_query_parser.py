"""
A Python module to parse a query language and translate it into PostgreSQL queries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from lark import Lark, Token, Transformer, exceptions

from app.storage.database import Database
from app.utils import get_config, get_logger

logger = get_logger()
config = get_config()

QUERY_LANGUAGE_GRAMMAR = r"""
    ?start: expr
    ?expr: expr OR term | term
    ?term: term AND factor | factor
    ?factor: NOT item | item
    ?item: "(" expr ")" | comparison | global_search
    global_search: simple_value
    comparison: field OP value
    field: IDENTIFIER ("." IDENTIFIER)*
    value: simple_value
    simple_value: ESCAPED_STRING | SIGNED_NUMBER | IDENTIFIER | ASTERISK
    AND.2: "AND"
    OR.2: "OR"
    NOT.2: "NOT"
    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_-]*/
    ASTERISK: "*"
    OP: "=" | "!=" | ">" | "<" | ">=" | "<=" | ":" | "=~" | "!~"
    %import common.ESCAPED_STRING
    %import common.SIGNED_NUMBER
    %import common.WS
    %ignore WS
"""


@dataclass(frozen=True)
class Field:
    parts: tuple[str, ...]

    def to_sql(
        self, schema_mapping: dict[str, str], value: Any = None, op: str | None = None
    ) -> str:
        base_field = self.parts[0]
        if base_field[-5:] == "_name":
            base_field = base_field[:-5]

        sql_column = schema_mapping.get(base_field)

        if not sql_column:
            # Check if this might be a foreign key field (entity reference)
            # Common entity fields that map to foreign keys in the dataset table
            entity_fields = {
                "accelerator",
                "stage",
                "campaign",
                "detector",
                "software_stack",
            }
            if base_field in entity_fields:
                # Map to the foreign key column in the dataset table
                sql_column = f"d.{base_field}_id"
            else:
                # Try to search the dataset columns directly
                sql_column = f"d.{base_field}"

        # Hardcoded "metadata" field name required in the db schema
        if base_field == "metadata" and len(self.parts) > 1:
            json_path_parts = self.parts[1:]
            path_expression = "->".join([f"'{part}'" for part in json_path_parts[:-1]])

            # Determine if we need to cast based on the value type and operator
            json_field = (
                f"{sql_column}->{path_expression}->>'{json_path_parts[-1]}'"
                if len(json_path_parts) > 1
                else f"{sql_column}->>'{json_path_parts[0]}'"
            )

            # If comparing with a number and using equality/comparison operators, cast to numeric
            if (
                value is not None
                and isinstance(value, int | float)
                and op in ("=", "!=", ">", "<", ">=", "<=", ":")
            ):
                # Cast the JSON text value to numeric for comparison
                return f"({json_field})::numeric"

            return json_field
        return sql_column


@dataclass(frozen=True)
class Comparison:
    field: Field
    op: str
    value: Any


@dataclass(frozen=True)
class GlobalSearch:
    value: str


@dataclass(frozen=True)
class And:
    left: Any
    right: Any


@dataclass(frozen=True)
class Or:
    left: Any
    right: Any


@dataclass(frozen=True)
class Not:
    term: Any


AstNode = Comparison | GlobalSearch | And | Or | Not


class AstTransformer(Transformer[Token, AstNode]):
    def expr(self, i: list[Any]) -> Or | Any:
        return Or(left=i[0], right=i[2]) if len(i) > 1 else i[0]

    def term(self, i: list[Any]) -> And | Any:
        return And(left=i[0], right=i[2]) if len(i) > 1 else i[0]

    def factor(self, i: list[Any]) -> Not | Any:
        return Not(term=i[1]) if len(i) > 1 else i[0]

    def item(self, i: list[Any]) -> Any:
        return i[0]

    def comparison(self, i: list[Any]) -> Comparison:
        return Comparison(field=i[0], op=str(i[1]), value=i[2])

    def global_search(self, i: list[Any]) -> GlobalSearch:
        return GlobalSearch(value=i[0])

    def field(self, i: list[Any]) -> Field:
        return Field(parts=tuple(p.value for p in i))

    def value(self, i: list[Any]) -> float | str | Any:
        return i[0]

    def simple_value(self, i: list[Any]) -> float | str | Any:
        v = i[0]
        if hasattr(v, "type"):
            if v.type == "ESCAPED_STRING":
                return v.value[1:-1]
            if v.type == "SIGNED_NUMBER":
                return float(v.value) if "." in v.value else int(v.value)
            if v.type == "IDENTIFIER":
                return str(v.value)
            if v.type == "ASTERISK":
                return "*"
        return str(v)


class SqlTranslator:
    def __init__(self) -> None:
        self.schema_mapping: dict[str, str] = {}
        self.global_search_fields: list[str] = []  # Will be set dynamically
        self.params: list[Any] = []
        self.param_index = 0

    def reset(
        self,
        schema_mapping: dict[str, str],
        global_search_fields: list[str] | None = None,
    ) -> None:
        self.schema_mapping = schema_mapping
        if global_search_fields is not None:
            self.global_search_fields = global_search_fields
        self.params = []
        self.param_index = 0

    def translate(self, node: AstNode) -> str:
        if isinstance(node, Comparison):
            return self._translate_comparison(node)
        if isinstance(node, GlobalSearch):
            return self._translate_global_search(node)
        if isinstance(node, Not):
            return f"NOT ({self.translate(node.term)})"
        if isinstance(node, And):
            return f"({self.translate(node.left)} AND {self.translate(node.right)})"
        if isinstance(node, Or):
            return f"({self.translate(node.left)} OR {self.translate(node.right)})"
        raise TypeError(f"Unknown AST node type: {type(node)}")

    def _translate_comparison(self, node: Comparison) -> str:
        sql_field = node.field.to_sql(self.schema_mapping, node.value, node.op)
        op = node.op
        value = node.value

        # Handle the special :* operator for field existence
        if op == ":" and value == "*":
            return self._translate_field_exists(node.field, sql_field)

        self.param_index += 1
        placeholder = f"${self.param_index}"

        if op == ":" or op == "=":
            if op == ":":
                # Substring match using ILIKE
                sql_op, param_value = "ILIKE", f"%{value}%"
            else:
                # Exact match
                sql_op, param_value = "=", value
        elif op == "=~":
            # Case-insensitive regular expression match
            sql_op, param_value = "~*", value
        elif op == "!~":
            # Case-insensitive regular expression NOT match
            sql_op, param_value = "!~*", value
        else:
            # Standard comparison operators: !=, >, <, >=, <=
            sql_op, param_value = op, value

        self.params.append(param_value)
        return f"{sql_field} {sql_op} {placeholder}"

    def _translate_field_exists(self, field: Any, sql_field: str) -> str:
        """
        Translate field existence checks (:* operator) to appropriate SQL.
        For regular fields, checks if NOT NULL.
        For JSON fields, checks if the key exists in the JSON object.
        """
        # Check if this is a metadata (JSON) field
        if field.parts[0] == "metadata" and len(field.parts) > 1:
            # For JSON fields, check if the key exists using the ? operator
            json_path = field.parts[1:]

            if len(json_path) == 1:
                # Simple JSON key: metadata.key
                # Use JSONB ? operator to check if key exists
                self.param_index += 1
                placeholder = f"${self.param_index}"
                self.params.append(json_path[0])
                return f"d.metadata ? {placeholder}"
            else:
                # Nested JSON key: metadata.nested.key
                # Check if the nested path exists using JSONB path functions
                path_expression = ".".join(json_path)
                self.param_index += 1
                placeholder = f"${self.param_index}"
                self.params.append(f"$.{path_expression}")
                return f"jsonb_path_exists(d.metadata, {placeholder})"
        else:
            # For regular fields, just check if NOT NULL
            return f"{sql_field} IS NOT NULL"

    def _translate_global_search(self, node: GlobalSearch) -> str:
        # If the search value is '*' or empty, do not filter (all values are good)
        if str(node.value).strip() in ("*", ""):
            return "TRUE"

        search_value = str(node.value).strip()
        print(f"DEBUG: Global search for: '{search_value}'")
        logger.info(f"Global search for: '{search_value}'")

        # Use one parameter for all field searches to avoid duplication
        self.param_index += 1
        placeholder = f"${self.param_index}"
        self.params.append(search_value)

        # Check if this is likely a quoted string vs unquoted identifier
        # Quoted strings should use exact substring search (ILIKE)
        # Unquoted identifiers should use fuzzy similarity search
        # We can detect this by checking if the search contains spaces or special chars
        # Single words without quotes are parsed as identifiers and should use fuzzy search
        contains_spaces_or_special = " " in search_value or any(
            c in search_value for c in ["-", ".", "_"]
        )

        print(f"DEBUG: Contains spaces or special chars: {contains_spaces_or_special}")

        clauses = []
        for field_name in self.global_search_fields:
            if contains_spaces_or_special:
                # Multi-word phrases (likely from quoted strings) - use exact substring search
                clauses.append(f"{field_name} ILIKE '%' || {placeholder} || '%'")
            else:
                # Single words (likely unquoted identifiers) - use similarity for fuzzy matching
                # similarity() is better than strict_word_similarity() for single word typos
                # Use lower threshold (0.6) for better fuzzy matching of single words
                clauses.append(f"similarity({placeholder}, {field_name}) > 0.6")

        if not clauses:
            raise ValueError("Global search used, but no fields configured for it.")

        result = "(" + " OR ".join(clauses) + ")"
        print(f"DEBUG: Global search generated clause: {result}")
        logger.info(f"Global search generated clause: {result}")
        logger.info(f"Global search parameter: '{search_value}'")
        return result


class QueryParser:
    def __init__(self, database: Database):
        self.database = database
        self.schema_mapping: dict[str, str] = {}
        self.parser = Lark(QUERY_LANGUAGE_GRAMMAR, start="start", parser="lalr")
        self.transformer = AstTransformer()
        self.translator = SqlTranslator()

        # Dynamic FROM and JOINs will be built during setup
        self.from_and_joins = ""
        self.navigation_analysis: dict[str, Any] = {}
        self.entity_aliases: dict[str, str] = {}  # Store entity_key -> alias mapping

    async def setup(self) -> None:
        self.schema_mapping = await self.database.generate_schema_mapping()

        # Get navigation structure analysis to build dynamic JOINs
        from app.schema_discovery import get_schema_discovery

        async with self.database.session() as conn:
            schema_discovery = await get_schema_discovery(conn)
            self.navigation_analysis = (
                await schema_discovery.analyze_navigation_structure(
                    config["application"]["main_table"]
                )
            )

        # Build dynamic FROM and JOIN clauses
        self._build_dynamic_joins()

    def _build_dynamic_joins(self) -> None:
        """Build FROM and JOIN clauses dynamically based on schema analysis."""
        joins = [f"FROM {config['application']['main_table']} d"]
        used_aliases = {"d"}  # Track used aliases to avoid conflicts

        for entity_key, table_info in self.navigation_analysis[
            "navigation_tables"
        ].items():
            table_name = table_info["table_name"]
            primary_key = table_info["primary_key"]

            # Create unique alias from entity key
            alias = self._generate_unique_alias(entity_key, used_aliases)
            used_aliases.add(alias)
            self.entity_aliases[entity_key] = alias  # Store for later use

            join_clause = f"LEFT JOIN {table_name} {alias} ON d.{entity_key}_id = {alias}.{primary_key}"
            joins.append(" " * 12 + join_clause)

        self.from_and_joins = "\n".join(joins)

    def _generate_unique_alias(self, entity_key: str, used_aliases: set[str]) -> str:
        """Generate a unique alias for a table, avoiding conflicts."""
        # Start with first 3-4 characters
        base_alias = entity_key[:3] if len(entity_key) > 3 else entity_key

        # If already used, try first 4 characters
        if base_alias in used_aliases and len(entity_key) > 3:
            base_alias = entity_key[:4]

        # If still conflicts, add number suffix
        if base_alias in used_aliases:
            counter = 1
            while f"{base_alias}{counter}" in used_aliases:
                counter += 1
            base_alias = f"{base_alias}{counter}"

        return base_alias

    def _build_dynamic_select_fields(self) -> str:
        """Build dynamic SELECT fields for navigation entities."""
        select_fields = ["d.*"]

        for entity_key, table_info in self.navigation_analysis[
            "navigation_tables"
        ].items():
            name_column = table_info["name_column"]

            # Use the alias that was generated during join building
            alias = self.entity_aliases[entity_key]

            select_field = f"{alias}.{name_column} as {entity_key}_name"
            select_fields.append(" " * 20 + select_field)

        return ",\n".join(select_fields)

    def _build_dynamic_global_search_fields(self) -> list[str]:
        """Build dynamic global search fields for navigation entities."""
        global_search_fields = [
            "d.name",  # Dataset name
            "jsonb_values_to_text(d.metadata)",  # Metadata values
        ]

        # Add name fields from all navigation tables using their aliases
        for entity_key, table_info in self.navigation_analysis[
            "navigation_tables"
        ].items():
            name_column = table_info["name_column"]
            alias = self.entity_aliases[entity_key]
            global_search_fields.append(f"{alias}.{name_column}")

        return global_search_fields

    def _build_fuzzy_search_clause(self, query_string: str) -> tuple[str, list[Any]]:
        """
        Build a fuzzy search clause using PostgreSQL's trigram similarity.
        Uses the similarity() function with a 60% similarity threshold (0.6).

        This method treats the entire query as a single search term for fuzzy matching.
        """
        # Clean up the query string - remove quotes and operators, keep the actual search content
        import re

        # Extract quoted strings first (these are likely the actual search terms)
        quoted_strings = re.findall(r'["\']([^"\']+)["\']', query_string)

        if quoted_strings:
            # If we have quoted strings, use the first one as the search term
            # (assumes the failing part is what we want to search for)
            search_term = quoted_strings[0].strip()
        else:
            # If no quoted strings, clean up the query by removing operators
            # Remove common operators and field assignments
            cleaned = re.sub(
                r"\b(AND|OR|NOT)\b", " ", query_string, flags=re.IGNORECASE
            )
            cleaned = re.sub(
                r'\w+\s*=\s*["\'][^"\']*["\']', " ", cleaned
            )  # Remove field=value pairs
            cleaned = re.sub(r"\s+", " ", cleaned).strip()  # Normalize whitespace
            search_term = cleaned

        # If we end up with empty search term, use the original query
        if not search_term:
            search_term = query_string.strip()

        print(f"DEBUG: Fuzzy search extracted term: '{search_term}'")
        logger.info(f"Fuzzy search for term: '{search_term}'")
        logger.info(f"Original query string: '{query_string}'")
        logger.info(f"Quoted strings found: {quoted_strings}")
        logger.info(f"Final search term: '{search_term}'")

        # Build fuzzy search conditions for the single search term
        # Use similarity() for fuzzy substring matching instead of strict word boundaries
        # This is better for phrases that might appear as substrings in the text
        conditions = []
        params = []
        param_index = 0

        # Use one parameter for all field searches to avoid duplication
        param_index += 1
        placeholder = f"${param_index}"
        params.append(search_term)

        # Search in all fields using similarity with 0.6 threshold (more lenient than 0.6)
        for field_name in [
            "d.name",
            "jsonb_values_to_text(d.metadata)",
        ] + [
            f"{self.entity_aliases[entity_key]}.{table_info['name_column']}"
            for entity_key, table_info in self.navigation_analysis[
                "navigation_tables"
            ].items()
        ]:
            # For metadata, use word_similarity which is better for finding phrases within larger text
            if field_name == "jsonb_values_to_text(d.metadata)":
                # Use word_similarity for better phrase matching within metadata text
                # This finds "forxed to tau" similar to "forced to tau" even as substring
                conditions.append(f"word_similarity({placeholder}, {field_name}) > 0.6")
            else:
                # Use similarity() for other fields (shorter text)
                conditions.append(f"similarity({placeholder}, {field_name}) > 0.6")

        # Combine all conditions with OR (any field can match)
        if conditions:
            where_clause = f"({' OR '.join(conditions)})"
        else:
            where_clause = "TRUE"

        logger.info(f"Generated fuzzy search WHERE clause: {where_clause}")
        logger.info(f"Fuzzy search parameters: {params}")

        return where_clause, params

    def _build_hybrid_search_clause(self, query_string: str) -> tuple[str, list[Any]]:
        """
        Build a hybrid search clause that combines exact matches for valid parts
        with fuzzy search for the parts that failed to parse.

        This approach first applies exact filters, then fuzzy search within those results.
        """
        import re

        print(f"DEBUG: Building hybrid search for: '{query_string}'")

        # Split the query into parts separated by AND
        parts = re.split(r"\s+AND\s+", query_string, flags=re.IGNORECASE)

        valid_clauses = []
        fuzzy_search_terms = []
        all_params = []

        global_search_fields = self._build_dynamic_global_search_fields()
        self.translator.reset(self.schema_mapping, global_search_fields)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            try:
                # Try to parse this individual part
                print(f"DEBUG: Trying to parse part: '{part}'")
                ast = cast(AstNode, self.transformer.transform(self.parser.parse(part)))

                # If successful, translate to SQL
                clause = self.translator.translate(ast)
                valid_clauses.append(clause)
                print(f"DEBUG: Successfully parsed part: '{part}' -> {clause}")

            except exceptions.LarkError:
                # If this part fails, add it to fuzzy search terms
                print(f"DEBUG: Failed to parse part: '{part}', adding to fuzzy search")
                fuzzy_search_terms.append(part)

        # Collect parameters from valid clauses
        all_params.extend(self.translator.params)
        param_index = len(all_params)

        # Build fuzzy search clause for failed parts
        if fuzzy_search_terms:
            # Combine all fuzzy search terms into one search phrase
            fuzzy_phrase = " ".join(fuzzy_search_terms).strip()
            print(f"DEBUG: Fuzzy search phrase: '{fuzzy_phrase}'")

            # Build fuzzy search conditions using similarity for fuzzy substring matching
            # This is better for phrases that might appear as substrings
            fuzzy_conditions = []
            param_index += 1
            placeholder = f"${param_index}"
            all_params.append(fuzzy_phrase)

            for field_name in global_search_fields:
                # For metadata, use word_similarity which is better for finding phrases within larger text
                if field_name == "jsonb_values_to_text(d.metadata)":
                    # Use word_similarity for better phrase matching within metadata text
                    # This finds "forxed to tau" similar to "forced to tau" even as substring
                    fuzzy_conditions.append(
                        f"word_similarity({placeholder}, {field_name}) > 0.6"
                    )
                else:
                    # Use similarity() for other fields (shorter text)
                    fuzzy_conditions.append(
                        f"similarity({placeholder}, {field_name}) > 0.6"
                    )

            if fuzzy_conditions:
                fuzzy_clause = f"({' OR '.join(fuzzy_conditions)})"
                valid_clauses.append(fuzzy_clause)
                print(f"DEBUG: Added fuzzy clause: {fuzzy_clause}")
                print(f"DEBUG: Fuzzy phrase parameter: '{fuzzy_phrase}'")

        # Combine all clauses with AND
        if valid_clauses:
            where_clause = f"({' AND '.join(valid_clauses)})"
        else:
            where_clause = "TRUE"

        print(f"DEBUG: Final hybrid WHERE clause: {where_clause}")
        print(f"DEBUG: Final hybrid parameters: {all_params}")

        return where_clause, all_params

    def parse_query(
        self,
        query_string: str,
        sort_by: str = "last_edited_at",
        sort_order: str = "desc",
    ) -> tuple[str, str, list[Any]]:
        if not self.schema_mapping:
            raise RuntimeError("QueryParser not set up.")

        if not query_string.strip():
            select_fields = self._build_dynamic_select_fields()
            select_query = f"""
                SELECT {select_fields}
                {self.from_and_joins}
                {self._build_order_by_clause(sort_by, sort_order)}
            """
            count_query = f"SELECT COUNT(*) FROM {config['application']['main_table']}"
            return count_query, select_query, []

        try:
            # Try to parse the query with the grammar
            print(f"DEBUG: Attempting to parse query: '{query_string}'")
            logger.info(f"Attempting to parse query: '{query_string}'")
            ast = cast(
                AstNode, self.transformer.transform(self.parser.parse(query_string))
            )
            print(f"DEBUG: Query parsed successfully. AST type: {type(ast)}")
            logger.info(f"Query parsed successfully. AST type: {type(ast)}")

            # If parsing succeeds, use the normal translation
            global_search_fields = self._build_dynamic_global_search_fields()
            self.translator.reset(self.schema_mapping, global_search_fields)
            where_clause = self.translator.translate(ast)
            print(f"DEBUG: Generated WHERE clause: {where_clause}")
            print(f"DEBUG: Generated parameters: {self.translator.params}")
            logger.info(f"Generated WHERE clause: {where_clause}")
            logger.info(f"Generated parameters: {self.translator.params}")

        except exceptions.LarkError as e:
            # If parsing fails, try to parse valid parts and apply fuzzy search to the rest
            print(f"DEBUG: Query parsing failed with error: {e}")
            logger.info(f"Query parsing failed, using hybrid approach: {e}")

            try:
                where_clause, params = self._build_hybrid_search_clause(query_string)
                print("DEBUG: Hybrid search completed successfully")
            except Exception as hybrid_error:
                print(f"DEBUG: Hybrid search failed with error: {hybrid_error}")
                logger.error(f"Hybrid search failed: {hybrid_error}")
                # Fallback to fuzzy search only
                where_clause, params = self._build_fuzzy_search_clause(query_string)

            select_fields = self._build_dynamic_select_fields()
            select_query = f"""
                SELECT {select_fields}
                {self.from_and_joins}
                WHERE {where_clause}
                {self._build_order_by_clause(sort_by, sort_order)}
            """
            count_query = f"SELECT COUNT(*) {self.from_and_joins} WHERE {where_clause}"
            print(f"DEBUG: Hybrid search final query: {select_query}")
            print(f"DEBUG: Hybrid search final params: {params}")
            return count_query, select_query, params

        select_fields = self._build_dynamic_select_fields()
        select_query = f"""
            SELECT {select_fields}
            {self.from_and_joins}
            WHERE {where_clause}
            {self._build_order_by_clause(sort_by, sort_order)}
        """
        count_query = f"SELECT COUNT(*) {self.from_and_joins} WHERE {where_clause}"

        logger.debug("COUNT_QUERY: %s", count_query)
        logger.debug("SELECT_QUERY: %s", select_query)
        return count_query, select_query, self.translator.params

    def _build_order_by_clause(self, sort_by: str, sort_order: str) -> str:
        """
        Builds the ORDER BY clause for the query with proper field mapping.
        Supports sorting by dataset fields, joined table fields, and metadata JSONB fields.
        """
        # Validate sort_order
        if sort_order.lower() not in ["asc", "desc"]:
            raise ValueError("sort_order must be 'asc' or 'desc'")

        # Handle metadata fields (e.g., "metadata.key" or "metadata.nested.key")
        if sort_by.startswith("metadata."):
            parts = sort_by.split(".", 1)  # Split into "metadata" and rest
            if len(parts) > 1:
                metadata_path = parts[1]
                # Split the metadata path by dots to handle nested keys
                path_parts = metadata_path.split(".")

                if len(path_parts) == 1:
                    # Simple metadata field: metadata.key
                    json_field = f"d.metadata->>{path_parts[0]!r}"
                else:
                    # Nested metadata field: metadata.nested.key
                    path_expression = "->".join(
                        [f"'{part}'" for part in path_parts[:-1]]
                    )
                    json_field = f"d.metadata->{path_expression}->>{path_parts[-1]!r}"

                # Add secondary sort by primary key for deterministic ordering
                # Get primary key from navigation analysis
                primary_key_field = (
                    f"d.{self.navigation_analysis['main_table_schema']['primary_key']}"
                )
                return f"ORDER BY {json_field} {sort_order.upper()}, {primary_key_field} {sort_order.upper()}"

        # Handle regular fields using the schema mapping
        field_obj = Field((sort_by,))
        try:
            sql_field = field_obj.to_sql(self.schema_mapping)
            # Add secondary sort by primary key to ensure deterministic ordering
            # This prevents the same entity from appearing on multiple pages when there are ties
            primary_key_field = (
                f"d.{self.navigation_analysis['main_table_schema']['primary_key']}"
            )
            return f"ORDER BY {sql_field} {sort_order.upper()}, {primary_key_field} {sort_order.upper()}"
        except Exception as e:
            logger.error("Could not find the column to sort by: %s", e)
            raise e
            # # If the field doesn't map, try direct dataset field access
            # # This handles cases like "dataset_id", "created_at", etc.
            # if sort_by in ["dataset_id", "created_at", "last_edited_at", "name"]:
            #     return f"ORDER BY d.{sort_by} {sort_order.upper()}"
            # elif sort_by in [
            #     "detector_name",
            #     "campaign_name",
            #     "stage_name",
            #     "accelerator_name",
            # ]:
            #     # These are already available in the SELECT clause
            #     return f"ORDER BY {sort_by} {sort_order.upper()}"
            # else:
            #     # Fallback: try to access the field directly
            #     return f"ORDER BY d.{sort_by} {sort_order.upper()}"
