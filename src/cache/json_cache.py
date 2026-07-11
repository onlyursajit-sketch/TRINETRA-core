from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class JSONCacheError(Exception):
    """Raised when JSON cache operations fail."""


class JSONCache:
    """
    TRINETRA unified JSON cache.

    Features:
    - Atomic JSON writes
    - TTL-based freshness
    - LIVE / STALE status handling
    - Corrupt-cache protection
    - Module-wise cache namespaces
    """

    def __init__(
        self,
        base_dir: str | Path = "cache",
    ) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _parse_datetime(
        value: Any,
    ) -> datetime | None:
        if not isinstance(value, str):
            return None

        try:
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

            if parsed.tzinfo is None:
                parsed = parsed.replace(
                    tzinfo=timezone.utc
                )

            return parsed.astimezone(
                timezone.utc
            )

        except ValueError:
            return None

    @staticmethod
    def _validate_name(value: str) -> str:
        cleaned = value.strip().lower()

        if not cleaned:
            raise JSONCacheError(
                "Cache name cannot be empty."
            )

        allowed = set(
            "abcdefghijklmnopqrstuvwxyz"
            "0123456789_-"
        )

        if any(
            character not in allowed
            for character in cleaned
        ):
            raise JSONCacheError(
                "Cache name contains unsupported characters."
            )

        return cleaned

    def _cache_path(
        self,
        namespace: str,
        key: str,
    ) -> Path:
        clean_namespace = self._validate_name(
            namespace
        )
        clean_key = self._validate_name(key)

        directory = (
            self.base_dir
            / clean_namespace
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory / f"{clean_key}.json"

    def write(
        self,
        namespace: str,
        key: str,
        payload: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> Path:
        if not isinstance(payload, dict):
            raise JSONCacheError(
                "Cache payload must be a dictionary."
            )

        if (
            ttl_seconds is not None
            and ttl_seconds < 0
        ):
            raise JSONCacheError(
                "TTL cannot be negative."
            )

        path = self._cache_path(
            namespace,
            key,
        )

        now = self._utc_now()

        cache_document = {
            "cache_metadata": {
                "namespace": namespace,
                "key": key,
                "written_at": now.isoformat(),
                "ttl_seconds": ttl_seconds,
                "schema_version": 1,
            },
            "payload": payload,
        }

        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                prefix=f".{path.stem}_",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                json.dump(
                    cache_document,
                    temporary_file,
                    indent=2,
                    ensure_ascii=False,
                    allow_nan=False,
                )

                temporary_file.flush()
                os.fsync(
                    temporary_file.fileno()
                )

                temporary_path = Path(
                    temporary_file.name
                )

            os.replace(
                temporary_path,
                path,
            )

            return path

        except (
            OSError,
            TypeError,
            ValueError,
        ) as exc:
            if (
                temporary_path is not None
                and temporary_path.exists()
            ):
                temporary_path.unlink(
                    missing_ok=True
                )

            raise JSONCacheError(
                f"Failed to write cache: {exc}"
            ) from exc

    def read(
        self,
        namespace: str,
        key: str,
        allow_stale: bool = True,
    ) -> dict[str, Any] | None:
        path = self._cache_path(
            namespace,
            key,
        )

        if not path.exists():
            return None

        try:
            with path.open(
                "r",
                encoding="utf-8",
            ) as file:
                cache_document = json.load(file)

        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:
            raise JSONCacheError(
                f"Failed to read cache: {exc}"
            ) from exc

        if not isinstance(
            cache_document,
            dict,
        ):
            raise JSONCacheError(
                "Cache document is invalid."
            )

        metadata = cache_document.get(
            "cache_metadata"
        )
        payload = cache_document.get(
            "payload"
        )

        if not isinstance(metadata, dict):
            raise JSONCacheError(
                "Cache metadata is missing."
            )

        if not isinstance(payload, dict):
            raise JSONCacheError(
                "Cached payload is invalid."
            )

        written_at = self._parse_datetime(
            metadata.get("written_at")
        )

        ttl_seconds = metadata.get(
            "ttl_seconds"
        )

        if written_at is None:
            raise JSONCacheError(
                "Cache written_at timestamp is invalid."
            )

        age_seconds = max(
            0.0,
            (
                self._utc_now()
                - written_at
            ).total_seconds(),
        )

        is_stale = (
            isinstance(ttl_seconds, int)
            and age_seconds > ttl_seconds
        )

        if is_stale and not allow_stale:
            return None

        result = dict(payload)

        result["cache_info"] = {
            "path": str(path),
            "written_at": written_at.isoformat(),
            "ttl_seconds": ttl_seconds,
            "age_seconds": round(
                age_seconds,
                3,
            ),
            "is_stale": is_stale,
        }

        if is_stale:
            result["data_status"] = "STALE"
        else:
            result.setdefault(
                "data_status",
                "LIVE",
            )

        return result

    def exists(
        self,
        namespace: str,
        key: str,
    ) -> bool:
        return self._cache_path(
            namespace,
            key,
        ).exists()

    def delete(
        self,
        namespace: str,
        key: str,
    ) -> bool:
        path = self._cache_path(
            namespace,
            key,
        )

        if not path.exists():
            return False

        try:
            path.unlink()
            return True

        except OSError as exc:
            raise JSONCacheError(
                f"Failed to delete cache: {exc}"
            ) from exc

    def clear_namespace(
        self,
        namespace: str,
    ) -> int:
        clean_namespace = self._validate_name(
            namespace
        )

        directory = (
            self.base_dir
            / clean_namespace
        )

        if not directory.exists():
            return 0

        deleted = 0

        for path in directory.glob("*.json"):
            try:
                path.unlink()
                deleted += 1

            except OSError as exc:
                raise JSONCacheError(
                    f"Failed to clear namespace: {exc}"
                ) from exc

        return deleted
