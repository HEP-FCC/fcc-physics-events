"""
A Python module to parse Google Cloud Logging query language which we are shamelessly
using as our query language as it is already well defined and matured.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from lark import Lark, Token, Transformer, exceptions

from app.db.database import Database

# Define the GCP Logging grammar
gcp_logging_grammar = r"""
    ?start: expr

    // Grammar rules to enforce precedence: OR < AND < NOT
    ?expr: expr OR term | term
    ?term: term AND factor | factor
    ?factor: NOT item | item

    ?item: "(" expr ")" | comparison | global_search

    global_search: value  // A simple search term without a field

    comparison: field OP value
    field: CNAME ("." CNAME)*

    value: ESCAPED_STRING | SIGNED_NUMBER | UNQUOTED_STRING

    // By giving keywords a higher priority (e.g., .2), we ensure the lexer
    // correctly tokenizes them instead of matching them as a generic
    // CNAME or UNQUOTED_STRING. This is critical for parsing correctly.
    AND.2: "AND" | "and"
    OR.2: "OR" | "or"
    NOT.2: "NOT" | "not"

    UNQUOTED_STRING: /[a-zA-Z0-9_.*-][a-zA-Z0-9_.*-:]*/
    OP: "=" | "!=" | ">" | "<" | ">=" | "<=" | ":" | "~" | "!~"

    %import common.CNAME
    %import common.ESCAPED_STRING
    %import common.SIGNED_NUMBER
    %import common.WS
    %ignore WS
"""


# AST dataclasses
@dataclass(frozen=True)
class Field:
    """Represents a field, which can be a single name or a path (e.g., 'metadata.energy')."""

    parts: tuple[str, ...]

    def to_sql(self, schema_mapping: dict[str, str]) -> str:
        base_field = self.parts[0]

        if base_field not in schema_mapping:
            raise ValueError(f"Field '{base_field}' is not a valid queryable field.")

        sql_column = schema_mapping[base_field]

        if len(self.parts) == 1:
            return sql_column
        else:
            json_path_parts = self.parts[1:]

            if len(json_path_parts) > 1:
                path_expression = "->".join(
                    [f"'{part}'" for part in json_path_parts[:-1]]
                )
                return f"{sql_column}->{path_expression}->>'{json_path_parts[-1]}'"
            else:
                return f"{sql_column}->>'{json_path_parts[0]}'"


@dataclass(frozen=True)
class Comparison:
    """Represents a comparison operation (e.g., 'name="my-sample"')."""

    field: Field
    op: str
    value: Any


@dataclass(frozen=True)
class GlobalSearch:
    """Represents a global text search (a value without a field)."""

    value: str


@dataclass(frozen=True)
class And:
    """Represents a logical AND operation."""

    left: Any
    right: Any


@dataclass(frozen=True)
class Or:
    """Represents a logical OR operation."""

    left: Any
    right: Any


@dataclass(frozen=True)
class Not:
    """Represents a logical NOT operation."""

    term: Comparison | GlobalSearch | And | Or | Not


AstNode = Comparison | GlobalSearch | And | Or | Not


class AstTransformer(Transformer[Token, AstNode]):
    """
    Transforms the Lark parse tree into our custom AST (using the dataclasses).
    """

    def expr(self, items: list[Any]) -> Or | Any:
        if len(items) == 1:
            return items[0]
        return Or(left=items[0], right=items[2])

    def term(self, items: list[Any]) -> And | Any:
        if len(items) == 1:
            return items[0]
        return And(left=items[0], right=items[2])

    def factor(self, items: list[Any]) -> Not | Any:
        if len(items) == 1:
            return items[0]
        return Not(term=items[1])  # items are [NOT, item]

    def item(self, items: list[Any]) -> Any:
        return items[0]  # Just pass through the item inside (e.g., from parentheses)

    def comparison(self, items: list[Any]) -> Comparison:
        return Comparison(field=items[0], op=str(items[1]), value=items[2])

    def global_search(self, items: list[Any]) -> GlobalSearch:
        return GlobalSearch(value=items[0])

    def field(self, items: list[Any]) -> Field:
        return Field(parts=tuple(p.value for p in items))

    def value(self, items: list[Any]) -> float | str | Any:
        v = items[0]
        if hasattr(v, "type") and v.type == "ESCAPED_STRING":
            return v.value[1:-1]  # Remove quotes
        if hasattr(v, "type") and v.type == "SIGNED_NUMBER":
            return float(v.value) if "." in v.value else int(v.value)
        return str(v)


class SqlTranslator:
    """
    Translates an AST into a PostgreSQL query string and parameters.
    """

    def __init__(
        self,
        schema_mapping: dict[str, str] | None = None,
        global_search_fields: list[str] | None = None,
    ):
        self.schema_mapping = schema_mapping or {}
        self.global_search_fields = global_search_fields or []
        self.params: list[Any] = []
        self.param_index = 0

    def reset(
        self, schema_mapping: dict[str, str], global_search_fields: list[str]
    ) -> None:
        """Reset translator state for a new query."""
        self.schema_mapping = schema_mapping
        self.global_search_fields = global_search_fields
        self.params = []
        self.param_index = 0

    def translate(self, node: AstNode) -> str:
        """Entry point to start the translation."""
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
        sql_field = node.field.to_sql(self.schema_mapping)
        op = node.op
        value = node.value

        self.param_index += 1
        placeholder = f"${self.param_index}"

        if op == ":":
            sql_op = "ILIKE"
            self.params.append(f"%{value}%")
        elif op == "~":
            sql_op = "~*"  # Use ~* for case-insensitive regex match
            self.params.append(value)
        elif op == "!~":
            sql_op = "!~*"  # Use !~* for case-insensitive regex match
            self.params.append(value)
        else:
            sql_op = op
            self.params.append(value)

        return f"{sql_field} {sql_op} {placeholder}"

    def _translate_global_search(self, node: GlobalSearch) -> str:
        if not self.global_search_fields:
            raise ValueError("Global search used, but no fields configured for it.")

        clauses = []
        for field_name in self.global_search_fields:
            sql_field = self.schema_mapping.get(field_name)
            if sql_field:
                self.param_index += 1
                placeholder = f"${self.param_index}"
                clauses.append(f"{sql_field} ILIKE {placeholder}")
                self.params.append(f"%{node.value}%")

        return "(" + " OR ".join(clauses) + ")"


class SchemaMapperFactory:
    """Factory for creating and caching database schema mappings."""

    def __init__(self) -> None:
        # Initial empty mapping, will be replaced when refresh_from_database is called
        self._mapping: dict[str, str] = {}
        self._global_search_fields: list[str] = list(self._mapping.keys())

    @property
    def mapping(self) -> dict[str, str]:
        """Get the current schema mapping."""
        return self._mapping

    @property
    def global_search_fields(self) -> list[str]:
        """Get the current global search fields."""
        return self._global_search_fields

    async def refresh_from_database(self, database: Database) -> None:
        """Updates the mapping by introspecting the database schema."""
        self._mapping = await database.generate_schema_mapping()
        # Update global search fields to match keys in mapping
        self._global_search_fields = list(self._mapping.keys())


class QueryParser:
    """
    A comprehensive query parser that handles GCP Logging query language and
    translates it to PostgreSQL queries based on database schema.
    """

    def __init__(self, database: Database) -> None:
        """
        Initialize the QueryParser with a database instance.

        Args:
            database: A database connection manager that provides a session method
        """
        self.database: Database = database
        self.schema_mapper: SchemaMapperFactory = SchemaMapperFactory()
        self.parser: Lark | None = None
        self.transformer: AstTransformer | None = None
        self.translator: SqlTranslator | None = None

        self.table_aliases = {
            "samples": "s",
            "detectors": "d",
            "campaigns": "c",
            "frameworks": "f",
            "accelerator_types": "at",
        }

        self.base_sql = f"""
            SELECT s.*, d.name as detector_name, c.name as campaign_name, f.name as framework_name, at.name as accelerator_name
            FROM samples s
            LEFT JOIN detectors {self.table_aliases["detectors"]} ON s.detector_id = d.detector_id
            LEFT JOIN campaigns {self.table_aliases["campaigns"]} ON s.campaign_id = c.campaign_id
            LEFT JOIN frameworks {self.table_aliases["frameworks"]} ON s.framework_id = f.framework_id
            LEFT JOIN accelerator_types {self.table_aliases["accelerator_types"]} ON s.accelerator_type_id = at.accelerator_type_id
            WHERE
        """
        # Table aliases mapping

    async def setup(self, database: Database) -> None:
        """
        Initialize the parser, transformer, translator and database schema mapping.
        This must be called before any query parsing operations.
        """
        # Initialize components
        self.parser = Lark(gcp_logging_grammar, start="start", parser="lalr")
        self.transformer = AstTransformer()
        self.translator = SqlTranslator()

        # Fetch schema mapping from database
        await self.schema_mapper.refresh_from_database(database)

        # Convert table names to aliases in the schema mapping
        self._convert_schema_mapping_to_aliases()

    def _convert_schema_mapping_to_aliases(self) -> None:
        """
        Convert full table names in schema mapping to the corresponding table aliases
        used in the SQL query.
        """
        updated_mapping = {}
        for key, value in self.schema_mapper.mapping.items():
            for table_name, alias in self.table_aliases.items():
                if value.startswith(f"{table_name}."):
                    # Replace "table_name." with "alias."
                    updated_mapping[key] = value.replace(f"{table_name}.", f"{alias}.")
                    break
            else:
                # Keep the original if no replacement was made
                updated_mapping[key] = value

        # Update the schema mapper with the modified mapping
        self.schema_mapper._mapping = updated_mapping

    def parse_query(self, query_string: str) -> tuple[str, list[Any]]:
        """
        Parse a GCP logging query and translate it to a PostgreSQL query.

        Args:
            query_string: The GCP logging query string to parse.

        Returns:
            A tuple containing (SQL query string, parameter list).

        Raises:
            RuntimeError: If setup() hasn't been called
            ValueError: If the query string is empty or has invalid syntax.
        """
        if not self.parser or not self.transformer or not self.translator:
            raise RuntimeError("QueryParser not set up. Call setup() first.")

        if not query_string.strip():
            raise ValueError("Query string cannot be empty.")

        try:
            parse_tree = self.parser.parse(query_string)
            ast = cast(AstNode, self.transformer.transform(parse_tree))
        except exceptions.LarkError as e:
            print(f"Error parsing query: {e}")
            raise ValueError(f"Invalid query syntax. {e}") from e

        # Reset the translator and set the appropriate mappings
        self.translator.reset(
            self.schema_mapper.mapping, self.schema_mapper.global_search_fields
        )
        where_clause = self.translator.translate(ast)

        full_sql_query = self.base_sql + where_clause

        return full_sql_query, self.translator.params
