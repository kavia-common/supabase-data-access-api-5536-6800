from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class SortDirection(str, Enum):
    """
    Enumeration of supported sort directions.
    """

    asc = "asc"
    desc = "desc"


class RecordBase(BaseModel):
    """
    Base fields for a record entity.

    Contains the common editable fields shared by create and update operations.
    """

    title: str = Field(..., description="Short title of the record")
    description: Optional[str] = Field(None, description="Optional longer description")


class RecordCreate(RecordBase):
    """
    Model used when creating a new record.
    """

    pass


class RecordUpdate(BaseModel):
    """
    Partial update model for records.

    All fields are optional to support PATCH-like behavior.
    """

    title: Optional[str] = Field(None, description="Short title of the record")
    description: Optional[str] = Field(None, description="Optional longer description")


class RecordOut(BaseModel):
    """
    Output representation of a record returned by the API.
    """

    id: str = Field(..., description="Unique identifier of the record")
    title: str = Field(..., description="Short title of the record")
    description: Optional[str] = Field(None, description="Optional longer description")
    created_at: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp when the record was created (as stored by the database)",
    )


class RecordsQueryParams(BaseModel):
    """
    Query parameters for listing records, including pagination, sorting, search, and filters.

    Validation rules:
    - page >= 1
    - 1 <= page_size <= 100
    - sort_by in {id, title, created_at}
    - sort_dir in {asc, desc}
    """

    page: int = Field(1, ge=1, description="Page number starting at 1")
    page_size: int = Field(
        20, ge=1, le=100, description="Number of items per page (1-100)"
    )
    sort_by: str = Field(
        "created_at",
        description="Field to sort by. Allowed values: id, title, created_at",
    )
    sort_dir: SortDirection = Field(
        SortDirection.desc, description="Sort direction: asc or desc"
    )
    q: Optional[str] = Field(
        None, description="Optional free-text search across title and description"
    )
    filters: Optional[List[str]] = Field(
        default=None,
        description=(
            "Optional list of simple filter expressions. "
            "Format: '<field>=<value>'. Allowed fields: id, title, created_at. "
            "Note: Complex filters should be implemented at repository level if needed."
        ),
    )

    # Allowed sort fields for validation
    _allowed_sort_fields = {"id", "title", "created_at"}

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        """
        Ensure sort_by is one of the allowed fields.
        """
        if v not in cls._allowed_sort_fields:
            raise ValueError(
                f"Invalid sort_by '{v}'. Allowed: {', '.join(sorted(cls._allowed_sort_fields))}"
            )
        return v

    @field_validator("filters")
    @classmethod
    def validate_filters(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """
        Validate that each filter string roughly conforms to '<field>=<value>' and uses an allowed field.
        This lightweight validation protects against obvious misuse while keeping flexibility.
        """
        if not v:
            return v
        allowed = cls._allowed_sort_fields  # reuse allowed set (id, title, created_at)
        for item in v:
            if "=" not in item:
                raise ValueError(
                    f"Invalid filter '{item}'. Expected format '<field>=<value>'."
                )
            field, _value = item.split("=", 1)
            field = field.strip()
            if field not in allowed:
                raise ValueError(
                    f"Invalid filter field '{field}'. Allowed: {', '.join(sorted(allowed))}"
                )
        return v


class PageMeta(BaseModel):
    """
    Pagination metadata returned with list endpoints.
    """

    page: int = Field(..., description="Current page number (starting at 1)")
    page_size: int = Field(..., description="Number of items per page")
    total: int = Field(..., description="Total number of available items")
    total_pages: int = Field(..., description="Total number of pages for the query")


class PaginatedRecords(BaseModel):
    """
    Paginated response model for records list endpoints.
    """

    items: List[RecordOut] = Field(..., description="List of records in the page")
    meta: PageMeta = Field(..., description="Pagination metadata")
