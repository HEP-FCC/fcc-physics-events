"""
A Python module to parse a query language and translate it into PostgreSQL queries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from lark import Lark, Token, Transformer, exceptions

from app.storage.database import Database

gcp_logging_grammar = r"""
    ?start: expr
    ?expr: expr OR term | term
    ?term: term AND factor | factor
    ?factor: NOT item | item
    ?item: "(" expr ")" | comparison | global_search
    global_search: value
    comparison: field OP value
    field: CNAME ("." CNAME)*
    value: ESCAPED_STRING | SIGNED_NUMBER | UNQUOTED_STRING
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


@dataclass(frozen=True)
class Field:
    parts: tuple[str, ...]

    def to_sql(self, schema_mapping: dict[str, str]) -> str:
        base_field = self.parts[0]
        if base_field not in schema_mapping:
            raise ValueError(f"Field '{base_field}' is not valid.")
        sql_column = schema_mapping[base_field]
        if base_field == "metadata" and len(self.parts) > 1:
            json_path_parts = self.parts[1:]
            path_expression = "->".join([f"'{part}'" for part in json_path_parts[:-1]])
            return (
                f"{sql_column}->{path_expression}->>'{json_path_parts[-1]}'"
                if len(json_path_parts) > 1
                else f"{sql_column}->>'{json_path_parts[0]}'"
            )
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
        v = i[0]
        if hasattr(v, "type"):
            if v.type == "ESCAPED_STRING":
                return v.value[1:-1]
            if v.type == "SIGNED_NUMBER":
                return float(v.value) if "." in v.value else int(v.value)
        return str(v)


class SqlTranslator:
    def __init__(self) -> None:
        self.schema_mapping: dict[str, str] = {}
        self.global_search_fields: list[str] = []
        self.params: list[Any] = []
        self.param_index = 0

    def reset(self, schema_mapping: dict[str, str]) -> None:
        self.schema_mapping = schema_mapping
        self.global_search_fields = [
            "name",
            "detector",
            "campaign",
            "framework",
            "accelerator",
            "metadata_text",
        ]
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
        sql_field, op, value, self.param_index = (
            node.field.to_sql(self.schema_mapping),
            node.op,
            node.value,
            self.param_index + 1,
        )
        placeholder = f"${self.param_index}"
        if op == ":" or op == "=":
            sql_op, param_value = "=", value
        elif op == "~":
            sql_op, param_value = "~*", value
        elif op == "!~":
            sql_op, param_value = "!~*", value
        else:
            sql_op, param_value = op, value
        self.params.append(param_value)
        return f"{sql_field} {sql_op} {placeholder}"

    def _translate_global_search(self, node: GlobalSearch) -> str:
        clauses = []
        for field_name in self.global_search_fields:
            if field_name in self.schema_mapping:
                sql_field, self.param_index = (
                    self.schema_mapping[field_name],
                    self.param_index + 1,
                )
                placeholder = f"${self.param_index}"
                clauses.append(f"{sql_field} ILIKE {placeholder}")
                self.params.append(f"%{node.value}%")
        if not clauses:
            raise ValueError("Global search used, but no fields configured for it.")
        return "(" + " OR ".join(clauses) + ")"


class QueryParser:
    def __init__(self, database: Database):
        self.database = database
        self.schema_mapping: dict[str, str] = {}
        self.parser = Lark(gcp_logging_grammar, start="start", parser="lalr")
        self.transformer = AstTransformer()
        self.translator = SqlTranslator()

    async def setup(self) -> None:
        self.schema_mapping = await self.database.generate_schema_mapping()

    def parse_query(self, query_string: str) -> tuple[str, str, list[Any]]:
        if not self.schema_mapping:
            raise RuntimeError("QueryParser not set up.")
        from_and_joins = "FROM processes p LEFT JOIN detectors d ON p.detector_id = d.detector_id LEFT JOIN campaigns c ON p.campaign_id = c.campaign_id LEFT JOIN frameworks f ON p.framework_id = f.framework_id LEFT JOIN accelerators at ON p.accelerator_id = at.accelerator_id"
        if not query_string.strip():
            base_select = f"SELECT p.*, d.name as detector_name, c.name as campaign_name, f.name as framework_name, at.name as accelerator_name {from_and_joins}"
            count_query = "SELECT COUNT(*) FROM processes"
            return base_select, count_query, []
        try:
            ast = cast(
                AstNode, self.transformer.transform(self.parser.parse(query_string))
            )
        except exceptions.LarkError as e:
            raise ValueError(f"Invalid query syntax: {e}") from e
        self.translator.reset(self.schema_mapping)
        where_clause = self.translator.translate(ast)
        base_select = f"SELECT p.*, d.name as detector_name, c.name as campaign_name, f.name as framework_name, at.name as accelerator_name {from_and_joins} WHERE {where_clause}"
        count_query = f"SELECT COUNT(*) {from_and_joins} WHERE {where_clause}"
        return base_select, count_query, self.translator.params
