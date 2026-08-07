"""A dependency-free validator for the JSON Schema subset the specs use.

The repository installs nothing, so `jsonschema` is not available. That
constraint creates a hazard worth naming: the same author writes the schema and
the validator, so a matching pair of mistakes cancels out and every test still
passes. `tests/test_schema.py` breaks that circle by running cases vendored
from the official JSON-Schema-Test-Suite, which neither this file nor the specs
had any hand in writing.

**Unknown keywords are errors, not no-ops.** A validator that silently ignores a
keyword it does not implement will accept instances the published schema
rejects, and a conformance surface that accepts too much is worse than none:
implementers would build against a contract this repository does not actually
enforce. Anything outside `SUPPORTED_KEYWORDS` fails loudly and names itself.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SPEC_DIR = Path(__file__).resolve().parents[1] / "spec"

#: Keywords this validator implements. Extending the list means implementing
#: the keyword and adding official-suite cases for it, in that order.
SUPPORTED_KEYWORDS = frozenset(
    {
        "$defs",
        "$id",
        "$ref",
        "$schema",
        "additionalProperties",
        "allOf",
        "anyOf",
        "const",
        "description",
        "enum",
        "examples",
        "exclusiveMaximum",
        "exclusiveMinimum",
        "items",
        "maxItems",
        "maxLength",
        "maximum",
        "minItems",
        "minLength",
        "minimum",
        "not",
        "oneOf",
        "pattern",
        "patternProperties",
        "properties",
        "propertyNames",
        "required",
        "title",
        "type",
        "uniqueItems",
    }
)

#: Keywords that carry no assertion. Listed separately so the distinction
#: between "implemented" and "annotation only" stays visible.
ANNOTATIONS = frozenset({"$id", "$schema", "description", "examples", "title", "$defs"})

_TYPES: dict[str, Any] = {
    "object": dict,
    "array": list,
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "null": type(None),
}


class SchemaError(Exception):
    """The schema itself is unusable. Distinct from an instance being invalid."""


def load(name: str) -> dict[str, Any]:
    """Load a published schema from `spec/` by bare name, e.g. `"erratum"`."""

    path = SPEC_DIR / f"{name}.schema.json"
    if not path.is_file():
        raise SchemaError(f"no schema named {name!r} in spec/")
    return json.loads(path.read_text(encoding="utf-8"))


def _matches_type(value: Any, expected: str) -> bool:
    if expected not in _TYPES:
        raise SchemaError(f"unknown type {expected!r}")
    # bool is a subclass of int in Python; JSON Schema treats them as distinct.
    if expected in {"number", "integer"} and isinstance(value, bool):
        return False
    if expected == "number" and isinstance(value, int):
        return True
    if expected == "integer" and isinstance(value, float):
        # JSON Schema: 1.0 is an integer. Only the value matters, not how the
        # document happened to spell it.
        return value.is_integer()
    return isinstance(value, _TYPES[expected])


def _resolve(ref: str, root: dict[str, Any]) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise SchemaError(
            f"unsupported $ref {ref!r}: only local #/... pointers are implemented"
        )
    node: Any = root
    for token in ref[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or token not in node:
            raise SchemaError(f"$ref {ref!r} does not resolve")
        node = node[token]
    if not isinstance(node, dict):
        raise SchemaError(f"$ref {ref!r} does not point at a schema")
    return node


def validate(
    instance: Any,
    schema: Any,
    *,
    root: dict[str, Any] | None = None,
    path: str = "$",
) -> list[str]:
    """Return a list of human-readable errors. Empty means valid."""

    if schema is True:
        return []
    if schema is False:
        return [f"{path}: schema is false, nothing is valid here"]
    if not isinstance(schema, dict):
        raise SchemaError(f"{path}: schema must be an object or a boolean")

    if root is None:
        root = schema

    unknown = sorted(set(schema) - SUPPORTED_KEYWORDS)
    if unknown:
        raise SchemaError(
            f"{path}: unsupported keyword(s) {unknown}. This validator refuses "
            "rather than ignoring them: silently skipping a keyword would accept "
            "instances the published schema rejects."
        )

    errors: list[str] = []

    if "$ref" in schema:
        # Draft 2020-12 evaluates $ref *alongside* its siblings. Draft-07
        # ignored them. Returning early here would silently drop every
        # constraint written next to a $ref.
        errors += validate(instance, _resolve(schema["$ref"], root), root=root, path=path)

    if "type" in schema:
        expected = schema["type"]
        options = expected if isinstance(expected, list) else [expected]
        if not any(_matches_type(instance, option) for option in options):
            errors.append(f"{path}: expected type {expected}, got {type(instance).__name__}")
            return errors

    if "enum" in schema and not any(
        _json_equal(instance, option) for option in schema["enum"]
    ):
        errors.append(f"{path}: {instance!r} is not one of {schema['enum']}")
    if "const" in schema and not _json_equal(instance, schema["const"]):
        errors.append(f"{path}: expected const {schema['const']!r}")

    if isinstance(instance, str):
        if "pattern" in schema and _search(schema["pattern"], instance) is None:
            errors.append(f"{path}: {instance!r} does not match /{schema['pattern']}/")
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{path}: longer than maxLength {schema['maxLength']}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: {instance} is below minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: {instance} is above maximum {schema['maximum']}")
        if "exclusiveMinimum" in schema and instance <= schema["exclusiveMinimum"]:
            errors.append(f"{path}: {instance} is not above {schema['exclusiveMinimum']}")
        if "exclusiveMaximum" in schema and instance >= schema["exclusiveMaximum"]:
            errors.append(f"{path}: {instance} is not below {schema['exclusiveMaximum']}")

    if isinstance(instance, list):
        if "items" in schema:
            for index, item in enumerate(instance):
                errors += validate(item, schema["items"], root=root, path=f"{path}[{index}]")
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: fewer than minItems {schema['minItems']}")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: more than maxItems {schema['maxItems']}")
        if schema.get("uniqueItems") and _has_duplicates(instance):
            errors.append(f"{path}: items are not unique")

    if isinstance(instance, dict):
        errors += _validate_object(instance, schema, root, path)

    for keyword in ("allOf", "anyOf", "oneOf"):
        if keyword not in schema:
            continue
        results = [
            validate(instance, sub, root=root, path=path) for sub in schema[keyword]
        ]
        passed = sum(1 for r in results if not r)
        if keyword == "allOf" and passed != len(results):
            for r in results:
                errors += r
        elif keyword == "anyOf" and passed == 0:
            errors.append(f"{path}: matched none of the anyOf branches")
        elif keyword == "oneOf" and passed != 1:
            errors.append(
                f"{path}: matched {passed} of the oneOf branches, expected exactly 1"
            )

    if "not" in schema and not validate(instance, schema["not"], root=root, path=path):
        errors.append(f"{path}: matched a schema it must not match")

    return errors


def _validate_object(
    instance: dict[str, Any], schema: dict[str, Any], root: dict[str, Any], path: str
) -> list[str]:
    errors: list[str] = []
    properties = schema.get("properties", {})

    for name in schema.get("required", []):
        if name not in instance:
            errors.append(f"{path}: missing required property {name!r}")

    for name, value in instance.items():
        where = f"{path}.{name}"
        matched = False
        if name in properties:
            errors += validate(value, properties[name], root=root, path=where)
            matched = True
        for pattern, sub in schema.get("patternProperties", {}).items():
            if _search(pattern, name):
                errors += validate(value, sub, root=root, path=where)
                matched = True
        if not matched and "additionalProperties" in schema:
            allowed = schema["additionalProperties"]
            if allowed is False:
                errors.append(f"{path}: additional property {name!r} is not allowed")
            else:
                errors += validate(value, allowed, root=root, path=where)
        if "propertyNames" in schema:
            errors += validate(name, schema["propertyNames"], root=root, path=where)

    return errors


def _json_equal(left: Any, right: Any) -> bool:
    """JSON equality, which is not Python equality.

    Python considers `False == 0` and `True == 1`. JSON Schema does not: a
    boolean and a number are different types, so `enum: [false]` must reject
    `0`. Getting this wrong makes `enum` and `const` quietly permissive, which
    is the failure mode this validator exists to avoid.
    """

    if isinstance(left, bool) != isinstance(right, bool):
        return False
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(
            _json_equal(left[k], right[k]) for k in left
        )
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _json_equal(a, b) for a, b in zip(left, right)
        )
    if isinstance(left, (list, dict)) != isinstance(right, (list, dict)):
        return False
    return left == right


def _search(pattern: str, value: str) -> Any:
    """Apply a JSON Schema `pattern`, refusing what Python cannot express.

    JSON Schema specifies ECMA-262 regular expressions. Python's `re` is not
    ECMA-262: Unicode property escapes such as \\p{...} do not compile. Rather
    than silently treating an uncompilable pattern as a non-match — which would
    make an instance look valid because the check could not run — this refuses.
    """

    try:
        return re.search(pattern, value)
    except re.error as error:
        raise SchemaError(
            f"pattern /{pattern}/ is not expressible in Python's re ({error}). "
            "JSON Schema specifies ECMA-262; this validator does not implement "
            "the difference, and refuses rather than reporting a false match."
        ) from error


def _has_duplicates(items: list[Any]) -> bool:
    for index, item in enumerate(items):
        if any(_json_equal(item, other) for other in items[:index]):
            return True
    return False
