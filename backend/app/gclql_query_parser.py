"""
A Python module to parse a query language and translate it into PostgreSQL queries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
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
    comparison: field OP value?
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


def parse_date_string(date_str: str) -> datetime:
    """
    Parse a date string in various formats to a datetime object.
    Supports formats like:
    - "2025-07-20" (date only)
    - "2025-07-20 15:30:00" (date and time)
    - "2025-07-20T15:30:00" (ISO format)
    """
    # Remove quotes if present
    date_str = date_str.strip("\"'")

    # List of supported formats
    formats = [
        "%Y-%m-%d",  # "2025-07-20"
        "%Y-%m-%d %H:%M:%S",  # "2025-07-20 15:30:00"
        "%Y-%m-%dT%H:%M:%S",  # "2025-07-20T15:30:00"
        "%Y-%m-%d %H:%M",  # "2025-07-20 15:30"
        "%Y-%m-%dT%H:%M",  # "2025-07-20T15:30"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # If none of the formats work, raise an error
    raise ValueError(f"Unable to parse date string: {date_str}")


@dataclass(frozen=True)
class Field:
    parts: tuple[str, ...]

    def to_sql(
        self,
        schema_mapping: dict[str, str],
        value: Any = None,
        op: str | None = None,
        available_metadata_fields: set[str] | None = None,
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
            elif available_metadata_fields and base_field in available_metadata_fields:
                # AUTO-DETECT: If field doesn't exist as regular column but exists in metadata,
                # automatically treat it as metadata.{field}
                logger.debug("Auto-detecting metadata field: %s", base_field)

                # Construct metadata field access
                metadata_column = schema_mapping.get("metadata", "d.metadata")
                json_path_parts = self.parts  # Use all parts for nested access

                if len(json_path_parts) == 1:
                    # Simple metadata field: field -> metadata.field
                    json_field = f"{metadata_column}->>'{json_path_parts[0]}'"
                else:
                    # Nested metadata field: field.sub -> metadata.field.sub
                    path_expression = "->".join(
                        [f"'{part}'" for part in json_path_parts[:-1]]
                    )
                    json_field = f"{metadata_column}->{path_expression}->>'{json_path_parts[-1]}'"

                # Handle numeric casting for comparison operators
                if (
                    value is not None
                    and isinstance(value, int | float)
                    and op in ("=", "!=", ">", "<", ">=", "<=", ":")
                ):
                    json_field = f"({json_field})::numeric"

                return json_field
            else:
                # Try to search the dataset columns directly
                sql_column = f"d.{base_field}"

        # Handle explicit metadata fields (metadata.field syntax)
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
    is_quoted: bool = False


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
        # The item is already transformed by other rules (e.g., global_search)
        return i[0]

    def comparison(self, i: list[Any]) -> Comparison:
        # Handle optional value: [field, op] or [field, op, value]
        if len(i) == 2:
            # No value provided (e.g., "last_edited_at:")
            return Comparison(field=i[0], op=str(i[1]), value=None)
        else:
            # Value provided (e.g., "last_edited_at: somevalue")
            return Comparison(field=i[0], op=str(i[1]), value=i[2])

    def global_search(self, i: list[Any]) -> GlobalSearch:
        # The value is already processed by simple_value, which is the first item in the list
        processed_value = i[0]

        # Check if the value was originally quoted (comes as a tuple from simple_value)
        if isinstance(processed_value, tuple) and processed_value[0] == "quoted":
            is_quoted = True
            value = processed_value[1]
        else:
            is_quoted = False
            value = str(processed_value)

        logger.debug(
            "global_search - processed_value: %s, is_quoted: %s, value: %s",
            processed_value,
            is_quoted,
            value,
        )

        return GlobalSearch(value=value, is_quoted=is_quoted)

    def field(self, i: list[Any]) -> Field:
        return Field(parts=tuple(p.value for p in i))

    def value(self, i: list[Any]) -> float | str | Any:
        processed = i[0]
        # Handle the quoted tuple from simple_value
        if isinstance(processed, tuple) and processed[0] == "quoted":
            return processed[1]  # Return just the value part
        return processed

    def simple_value(self, i: list[Any]) -> float | str | Any:
        v = i[0]
        if hasattr(v, "type"):
            if v.type == "ESCAPED_STRING":
                # Return a tuple to preserve the information that this was quoted
                return ("quoted", v.value[1:-1])
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
        self.available_metadata_fields: set[str] = (
            set()
        )  # Store available metadata fields
        self.params: list[Any] = []
        self.param_index = 0

    def reset(
        self,
        schema_mapping: dict[str, str],
        global_search_fields: list[str] | None = None,
        available_metadata_fields: set[str] | None = None,
    ) -> None:
        self.schema_mapping = schema_mapping
        if global_search_fields is not None:
            self.global_search_fields = global_search_fields
        if available_metadata_fields is not None:
            self.available_metadata_fields = available_metadata_fields
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
        sql_field = node.field.to_sql(
            self.schema_mapping, node.value, node.op, self.available_metadata_fields
        )
        op = node.op
        value = node.value

        # Handle the special :* operator for field existence
        if op == ":" and value == "*":
            return self._translate_field_exists(node.field, sql_field)

        # Special handling for last_edited_at field
        is_last_edited_at = node.field.parts[
            0
        ] == "last_edited_at" or sql_field.endswith("last_edited_at")

        self.param_index += 1
        placeholder = f"${self.param_index}"

        if op == ":" or op == "=":
            if op == ":":
                if is_last_edited_at and (value == "" or value is None):
                    # Special case: last_edited_at: (empty value) means "show only edited entities"
                    # Don't increment param_index or add to params since we're not using a placeholder
                    self.param_index -= (
                        1  # Decrement since we incremented above but won't use it
                    )
                    return f"{sql_field} IS NOT NULL"
                else:
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

        # Special handling for last_edited_at: parse date strings to datetime objects
        if (
            is_last_edited_at
            and isinstance(param_value, str)
            and op in ("=", "!=", ">", "<", ">=", "<=")
        ):
            try:
                param_value = parse_date_string(param_value)
            except ValueError as e:
                logger.error("Error parsing date string '%s': %s", param_value, e)
                # If parsing fails, keep as string and let PostgreSQL handle it
                pass

        self.params.append(param_value)

        # For last_edited_at comparison operations, add NULL check
        if is_last_edited_at and op in (">", "<", ">=", "<=", "!="):
            return f"({sql_field} IS NOT NULL AND {sql_field} {sql_op} {placeholder})"
        else:
            return f"{sql_field} {sql_op} {placeholder}"

    def _translate_field_exists(self, field: Any, sql_field: str) -> str:
        """
        Translate field existence checks (:* operator) to appropriate SQL.
        For regular fields, checks if NOT NULL.
        For JSON fields, checks if the key exists in the JSON object.
        """
        # Check if this is a metadata (JSON) field (explicit or auto-detected)
        if (field.parts[0] == "metadata" and len(field.parts) > 1) or (
            field.parts[0] in self.available_metadata_fields
        ):
            # Handle auto-detected metadata fields
            if field.parts[0] in self.available_metadata_fields:
                json_path = field.parts  # field.sub becomes ["field", "sub"]
            else:
                # Handle explicit metadata.field syntax
                json_path = field.parts[
                    1:
                ]  # metadata.field.sub becomes ["field", "sub"]

            if len(json_path) == 1:
                # Simple JSON key: metadata.key or auto-detected key
                # Use JSONB ? operator to check if key exists
                self.param_index += 1
                placeholder = f"${self.param_index}"
                self.params.append(json_path[0])
                return f"d.metadata ? {placeholder}"
            else:
                # Nested JSON key: metadata.nested.key or auto-detected nested.key
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
        logger.debug(
            "Global search for: '%s' (quoted: %s)", search_value, node.is_quoted
        )

        # Use the new helper to build the search clause
        where_clause, placeholder = self._build_global_search_clause(
            search_value, node.is_quoted, self.global_search_fields, self.param_index
        )

        # Update parameter tracking
        if placeholder:
            self.param_index += 1
            self.params.append(search_value)

        logger.debug("Global search generated clause: %s", where_clause)
        logger.debug("Global search parameter: '%s'", search_value)
        return where_clause

    def _build_search_condition(
        self, field_name: str, placeholder: str, is_quoted: bool
    ) -> str:
        """
        Build a search condition for a given field based on whether the search term is quoted.

        Args:
            field_name: The SQL field name to search in
            placeholder: The parameter placeholder (e.g., "$1")
            is_quoted: Whether the original search term was quoted

        Returns:
            A SQL condition string for this field
        """
        if is_quoted:
            # For quoted strings, use simple substring search
            return f"{field_name} ILIKE '%' || {placeholder} || '%'"
        else:
            # For unquoted terms, use similarity search
            if field_name == "jsonb_values_to_text(d.metadata)":
                # Use word_similarity for better phrase matching within metadata text
                return f"word_similarity({placeholder}, {field_name}) > 0.4"
            else:
                # Use similarity() for shorter text fields like names
                return f"similarity({placeholder}, {field_name}) > 0.6"

    def _build_global_search_clause(
        self,
        search_term: str,
        is_quoted: bool,
        field_list: list[str],
        param_offset: int = 0,
    ) -> tuple[str, str]:
        """
        Build a global search clause for a given search term across specified fields.

        Args:
            search_term: The term to search for
            is_quoted: Whether the search term was originally quoted
            field_list: List of field names to search in
            param_offset: Starting parameter index offset

        Returns:
            Tuple of (WHERE clause, parameter placeholder used)
        """
        if not search_term.strip():
            return "TRUE", ""

        param_index = param_offset + 1
        placeholder = f"${param_index}"

        conditions = []
        for field_name in field_list:
            conditions.append(
                self._build_search_condition(field_name, placeholder, is_quoted)
            )

        if not conditions:
            return "TRUE", ""

        where_clause = f"({' OR '.join(conditions)})"
        return where_clause, placeholder


class QueryParser:
    def __init__(self, database: Database):
        self.database = database
        self.schema_mapping: dict[str, str] = {}
        self.available_metadata_fields: set[str] = (
            set()
        )  # Store available metadata fields
        self.parser = Lark(QUERY_LANGUAGE_GRAMMAR, start="start", parser="lalr")
        self.transformer = AstTransformer()
        self.translator = SqlTranslator()

        # Dynamic FROM and JOINs will be built during setup
        self.from_and_joins = ""
        self.navigation_analysis: dict[str, Any] = {}
        self.entity_aliases: dict[str, str] = {}  # Store entity_key -> alias mapping

    async def setup(self) -> None:
        self.schema_mapping = await self.database.generate_schema_mapping()
        self.available_metadata_fields = await self._fetch_available_metadata_fields()

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

    async def _fetch_available_metadata_fields(self) -> set[str]:
        """Fetch all available metadata field names from the database."""
        main_table = config["application"]["main_table"]

        async with self.database.session() as conn:
            # Get top-level metadata fields
            metadata_query = f"""
                SELECT DISTINCT jsonb_object_keys(metadata) as metadata_key
                FROM {main_table}
                WHERE metadata IS NOT NULL
                AND metadata != 'null'::jsonb
                ORDER BY metadata_key
            """

            # Get nested metadata fields (one level deep)
            nested_metadata_query = f"""
                SELECT DISTINCT
                    parent_key || '.' || child_key as nested_key
                FROM (
                    SELECT
                        parent_key,
                        jsonb_object_keys(parent_value) as child_key
                    FROM (
                        SELECT
                            key as parent_key,
                            value as parent_value
                        FROM {main_table}, jsonb_each(metadata)
                        WHERE metadata IS NOT NULL
                        AND metadata != 'null'::jsonb
                        AND jsonb_typeof(value) = 'object'
                    ) nested_objects
                ) nested_keys
                ORDER BY nested_key
            """

            try:
                metadata_keys = await conn.fetch(metadata_query)
                nested_keys = await conn.fetch(nested_metadata_query)

                # Combine all metadata field names
                all_fields = set()

                # Add top-level fields
                for row in metadata_keys:
                    all_fields.add(row["metadata_key"])

                # Add nested fields
                for row in nested_keys:
                    all_fields.add(row["nested_key"])

                logger.debug(
                    f"Found {len(all_fields)} available metadata fields: {sorted(all_fields)}"
                )
                return all_fields

            except Exception as e:
                logger.error(f"Failed to fetch metadata fields: {e}")
                return set()

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
        This method treats the entire query as a single search term for fuzzy matching.
        """
        # Clean up the query string - remove quotes and operators, keep the actual search content

        # Extract quoted strings first (these are likely the actual search terms)
        quoted_strings = re.findall(r'["\']([^"\']+)["\']', query_string)

        if quoted_strings:
            # If we have quoted strings, use the first one as the search term
            search_term = quoted_strings[0].strip()
            is_quoted = True
        else:
            # If no quoted strings, clean up the query by removing operators
            cleaned = re.sub(
                r"\b(AND|OR|NOT)\b", " ", query_string, flags=re.IGNORECASE
            )
            cleaned = re.sub(
                r'\w+\s*=\s*["\'][^"\']*["\']', " ", cleaned
            )  # Remove field=value pairs
            cleaned = re.sub(r"\s+", " ", cleaned).strip()  # Normalize whitespace
            search_term = cleaned if cleaned else query_string.strip()
            is_quoted = False

        logger.debug(
            "Fuzzy search extracted term: '%s' (quoted: %s)", search_term, is_quoted
        )

        # Build the field list for fuzzy search
        field_list = ["d.name", "jsonb_values_to_text(d.metadata)"] + [
            f"{self.entity_aliases[entity_key]}.{table_info['name_column']}"
            for entity_key, table_info in self.navigation_analysis[
                "navigation_tables"
            ].items()
        ]

        # Use the centralized helper to build the search clause
        where_clause, _ = self.translator._build_global_search_clause(
            search_term, is_quoted, field_list, 0
        )
        params = [search_term] if search_term.strip() else []

        logger.debug("Generated fuzzy search WHERE clause: %s", where_clause)
        logger.debug("Fuzzy search parameters: %s", params)

        return where_clause, params

    def _build_hybrid_search_clause(self, query_string: str) -> tuple[str, list[Any]]:
        """
        Build a hybrid search clause that combines exact matches for valid parts
        with fuzzy search for the parts that failed to parse.
        """

        logger.debug("Building hybrid search for: '%s'", query_string)

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
                logger.debug("Trying to parse part: '%s'", part)
                ast = cast(AstNode, self.transformer.transform(self.parser.parse(part)))

                # If successful, translate to SQL
                clause = self.translator.translate(ast)
                valid_clauses.append(clause)
                logger.debug("Successfully parsed part: '%s' -> %s", part, clause)

            except exceptions.LarkError:
                # If this part fails, add it to fuzzy search terms
                logger.debug("Failed to parse part: '%s', adding to fuzzy search", part)
                fuzzy_search_terms.append(part)

        # Collect parameters from valid clauses
        all_params.extend(self.translator.params)
        param_index = len(all_params)

        # Build fuzzy search clause for failed parts
        if fuzzy_search_terms:
            # Combine all fuzzy search terms into one search phrase
            fuzzy_phrase = " ".join(fuzzy_search_terms).strip()
            logger.debug("Fuzzy search phrase: '%s'", fuzzy_phrase)

            # Check if the original query had quoted strings
            quoted_strings = re.findall(r'["\']([^"\']+)["\']', query_string)
            is_quoted = len(quoted_strings) > 0

            # Use the centralized helper to build the search clause
            fuzzy_clause, _ = self.translator._build_global_search_clause(
                fuzzy_phrase, is_quoted, global_search_fields, param_index
            )
            all_params.append(fuzzy_phrase)

            if fuzzy_clause != "TRUE":
                valid_clauses.append(fuzzy_clause)
                logger.debug("Added fuzzy clause: %s", fuzzy_clause)

        # Combine all clauses with AND
        if valid_clauses:
            where_clause = f"({' AND '.join(valid_clauses)})"
        else:
            where_clause = "TRUE"

        logger.debug("Final hybrid WHERE clause: %s", where_clause)
        logger.debug("Final hybrid parameters: %s", all_params)

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
            logger.debug("Attempting to parse query: '%s'", query_string)
            ast = cast(
                AstNode, self.transformer.transform(self.parser.parse(query_string))
            )
            logger.debug("Query parsed successfully. AST type: %s", type(ast))

            # If parsing succeeds, use the normal translation
            global_search_fields = self._build_dynamic_global_search_fields()
            self.translator.reset(
                self.schema_mapping,
                global_search_fields,
                self.available_metadata_fields,
            )
            where_clause = self.translator.translate(ast)

            logger.debug("Generated WHERE clause: %s", where_clause)
            logger.debug("Generated parameters: %s", self.translator.params)

        except exceptions.LarkError as e:
            # If parsing fails, try to parse valid parts and apply fuzzy search to the rest
            logger.debug("Query parsing failed, using hybrid approach: %s", e)

            try:
                where_clause, params = self._build_hybrid_search_clause(query_string)
                logger.debug("Hybrid search completed successfully")
            except Exception as hybrid_error:
                logger.error("Hybrid search failed: %s", hybrid_error)
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
            logger.debug("Hybrid search final query: %s", select_query)
            logger.debug("Hybrid search final params: %s", params)
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
            sql_field = field_obj.to_sql(
                self.schema_mapping,
                available_metadata_fields=self.available_metadata_fields,
            )
            # Add secondary sort by primary key to ensure deterministic ordering
            # This prevents the same entity from appearing on multiple pages when there are ties
            primary_key_field = (
                f"d.{self.navigation_analysis['main_table_schema']['primary_key']}"
            )
            return f"ORDER BY {sql_field} {sort_order.upper()}, {primary_key_field} {sort_order.upper()}"
        except Exception as e:
            logger.error("Could not find the column to sort by: %s", e)
            raise e
