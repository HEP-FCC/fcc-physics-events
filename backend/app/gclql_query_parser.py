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
            # Try to search the dataset columns
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
        self, schema_mapping: dict[str, str], global_search_fields: list[str] = None
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

        clauses = []
        for field_name in self.global_search_fields:
            self.param_index += 1
            placeholder = f"${self.param_index}"
            clauses.append(f"{field_name} ILIKE {placeholder}")
            self.params.append(f"%{node.value}%")

        if not clauses:
            raise ValueError("Global search used, but no fields configured for it.")
        return "(" + " OR ".join(clauses) + ")"


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
            ast = cast(
                AstNode, self.transformer.transform(self.parser.parse(query_string))
            )
        except exceptions.LarkError as e:
            raise ValueError(f"Invalid query syntax: {e}") from e

        global_search_fields = self._build_dynamic_global_search_fields()
        self.translator.reset(self.schema_mapping, global_search_fields)
        where_clause = self.translator.translate(ast)
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

                return f"ORDER BY {json_field} {sort_order.upper()}"

        # Handle regular fields using the schema mapping
        field_obj = Field((sort_by,))
        try:
            sql_field = field_obj.to_sql(self.schema_mapping)
            return f"ORDER BY {sql_field} {sort_order.upper()}"
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
