from pydantic import ValidationError


def validate_request(dto_class, data: dict) -> tuple:
    try:
        validated = dto_class(**data)
        return validated, None
    except ValidationError as e:
        return None, {"error": "VALIDATION_001", "details": e.errors()}
