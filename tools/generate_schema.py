from __future__ import annotations

import ast
import dataclasses
import inspect
import json
import types

from typing import Any, Literal, Union, cast, get_args, get_origin, get_type_hints

import docstring_parser

from docstring_parser import DocstringStyle
from jsonargparse.typing import SecretStr

JSON_SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"


def is_union(tp: Any) -> bool:
    origin = get_origin(tp)
    return origin is Union or origin is types.UnionType


def is_optional(tp: Any) -> bool:
    return is_union(tp) and type(None) in get_args(tp)


def unwrap_optional(tp: Any) -> Any:
    return next(t for t in get_args(tp) if t is not type(None))


def literal_values(tp: Any) -> list[Any]:
    if get_origin(tp) is Literal:
        return list(get_args(tp))
    return []


def parse_docstring(obj: type) -> str | None:

    src = inspect.getsource(obj)
    node = ast.parse(src)
    doc = ast.get_docstring(cast(ast.ClassDef, node.body[0]))
    if not doc:
        return None
    parsed = docstring_parser.parse(doc, style=DocstringStyle.GOOGLE)
    return parsed.short_description


def parse_field_docstring(cls: type, field_name: str) -> str | None:
    doc = inspect.getdoc(cls)
    if not doc:
        return None
    parsed = docstring_parser.parse(doc)
    for param in parsed.params:
        if param.arg_name == field_name:
            return param.description
    return None


class SchemaGenerator:
    def __init__(self, module):
        self.module = module
        self.globals = module.__dict__
        self.defs: dict[str, dict[str, Any]] = {}
        self.visited: set[type] = set()

        # Detect union aliases like FlowTriggerConfig = A | B | C
        self.alias_unions: dict[str, tuple[type, ...]] = {}
        self._discover_alias_unions()

    def _discover_alias_unions(self):
        for name, value in self.globals.items():
            origin = get_origin(value)
            if origin is Union or origin is types.UnionType:
                variants = tuple(v for v in get_args(value) if isinstance(v, type))
                if variants:
                    self.alias_unions[name] = variants

    def resolve_type(self, tp: Any) -> Any:
        if isinstance(tp, str):
            return eval(tp, self.globals)
        if getattr(tp, "__forward_arg__", None):
            return eval(tp.__forward_arg__, self.globals)
        return tp

    def python_type_to_schema(self, tp: Any) -> dict[str, Any]:
        type_schema = self.python_type_to_schema_optional(tp)
        assert type_schema is not None
        return type_schema

    def python_type_to_schema_optional(self, tp: Any) -> dict[str, Any] | None:
        tp = self.resolve_type(tp)

        # If it's a known alias union (FlowTriggerConfig)
        if isinstance(tp, str) and tp in self.alias_unions:
            variants = self.alias_unions[tp]
            return {"oneOf": [{"$ref": f"#/$defs/{v.__name__}"} for v in variants]}

        origin = get_origin(tp)

        if origin is list:
            (item_type,) = get_args(tp)
            return {
                "type": "array",
                "items": self.python_type_to_schema(item_type),
            }

        if origin is Literal:
            vals = literal_values(tp)
            if len(vals) == 1:
                return {"const": vals[0]}
            return {"enum": vals}

        if is_union(tp):
            union_types = [a for a in get_args(tp) if a is not types.NoneType]
            union_schema_types = [self.python_type_to_schema_optional(a) for a in union_types]
            if None in union_schema_types:
                union_schema_types.remove(None)

            if len(union_schema_types) == 1:
                return union_schema_types[0]
            elif len(union_schema_types) > 1:
                return {"anyOf": union_schema_types}
            else:
                return {}

        if isinstance(tp, type) and dataclasses.is_dataclass(tp):
            ref_name = tp.__name__
            if tp not in self.visited:
                self.visited.add(tp)
                self.defs[ref_name] = self.dataclass_schema(tp)
            return {"$ref": f"#/$defs/{ref_name}"}

        if tp is str:
            return {"type": "string"}
        if tp is int:
            return {"type": "integer"}
        if tp is bool:
            return {"type": "boolean"}
        if tp is float:
            return {"type": "number"}
        if tp is dict or origin is dict:
            return {"type": "object"}
        if tp is SecretStr:
            return {"type": "string"}

        return None

    def dataclass_schema(self, cls: type) -> dict[str, Any]:
        schema = {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }

        class_doc = parse_docstring(cls)
        if class_doc:
            schema["description"] = class_doc

        required = []
        hints = get_type_hints(cls, globalns=self.globals)

        for field in dataclasses.fields(cls):
            field_type = hints[field.name]
            f_schema = self.python_type_to_schema(field_type)

            field_doc = parse_field_docstring(cls, field.name)
            if field_doc:
                f_schema["description"] = field_doc

            if (
                field.default is dataclasses.MISSING
                and field.default_factory is dataclasses.MISSING
            ):
                if not is_optional(field_type):
                    required.append(field.name)
            else:
                if field.default and field.default is not dataclasses.MISSING:
                    f_schema["default"] = field.default

            schema["properties"][field.name] = f_schema

        if required:
            schema["required"] = required

        return schema

    def build(self, root_cls: type) -> dict[str, Any]:

        schema: dict[str, Any] = {}
        schema["$schema"] = JSON_SCHEMA_DRAFT
        schema["title"] = root_cls.__name__

        root_schema = self.dataclass_schema(root_cls)
        schema.update(root_schema)

        # Ensure union variants are defined
        for variants in self.alias_unions.values():
            for v in variants:
                if v not in self.visited:
                    self.visited.add(v)
                    self.defs[v.__name__] = self.dataclass_schema(v)

        schema["$defs"] = self.defs
        return schema


if __name__ == "__main__":
    import dbus2mqtt.config as cfg

    generator = SchemaGenerator(cfg)
    schema = generator.build(cfg.Config)

    # patch the generated schema
    required_properties: list[str] = schema["required"]
    required_properties.remove("mqtt")

    print(json.dumps(schema, indent=2))
