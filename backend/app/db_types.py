from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

JSON_DICT = JSON().with_variant(JSONB(), "postgresql")
