"""Minimal YAML-subset parser for schema files. Handles the flat structure used in our schemas.

Supports: scalars, lists, nested dicts (by indentation), inline flow mappings are NOT supported.
This avoids requiring PyYAML as a dependency.
"""

import re
from typing import Any


def parse_yaml(text: str) -> dict:
    """Parse a YAML-subset string into a Python dict."""
    lines = text.split("\n")
    return _parse_block(lines, 0, 0)[0]


def _get_indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _parse_value(raw: str) -> Any:
    raw = raw.strip()
    if not raw:
        return None
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1].replace("\\\\", "\\")
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    if raw.lower() in ("true", "yes"):
        return True
    if raw.lower() in ("false", "no"):
        return False
    if raw.lower() in ("null", "~", ""):
        return None
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def _parse_block(lines: list[str], start: int, base_indent: int) -> tuple[dict, int]:
    result = {}
    i = start

    while i < len(lines):
        line = lines[i]

        if not line.strip() or line.strip().startswith("#"):
            i += 1
            continue

        indent = _get_indent(line)

        if indent < base_indent:
            break

        if indent > base_indent and i > start:
            break

        stripped = line.strip()

        if stripped.startswith("- "):
            break

        if ":" in stripped:
            colon_idx = stripped.index(":")
            key = stripped[:colon_idx].strip()
            value_part = stripped[colon_idx + 1:].strip()

            if value_part:
                result[key] = _parse_value(value_part)
                i += 1
            else:
                next_i = i + 1
                while next_i < len(lines) and (not lines[next_i].strip() or lines[next_i].strip().startswith("#")):
                    next_i += 1

                if next_i < len(lines):
                    next_line = lines[next_i]
                    next_indent = _get_indent(next_line)

                    if next_indent > indent and next_line.strip().startswith("- "):
                        items, next_i = _parse_list(lines, next_i, next_indent)
                        result[key] = items
                        i = next_i
                    elif next_indent > indent:
                        sub_dict, next_i = _parse_block(lines, next_i, next_indent)
                        result[key] = sub_dict
                        i = next_i
                    else:
                        result[key] = None
                        i += 1
                else:
                    result[key] = None
                    i += 1
        else:
            i += 1

    return result, i


def _parse_list(lines: list[str], start: int, base_indent: int) -> tuple[list, int]:
    result = []
    i = start

    while i < len(lines):
        line = lines[i]

        if not line.strip() or line.strip().startswith("#"):
            i += 1
            continue

        indent = _get_indent(line)

        if indent < base_indent:
            break

        stripped = line.strip()

        if not stripped.startswith("- "):
            if indent == base_indent:
                break
            i += 1
            continue

        item_content = stripped[2:].strip()

        if ":" in item_content and not item_content.startswith('"'):
            item_dict = {}
            colon_idx = item_content.index(":")
            key = item_content[:colon_idx].strip()
            val = item_content[colon_idx + 1:].strip()
            item_dict[key] = _parse_value(val) if val else None

            i += 1
            while i < len(lines):
                sub_line = lines[i]
                if not sub_line.strip() or sub_line.strip().startswith("#"):
                    i += 1
                    continue
                sub_indent = _get_indent(sub_line)
                if sub_indent <= base_indent:
                    break
                sub_stripped = sub_line.strip()
                if ":" in sub_stripped:
                    ci = sub_stripped.index(":")
                    k = sub_stripped[:ci].strip()
                    v = sub_stripped[ci + 1:].strip()
                    item_dict[k] = _parse_value(v) if v else None
                i += 1

            result.append(item_dict)
        else:
            result.append(_parse_value(item_content))
            i += 1

    return result, i


def load_yaml_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return parse_yaml(f.read())
