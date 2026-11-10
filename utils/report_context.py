"""Tiny API that page objects / tests use to feed the HTML report.

Everything here is a safe no-op when no report is active, so page objects can
also be used from plain scripts.
"""
from __future__ import annotations
import base64
import functools
import html
import logging
import re
import time
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List

_log = logging.getLogger("report")


@dataclass
class Screenshot:
    name: str
    data_b64: str
    mime: str = "image/png"
    caption: str = ""


@dataclass
class StepRecord:
    name: str
    depth: int
    start: float
    duration: float = 0.0
    status: str = "passed"
    error: str = ""
    level: str = "INFO"
    logger: str = ""
    screenshots: list[Screenshot] = field(default_factory=list)


@dataclass
class LogRecord:
    ts: float
    message: str
    level: str = "INFO"
    logger: str = ""


@dataclass
class TestRecord:
    __test__ = False  # stop pytest trying to collect this class

    nodeid: str
    name: str
    description: str = ""
    airport: str = "-"
    tc: str = ""
    markers: list = field(default_factory=list)
    status: str = "RUNNING"          # PASSED | FAILED | ERROR | SKIPPED
    start: float = 0.0
    duration: float = 0.0
    error: str = ""
    skip_reason: str = ""
    steps: list[StepRecord] = field(default_factory=list)
    logs: list[LogRecord] = field(default_factory=list)
    screenshots: list[Screenshot] = field(default_factory=list)

    @property
    def group(self) -> str:
        if self.status in ("FAILED", "ERROR"):
            return "failed"
        if self.status == "SKIPPED":
            return "skipped"
        return "passed"

    @property
    def warnings(self) -> int:
        return sum(1 for l in self.logs if l.level == "WARNING")

    @property
    def errors(self) -> int:
        return sum(1 for l in self.logs if l.level in ("ERROR", "CRITICAL"))


_current: Optional[TestRecord] = None
_depth = 0
_active_steps: List[StepRecord] = []


def set_current(record: Optional[TestRecord]) -> None:
    global _current, _depth, _active_steps
    _current = record
    _depth = 0
    _active_steps = []


def get_current() -> Optional[TestRecord]:
    return _current


def clean_summary_text(text: str) -> str:
    """Sanitize message, removing raw python object reprs and internal noise."""
    if not text:
        return ""
    s = str(text).strip()
    # Strip <class '...'> or <... object at 0x...>
    s = re.sub(r"<[a-zA-Z_][\w.]*\s+object\s+at\s+0x[0-9a-fA-F]+>", "", s)
    s = re.sub(r"<Page\s+url=[^>]+>", "", s)
    s = re.sub(r"<Locator\s+frame=[^>]+>", "", s)
    return s.strip()


@contextmanager
def step(name: str):
    """Record a named step (shown in the report and the console log)."""
    global _depth, _active_steps
    clean_name = clean_summary_text(name) or str(name)
    _log.info("STEP: %s", clean_name)
    record = None
    if _current is not None:
        record = StepRecord(name=clean_name, depth=_depth, start=time.time())
        _current.steps.append(record)
        _active_steps.append(record)
    _depth += 1
    try:
        yield
    except BaseException as exc:
        if record is not None:
            record.status = "failed"
            first_line = str(exc).strip().splitlines()[0] if str(exc).strip() else type(exc).__name__
            record.error = f"{type(exc).__name__}: {first_line}"
        raise
    finally:
        _depth -= 1
        if record is not None:
            record.duration = time.time() - record.start
            if _active_steps and _active_steps[-1] is record:
                _active_steps.pop()


def attach_screenshot(data: bytes, name: str, caption: str = "", mime: str = "image/png") -> None:
    """Attach screenshot bytes to the current test record and the active failing step."""
    if _current is None:
        return
    b64_str = base64.b64encode(data).decode("ascii")
    # Avoid duplicate additions of the exact same screenshot
    if _current.screenshots and _current.screenshots[-1].data_b64 == b64_str:
        return
    shot = Screenshot(name=name, data_b64=b64_str, mime=mime, caption=caption or name)
    _current.screenshots.append(shot)
    if _active_steps:
        if not (_active_steps[-1].screenshots and _active_steps[-1].screenshots[-1].data_b64 == b64_str):
            _active_steps[-1].screenshots.append(shot)


class LogCapture(logging.Handler):
    """Copies every log record emitted during a test into its report record."""

    def emit(self, record: logging.LogRecord) -> None:
        if _current is None:
            return
        try:
            message = record.getMessage()
            if record.exc_info:
                message += "\n" + "".join(traceback.format_exception(*record.exc_info)).rstrip()
            # Omit huge binary or raw base64 dumps in log lines
            if "data:image" in message and len(message) > 500:
                message = re.sub(r"data:image/[^;]+;base64,[A-Za-z0-9+/=]{50,}", "[IMAGE_DATA]", message)
            _current.logs.append(
                LogRecord(ts=record.created, level=record.levelname, logger=record.name, message=message)
            )
        except Exception:  # never let reporting break a test
            pass


# ---------------------------------------------------------------------------
# Allure step bridge: automatically route allure.step into report_context.step
# ---------------------------------------------------------------------------
try:
    import allure
    _orig_allure_step = getattr(allure, "step", None)

    class _AllureStepBridge:
        def __init__(self, title):
            self.title = str(title)
            self._allure_ctx = None
            self._rc_ctx = None

        def __enter__(self):
            if _orig_allure_step is not None:
                try:
                    self._allure_ctx = _orig_allure_step(self.title)
                    self._allure_ctx.__enter__()
                except Exception:
                    pass
            self._rc_ctx = step(self.title)
            return self._rc_ctx.__enter__()

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self._rc_ctx:
                try:
                    self._rc_ctx.__exit__(exc_type, exc_val, exc_tb)
                except Exception:
                    pass
            if self._allure_ctx:
                try:
                    self._allure_ctx.__exit__(exc_type, exc_val, exc_tb)
                except Exception:
                    pass
            return False

        def __call__(self, fn):
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                with self:
                    return fn(*args, **kwargs)
            return wrapper

    allure.step = _AllureStepBridge

    # ---------------------------------------------------------------------------
    # Allure attach bridge: automatically route allure.attach screenshots to report_context
    # ---------------------------------------------------------------------------
    _orig_allure_attach = getattr(allure, "attach", None)

    def _allure_attach_bridge(body, name=None, attachment_type=None, extension=None):
        if _orig_allure_attach is not None:
            try:
                _orig_allure_attach(body, name=name, attachment_type=attachment_type, extension=extension)
            except Exception:
                pass
        try:
            is_image = False
            att_type_str = str(attachment_type or "").lower()
            if "png" in att_type_str or "image" in att_type_str or "jpg" in att_type_str or "jpeg" in att_type_str:
                is_image = True
            elif isinstance(body, bytes) and (body.startswith(b"\x89PNG") or body.startswith(b"\xff\xd8\xff")):
                is_image = True

            if is_image and isinstance(body, bytes):
                mime = "image/jpeg" if ("jpg" in att_type_str or "jpeg" in att_type_str or body.startswith(b"\xff\xd8\xff")) else "image/png"
                attach_screenshot(body, name=name or "Screenshot", caption=name or "Screenshot", mime=mime)
        except Exception:
            pass

    if _orig_allure_attach is not None:
        _orig_allure_attach_file = getattr(_orig_allure_attach, "file", None)

        def _allure_attach_file_bridge(source, name=None, attachment_type=None, extension=None):
            if _orig_allure_attach_file is not None:
                try:
                    _orig_allure_attach_file(source, name=name, attachment_type=attachment_type, extension=extension)
                except Exception:
                    pass
            try:
                p = Path(source)
                if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg"):
                    data = p.read_bytes()
                    mime = "image/jpeg" if p.suffix.lower() in (".jpg", ".jpeg") else "image/png"
                    attach_screenshot(data, name=name or p.name, caption=name or p.name, mime=mime)
            except Exception:
                pass

        _allure_attach_bridge.file = _allure_attach_file_bridge
        for attr in ("attachment_type",):
            if hasattr(_orig_allure_attach, attr):
                setattr(_allure_attach_bridge, attr, getattr(_orig_allure_attach, attr))
        allure.attach = _allure_attach_bridge
except Exception:
    pass
