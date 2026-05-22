"""
Deterministic markdown rendering via Jinja2 templates.
Content-hashes the rendered output and skips writes when unchanged.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def render(template_name: str, context: dict[str, Any]) -> str:
    env = _env()
    tmpl = env.get_template(template_name)
    return tmpl.render(**context)


def write_if_changed(path: Path, content: str) -> bool:
    """Write content to path only if it differs. Returns True if file was written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() == content:
        return False
    path.write_text(content)
    return True


def render_and_write(template_name: str, context: dict[str, Any], dest: Path) -> bool:
    content = render(template_name, context)
    return write_if_changed(dest, content)
