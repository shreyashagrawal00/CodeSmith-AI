from pydantic import ValidationError
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def validate_output(data: dict, schema: Type[T]) -> T:
    """Validate agent output against a Pydantic schema. Raises on failure."""
    try:
        return schema(**data)
    except ValidationError as e:
        raise ValueError(f"Agent output validation failed: {e}")
