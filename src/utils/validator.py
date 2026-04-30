from __future__ import annotations

from dataclasses import MISSING
from typing import Any, Dict, List, Type, TypeVar, Union, get_args, get_origin, get_type_hints

from src.schemas import (
    ArchitectNote,
    Assessment,
    AssessmentQuestion,
    ConceptNote,
    EvaluationResult,
    RunState,
    Scores,
    SelectedTopic,
    Topic,
    UseCaseMapping,
    UserAnswer,
)


T = TypeVar("T")


class ValidationError(Exception):
    """Raised when payload validation fails."""


def _is_optional(annotation: Any) -> bool:
    origin = get_origin(annotation)
    if origin is Union:
        return type(None) in get_args(annotation)
    return False


def _strip_optional(annotation: Any) -> Any:
    if not _is_optional(annotation):
        return annotation
    args = [arg for arg in get_args(annotation) if arg is not type(None)]
    return args[0] if len(args) == 1 else annotation


def _validate_primitive(value: Any, expected_type: Any, field_name: str) -> None:
    if expected_type is Any:
        return

    if expected_type is str and not isinstance(value, str):
        raise ValidationError(f"Field '{field_name}' must be a string.")
    if expected_type is int and not isinstance(value, int):
        raise ValidationError(f"Field '{field_name}' must be an integer.")
    if expected_type is bool and not isinstance(value, bool):
        raise ValidationError(f"Field '{field_name}' must be a boolean.")
    if expected_type is float and not isinstance(value, (int, float)):
        raise ValidationError(f"Field '{field_name}' must be a float.")
    if expected_type is dict and not isinstance(value, dict):
        raise ValidationError(f"Field '{field_name}' must be a dictionary.")
    if expected_type is list and not isinstance(value, list):
        raise ValidationError(f"Field '{field_name}' must be a list.")


def _validate_list(value: Any, expected_type: Any, field_name: str) -> None:
    if not isinstance(value, list):
        raise ValidationError(f"Field '{field_name}' must be a list.")

    item_type = get_args(expected_type)[0] if get_args(expected_type) else Any
    for idx, item in enumerate(value):
        _validate_value(item, item_type, f"{field_name}[{idx}]")


def _validate_dict(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise ValidationError(f"Field '{field_name}' must be a dictionary.")


def _validate_value(value: Any, expected_type: Any, field_name: str) -> None:
    expected_type = _strip_optional(expected_type)
    origin = get_origin(expected_type)

    if origin in (list, List):
        _validate_list(value, expected_type, field_name)
        return

    if origin in (dict, Dict):
        _validate_dict(value, field_name)
        return

    if hasattr(expected_type, "__dataclass_fields__"):
        if not isinstance(value, dict):
            raise ValidationError(f"Field '{field_name}' must be an object/dict.")
        validate_payload(value, expected_type)
        return

    _validate_primitive(value, expected_type, field_name)


def validate_payload(payload: Dict[str, Any], schema_cls: Type[T]) -> None:
    if not isinstance(payload, dict):
        raise ValidationError("Payload must be a dictionary.")

    schema_fields = schema_cls.__dataclass_fields__
    type_hints = get_type_hints(schema_cls)

    for field_name, field_def in schema_fields.items():
        expected_type = type_hints.get(field_name, field_def.type)

        has_default = not (
            field_def.default is MISSING and field_def.default_factory is MISSING
        )
        is_required = not _is_optional(expected_type) and not has_default

        if field_name not in payload:
            if is_required:
                raise ValidationError(f"Missing required field: '{field_name}'")
            continue

        _validate_value(payload[field_name], expected_type, field_name)


def build_dataclass(payload: Dict[str, Any], schema_cls: Type[T]) -> T:
    validate_payload(payload, schema_cls)

    converted_payload = {}
    schema_fields = schema_cls.__dataclass_fields__
    type_hints = get_type_hints(schema_cls)

    for field_name, field_def in schema_fields.items():
        if field_name not in payload:
            continue

        value = payload[field_name]
        expected_type = _strip_optional(type_hints.get(field_name, field_def.type))
        origin = get_origin(expected_type)

        if hasattr(expected_type, "__dataclass_fields__") and isinstance(value, dict):
            converted_payload[field_name] = build_dataclass(value, expected_type)

        elif origin in (list, List) and isinstance(value, list):
            item_type = get_args(expected_type)[0] if get_args(expected_type) else Any

            if hasattr(item_type, "__dataclass_fields__"):
                converted_payload[field_name] = [
                    build_dataclass(item, item_type) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                converted_payload[field_name] = value

        else:
            converted_payload[field_name] = value

    return schema_cls(**converted_payload)


SCHEMA_REGISTRY = {
    "Topic": Topic,
    "SelectedTopic": SelectedTopic,
    "ConceptNote": ConceptNote,
    "UseCaseMapping": UseCaseMapping,
    "ArchitectNote": ArchitectNote,
    "AssessmentQuestion": AssessmentQuestion,
    "Assessment": Assessment,
    "UserAnswer": UserAnswer,
    "Scores": Scores,
    "EvaluationResult": EvaluationResult,
    "RunState": RunState,
}