"""Shared CLI utilities."""

import json
from pathlib import Path
from typing import Any, Callable


def output_json(data: dict[str, Any], output_path: Path | None) -> None:
    """Output JSON to stdout or file."""
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    if output_path:
        output_path.write_text(json_str, encoding="utf-8")
        print(f"Output written to: {output_path}")
    else:
        print(json_str)


def output_result(
    data: dict[str, Any],
    json_output: bool,
    output_path: Path | None,
    render_fn: Callable[..., None],
    *render_args: Any,
) -> None:
    """Universal output handler - JSON or Rich.

    Args:
        data: JSON-serializable data dict
        json_output: True for JSON output
        output_path: Optional file path for output
        render_fn: Rich render function
        *render_args: Arguments for render function
    """
    if json_output:
        output_json(data, output_path)
    else:
        render_fn(*render_args)
