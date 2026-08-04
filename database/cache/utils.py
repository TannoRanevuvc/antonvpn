from sqlalchemy import inspect


def model_to_dict(obj) -> dict:
    """Convert a SQLAlchemy model instance to a plain dict (columns only)."""
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}
