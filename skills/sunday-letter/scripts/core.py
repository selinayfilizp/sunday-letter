#!/usr/bin/env python3
"""Shared contracts for the Codex-local Sunday Letter runtime."""

from __future__ import annotations

import html
import json
import os
import tempfile
import time
from contextlib import contextmanager
from copy import deepcopy
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterator

try:
    import fcntl
except ImportError:  # Windows
    fcntl = None  # type: ignore[assignment]
    import msvcrt


HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE.parent / "references" / "signals.schema.json"
ALLOWED_RICH_TEXT_TAGS = frozenset({"strong", "em"})
LEGACY_METRIC_FIELDS = frozenset(
    {
        "calibration_pct",
        "exports",
        "hours_saved",
        "read_time",
        "total_prefs",
        "tracking_conversations",
        "tracking_signals",
    }
)


class ValidationError(ValueError):
    """Signals did not satisfy the canonical schema or editorial contract."""


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text())


def _json_type_matches(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    return True


def _resolve_ref(root: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValidationError(f"unsupported schema reference: {ref}")
    current: Any = root
    for part in ref[2:].split("/"):
        current = current[part.replace("~1", "/").replace("~0", "~")]
    return current


def _validate_node(value: Any, schema: dict[str, Any], root: dict[str, Any], path: str) -> None:
    if "$ref" in schema:
        _validate_node(value, _resolve_ref(root, schema["$ref"]), root, path)
        return

    if "oneOf" in schema:
        errors: list[str] = []
        matches = 0
        for option in schema["oneOf"]:
            try:
                _validate_node(value, option, root, path)
                matches += 1
            except ValidationError as error:
                errors.append(str(error))
        if matches != 1:
            detail = "; ".join(errors[:2])
            raise ValidationError(f"{path}: expected exactly one schema variant ({detail})")
        return

    if "const" in schema and value != schema["const"]:
        raise ValidationError(f"{path}: expected {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValidationError(f"{path}: expected one of {schema['enum']!r}")

    expected = schema.get("type")
    if expected is not None:
        expected_types = [expected] if isinstance(expected, str) else expected
        if not any(_json_type_matches(value, item) for item in expected_types):
            raise ValidationError(f"{path}: expected type {expected_types!r}")
        if value is None:
            return

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        missing = [key for key in schema.get("required", []) if key not in value]
        if missing:
            raise ValidationError(f"{path}: missing required fields {missing!r}")
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                raise ValidationError(f"{path}: unsupported fields {extra!r}")
        for key, child in value.items():
            if key in properties:
                _validate_node(child, properties[key], root, f"{path}.{key}")

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise ValidationError(f"{path}: expected at least {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ValidationError(f"{path}: expected at most {schema['maxItems']} items")
        if "items" in schema:
            for index, child in enumerate(value):
                _validate_node(child, schema["items"], root, f"{path}[{index}]")

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise ValidationError(f"{path}: must not be empty")
        if schema.get("format") == "date-time":
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as error:
                raise ValidationError(f"{path}: expected an ISO 8601 date-time") from error
            if parsed.tzinfo is None:
                raise ValidationError(f"{path}: date-time must include a timezone")
    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValidationError(f"{path}: must be >= {schema['minimum']}")


def has_meaningful_delta(signals: dict[str, Any]) -> bool:
    if signals.get("skip") is True:
        return False
    return any(
        signals.get(field)
        for field in ("consequences", "decisions", "observations", "retired")
    )


def validate_signals(signals: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(signals, dict):
        raise ValidationError("signals: expected a JSON object")
    legacy = sorted(set(signals) & LEGACY_METRIC_FIELDS)
    if legacy:
        raise ValidationError(
            "signals: unmeasured legacy metrics are not allowed: " + ", ".join(legacy)
        )
    schema = load_schema()
    _validate_node(signals, schema, schema, "signals")
    if not signals.get("skip") and not has_meaningful_delta(signals):
        raise ValidationError(
            "signals: no meaningful delta; return the explicit skip payload instead"
        )
    if signals.get("consequences") and len(signals["consequences"]) < 2:
        raise ValidationError("signals.consequences: include 2-4 actions or none")
    if not signals.get("skip"):
        source = signals["source_summary"]
        start = datetime.fromisoformat(source["window_start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(source["window_end"].replace("Z", "+00:00"))
        if start > end:
            raise ValidationError("signals.source_summary: window_start must precede window_end")
    return deepcopy(signals)


class _RichTextSanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ALLOWED_RICH_TEXT_TAGS and not attrs:
            self.parts.append(f"<{tag}>")
        else:
            self.parts.append(html.escape(self.get_starttag_text(), quote=True))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.parts.append(html.escape(self.get_starttag_text(), quote=True))

    def handle_endtag(self, tag: str) -> None:
        if tag in ALLOWED_RICH_TEXT_TAGS:
            self.parts.append(f"</{tag}>")
        else:
            self.parts.append(html.escape(f"</{tag}>", quote=True))

    def handle_data(self, data: str) -> None:
        self.parts.append(html.escape(data, quote=False))

    def handle_entityref(self, name: str) -> None:
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.parts.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        self.parts.append(html.escape(f"<!--{data}-->", quote=False))

    def handle_decl(self, decl: str) -> None:
        self.parts.append(html.escape(f"<!{decl}>", quote=False))


def sanitize_rich_text(value: Any) -> str:
    parser = _RichTextSanitizer()
    parser.feed("" if value is None else str(value))
    parser.close()
    return "".join(parser.parts)


def text(value: Any, default: str = "") -> str:
    if value is None:
        value = default
    return html.escape(str(value), quote=True)


def ensure_private_directory(path: Path) -> Path:
    path = Path(path).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)
    return path


@contextmanager
def ledger_lock(path: Path) -> Iterator[None]:
    """Serialize every read-modify-write transaction for one local ledger."""
    ledger_path = Path(path).expanduser()
    ensure_private_directory(ledger_path.parent)
    lock_path = ledger_path.with_name(f".{ledger_path.name}.lock")
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "a+b") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        else:  # pragma: no cover - exercised by Windows installations
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            while True:
                try:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(0.05)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            else:  # pragma: no cover - exercised by Windows installations
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def atomic_write_text(path: Path, content: str, mode: int = 0o600) -> None:
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, mode)
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        temporary.unlink(missing_ok=True)
        raise


def default_ledger() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "paused": False,
        "letter_number": 0,
        "last_run": None,
        "last_shipped": None,
        "last_status": None,
        "last_skip_reason": None,
        "open_question": None,
        "retired": [],
        "letters": [],
        "events": [],
    }


def _normalize_ledger(loaded: dict[str, Any]) -> dict[str, Any]:
    defaults = default_ledger()
    version = loaded.get("schema_version", defaults["schema_version"])
    if version != defaults["schema_version"]:
        raise ValidationError(f"unsupported ledger schema_version: {version!r}")
    ledger = {
        key: deepcopy(loaded[key]) if key in loaded else deepcopy(value)
        for key, value in defaults.items()
    }
    ledger["schema_version"] = defaults["schema_version"]
    if not isinstance(ledger.get("paused"), bool):
        raise ValidationError("ledger.paused must be a boolean")
    if (
        not isinstance(ledger.get("letter_number"), int)
        or isinstance(ledger["letter_number"], bool)
        or ledger["letter_number"] < 0
    ):
        raise ValidationError("ledger.letter_number must be a non-negative integer")
    for key in ("retired", "letters", "events"):
        if not isinstance(ledger.get(key), list):
            raise ValidationError(f"ledger.{key} must be an array")
        if not all(isinstance(item, dict) for item in ledger[key]):
            raise ValidationError(f"ledger.{key} entries must be objects")
    return ledger


def load_ledger(path: Path) -> dict[str, Any]:
    path = Path(path).expanduser()
    if not path.exists():
        return default_ledger()
    loaded = json.loads(path.read_text())
    if not isinstance(loaded, dict):
        raise ValidationError(f"ledger must contain a JSON object: {path}")
    return _normalize_ledger(loaded)


def save_ledger(path: Path, ledger: dict[str, Any]) -> None:
    normalized = _normalize_ledger(ledger)
    atomic_write_text(
        Path(path),
        json.dumps(normalized, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
    )


def today_iso() -> str:
    return date.today().isoformat()
