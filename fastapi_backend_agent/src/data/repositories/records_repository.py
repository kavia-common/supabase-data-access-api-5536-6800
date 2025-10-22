from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ...core.errors import AppError, NotFoundError
from ...core.logging import get_logger
from ..supabase_client import get_client, get_schema

logger = get_logger(__name__)


class RecordsRepository:
    """
    Repository for interacting with the 'records' table via Supabase.

    Supports:
    - Pagination with total count
    - Safe sorting on allowed columns
    - Basic text search across 'title' and 'description'
    - CRUD operations with error handling
    """

    def __init__(self, table_name: Optional[str] = None, schema: Optional[str] = None) -> None:
        self._client = get_client()
        self._schema = schema or get_schema()
        self._table = table_name or "records"

        # Allowed columns for sorting and filtering
        self._allowed_cols = {"id", "title", "description", "created_at"}

    def _table_query(self):
        """
        Helper to get a table query object with schema applied if supported.

        supabase-py v2: client.table("name") with .schema("schema") to select schema.
        """
        try:
            qb = self._client.table(self._table)
            # Apply schema if SDK supports schema() on query builder
            try:
                # Some versions allow schema() chaining; if not, this is a no-op via except
                qb = qb.schema(self._schema)
            except Exception:
                # ignore schema application if not supported
                pass
            return qb
        except Exception as exc:
            logger.error("Failed to build table query", exc_info=exc)
            raise AppError("Failed to build table query", code="supabase_query_error") from exc

    def _apply_filters(self, query, filters: Optional[Dict[str, Any]] = None, q: Optional[str] = None):
        """
        Apply column filters and a case-insensitive search query across title/description.
        """
        qb = query
        # Structured filters
        if filters:
            for key, value in filters.items():
                if key not in self._allowed_cols:
                    # ignore disallowed filters to avoid injection; callers can see no effect
                    continue
                # For None we can filter is null
                if value is None:
                    qb = qb.is_(key, "null")
                else:
                    qb = qb.eq(key, value)

        # Free-text search 'q': try ilike on title OR description
        if q:
            like = f"%{q}%"
            # Build two separate filters and combine with or_
            try:
                qb = qb.or_(f"title.ilike.{like},description.ilike.{like}")
            except Exception:
                # Fallback: attempt to chain filters; some SDKs require explicit or_ string
                # If or_ not available, we filter title ilike; description filter can be added by caller if needed
                try:
                    qb = qb.ilike("title", like)
                except Exception:
                    # As a last resort do nothing; the API layer may handle additional filtering
                    pass
        return qb

    def _safe_sort(self, sort_by: str, sort_dir: str) -> Tuple[str, bool]:
        """
        Validate sort column and direction, returning column and ascending flag.
        """
        col = sort_by if sort_by in self._allowed_cols else "created_at"
        direction = sort_dir.lower()
        ascending = direction in ("asc", "ascending", "1", "true")
        return col, ascending

    # PUBLIC_INTERFACE
    def list_records(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        q: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List records with pagination, sorting, and optional filtering/search.

        Returns a tuple: (items, total_count)
        """
        if page < 1 or page_size < 1:
            raise AppError("page and page_size must be positive integers", code="validation_error")

        from_idx = (page - 1) * page_size
        to_idx = from_idx + page_size - 1

        qb = self._table_query().select("*")
        qb = self._apply_filters(qb, filters=filters, q=q)

        sort_col, ascending = self._safe_sort(sort_by, sort_dir)
        try:
            qb = qb.order(sort_col, desc=not ascending)
        except Exception:
            # If order signature differs, attempt alternative parameter name
            try:
                qb = qb.order(sort_col, ascending=ascending)
            except Exception:
                # Ignore sort if not supported
                pass

        # Range for pagination
        try:
            qb_paged = qb.range(from_idx, to_idx)
        except Exception:
            qb_paged = qb  # fallback if range unsupported

        try:
            data_resp = qb_paged.execute()
            items = getattr(data_resp, "data", None) or getattr(data_resp, "json", {}).get("data") or []
        except Exception as exc:
            logger.error("Failed to list records", exc_info=exc)
            raise AppError("Failed to fetch records", code="supabase_query_error") from exc

        # Total count via a separate count query
        total = 0
        try:
            count_qb = self._table_query().select("id", count="exact")
            count_qb = self._apply_filters(count_qb, filters=filters, q=q)
            count_resp = count_qb.execute()
            # supabase-py v2 returns "count" attribute or within response dict
            total = getattr(count_resp, "count", None) or getattr(count_resp, "data", None)
            if isinstance(total, list):
                # Some responses might return data rows; fallback to len
                total = len(total)
            if total is None:
                # final fallback: use length from items if unknown
                total = len(items)
        except Exception:
            # If count fails, fallback to page sized estimation (not ideal but resilient)
            total = len(items) if page == 1 else (page * page_size + (len(items) > 0))

        return items, int(total)

    # PUBLIC_INTERFACE
    def get_record_by_id(self, id: str) -> Dict[str, Any]:
        """
        Retrieve a single record by ID or raise NotFoundError if missing.
        """
        try:
            qb = self._table_query().select("*").eq("id", id).limit(1)
            resp = qb.execute()
            data = getattr(resp, "data", None) or []
            if not data:
                raise NotFoundError(f"Record with id '{id}' not found")
            return data[0]
        except NotFoundError:
            raise
        except Exception as exc:
            logger.error("Failed to fetch record by id", exc_info=exc)
            raise AppError("Failed to fetch record", code="supabase_query_error") from exc

    # PUBLIC_INTERFACE
    def create_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new record and return the created row.
        """
        try:
            resp = self._table_query().insert(data).select("*").single().execute()
            created = getattr(resp, "data", None)
            if not created:
                # When single() not supported, try to fetch first row
                data_list = getattr(resp, "data", None) or []
                if isinstance(data_list, list) and data_list:
                    created = data_list[0]
            if not created:
                raise AppError("Failed to create record", code="record_create_failed")
            return created
        except AppError:
            raise
        except Exception as exc:
            logger.error("Failed to create record", exc_info=exc)
            raise AppError("Failed to create record", code="supabase_mutation_error") from exc

    # PUBLIC_INTERFACE
    def update_record(self, id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a record by ID and return the updated row.
        """
        try:
            resp = self._table_query().update(data).eq("id", id).select("*").single().execute()
            updated = getattr(resp, "data", None)
            if not updated:
                # Try alternative: data list
                data_list = getattr(resp, "data", None) or []
                if isinstance(data_list, list) and data_list:
                    updated = data_list[0]
            if not updated:
                # Check existence
                raise NotFoundError(f"Record with id '{id}' not found")
            return updated
        except NotFoundError:
            raise
        except Exception as exc:
            logger.error("Failed to update record", exc_info=exc)
            raise AppError("Failed to update record", code="supabase_mutation_error") from exc

    # PUBLIC_INTERFACE
    def delete_record(self, id: str) -> bool:
        """
        Delete a record by ID. Returns True if a row was deleted.
        """
        try:
            resp = self._table_query().delete().eq("id", id).execute()
            data = getattr(resp, "data", None)
            # If data is list with deleted rows, success if non-empty
            if isinstance(data, list):
                if len(data) == 0:
                    raise NotFoundError(f"Record with id '{id}' not found")
                return True
            # Some SDK versions may not return rows; do a follow-up existence check
            try:
                self.get_record_by_id(id)
                # If no NotFoundError raised, then deletion didn't occur
                return False
            except NotFoundError:
                return True
        except NotFoundError:
            raise
        except Exception as exc:
            logger.error("Failed to delete record", exc_info=exc)
            raise AppError("Failed to delete record", code="supabase_mutation_error") from exc
