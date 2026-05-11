"""Validation for the canonical matrix document — heatgraph's only input shape.

See docs/SCHEMA.md for the authoritative field-by-field reference.
"""

from __future__ import annotations

from typing import Any

SCHEMA_HINT = "See docs/SCHEMA.md for the matrix doc format."


class SchemaError(ValueError):
    """Raised when stdin input does not conform to the matrix doc schema."""


def validate_matrix_doc(doc: Any) -> None:
    if not isinstance(doc, dict):
        raise SchemaError(
            f"Expected a JSON object, got {type(doc).__name__}. {SCHEMA_HINT}"
        )

    if "values" not in doc:
        raise SchemaError(f"Missing required field 'values'. {SCHEMA_HINT}")

    values = doc["values"]
    if not isinstance(values, list):
        raise SchemaError(
            f"'values' must be a list of rows, got {type(values).__name__}. {SCHEMA_HINT}"
        )

    for i, row in enumerate(values):
        if not isinstance(row, list):
            raise SchemaError(
                f"'values[{i}]' must be a list, got {type(row).__name__}. {SCHEMA_HINT}"
            )
        for j, v in enumerate(row):
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                raise SchemaError(
                    f"'values[{i}][{j}]' must be a number, got {type(v).__name__}. {SCHEMA_HINT}"
                )

    if "cols" in doc and doc["cols"] is not None:
        _validate_label_list(doc["cols"], "cols")

    if "rows" in doc and doc["rows"] is not None:
        _validate_label_list(doc["rows"], "rows")

    if "meta" in doc and doc["meta"] is not None and not isinstance(doc["meta"], dict):
        raise SchemaError(f"'meta' must be an object if present. {SCHEMA_HINT}")


def _validate_label_list(labels: Any, name: str) -> None:
    if not isinstance(labels, list):
        raise SchemaError(f"'{name}' must be a list of strings. {SCHEMA_HINT}")
    for i, label in enumerate(labels):
        if not isinstance(label, str):
            raise SchemaError(
                f"'{name}[{i}]' must be a string, got {type(label).__name__}. {SCHEMA_HINT}"
            )
