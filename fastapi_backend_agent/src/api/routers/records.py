from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Path, Query, status
from pydantic import BaseModel, Field

from ...core.dependencies import get_logger
from ...core.errors import AppError, NotFoundError
from ...data.repositories.records_repository import RecordsRepository
from ...models import (
    PageMeta,
    PaginatedRecords,
    RecordCreate,
    RecordOut,
    RecordUpdate,
    RecordsQueryParams,
    SortDirection,
)

router = APIRouter(
    prefix="/records",
    tags=["Records"],
)


def _parse_filters(filters: Optional[list[str]]) -> Optional[Dict[str, Any]]:
    """
    Parse a list of 'key=value' filters into a dict. Non-conforming entries are ignored.
    """
    if not filters:
        return None
    out: Dict[str, Any] = {}
    for item in filters:
        if "=" not in item:
            continue
        k, v = item.split("=", 1)
        k = k.strip()
        v = v.strip()
        if k and v != "":
            out[k] = v
    return out or None


class DeleteResponse(BaseModel):
    """Response model for deletion acknowledgment."""

    success: bool = Field(..., description="True if the record was deleted")
    id: str = Field(..., description="Identifier of the attempted deletion target")


# PUBLIC_INTERFACE
@router.get(
    "",
    response_model=PaginatedRecords,
    summary="List records",
    description="List records with pagination, optional search, filtering, and sorting.",
)
def list_records(
    page: int = Query(1, ge=1, description="Page number starting at 1"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_dir: SortDirection = Query(SortDirection.desc, description="Sort direction"),
    q: Optional[str] = Query(None, description="Free-text search across title and description"),
    filters: Optional[list[str]] = Query(
        default=None,
        description="Optional list of simple filter expressions in the form field=value. Allowed fields: id, title, created_at.",
    ),
    logger=Depends(get_logger),
) -> PaginatedRecords:
    """
    List records with pagination, filtering, search and sorting.

    Parameters:
    - page: Page number (>=1)
    - page_size: Page size (1-100)
    - sort_by: Sort column
    - sort_dir: Sort direction
    - q: Free-text search
    - filters: Simple filters list in key=value format

    Returns:
    - PaginatedRecords: Items and pagination metadata
    """
    log = logger
    repo = RecordsRepository()
    # Validate query params via model (for consistent 422 formatting through our handler)
    qp = RecordsQueryParams(
        page=page, page_size=page_size, sort_by=sort_by, sort_dir=sort_dir, q=q, filters=filters
    )
    parsed_filters = _parse_filters(qp.filters)

    items, total = repo.list_records(
        page=qp.page,
        page_size=qp.page_size,
        sort_by=qp.sort_by,
        sort_dir=qp.sort_dir.value if isinstance(qp.sort_dir, SortDirection) else str(qp.sort_dir),
        q=qp.q,
        filters=parsed_filters,
    )
    total_pages = max(1, (total + qp.page_size - 1) // qp.page_size)
    log.info("Listed records", extra={"page": qp.page, "page_size": qp.page_size, "total": total})
    return PaginatedRecords(
        items=[RecordOut(**it) for it in items],
        meta=PageMeta(page=qp.page, page_size=qp.page_size, total=total, total_pages=total_pages),
    )


# PUBLIC_INTERFACE
@router.get(
    "/{id}",
    response_model=RecordOut,
    summary="Get record by ID",
    description="Retrieve a single record by its unique identifier.",
    responses={
        404: {"description": "Record not found"},
    },
)
def get_record(
    id: str = Path(..., description="Record ID"),
    logger=Depends(get_logger),
) -> RecordOut:
    """
    Fetch a record by ID.

    Parameters:
    - id: Record identifier

    Returns:
    - RecordOut: The requested record or 404 if not found.
    """
    log = logger
    repo = RecordsRepository()
    try:
        rec = repo.get_record_by_id(id)
        log.info("Fetched record", extra={"id": id})
        return RecordOut(**rec)
    except NotFoundError as e:
        log.info("Record not found", extra={"id": id})
        raise e


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=RecordOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create record",
    description="Create a new record.",
)
def create_record(
    payload: RecordCreate,
    logger=Depends(get_logger),
) -> RecordOut:
    """
    Create a new record.

    Parameters:
    - payload: RecordCreate model

    Returns:
    - RecordOut: The created record
    """
    log = logger
    repo = RecordsRepository()
    created = repo.create_record(payload.model_dump(exclude_none=True))
    log.info("Created record", extra={"id": created.get("id")})
    return RecordOut(**created)


# PUBLIC_INTERFACE
@router.patch(
    "/{id}",
    response_model=RecordOut,
    summary="Update record",
    description="Update a record by ID with partial fields.",
)
def update_record(
    id: str = Path(..., description="Record ID"),
    payload: RecordUpdate = ...,
    logger=Depends(get_logger),
) -> RecordOut:
    """
    Update a record.

    Parameters:
    - id: Record identifier
    - payload: RecordUpdate model with partial fields

    Returns:
    - RecordOut: The updated record
    """
    log = logger
    repo = RecordsRepository()
    data = payload.model_dump(exclude_none=True)
    if not data:
        raise AppError("No fields provided for update", code="validation_error")
    updated = repo.update_record(id, data)
    log.info("Updated record", extra={"id": id})
    return RecordOut(**updated)


# PUBLIC_INTERFACE
@router.delete(
    "/{id}",
    response_model=DeleteResponse,
    summary="Delete record",
    description="Delete a record by ID.",
    responses={404: {"description": "Record not found"}},
)
def delete_record(
    id: str = Path(..., description="Record ID"),
    logger=Depends(get_logger),
) -> DeleteResponse:
    """
    Delete a record by ID.

    Parameters:
    - id: Record identifier

    Returns:
    - DeleteResponse: Deletion acknowledgement
    """
    log = logger
    repo = RecordsRepository()
    try:
        success = repo.delete_record(id)
        log.info("Deleted record", extra={"id": id, "success": success})
        return DeleteResponse(success=success, id=id)
    except NotFoundError as e:
        log.info("Record not found to delete", extra={"id": id})
        raise e
