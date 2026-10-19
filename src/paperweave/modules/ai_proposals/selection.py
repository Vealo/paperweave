"""Tiptap position validation and replacement for a single text block."""

from copy import deepcopy
from typing import Any

from paperweave.modules.ai_proposals.errors import InvalidSelectionError


def _node_size(node: dict[str, Any]) -> int:
    if node.get("type") == "text":
        return len(str(node.get("text", "")))
    content = node.get("content")
    if isinstance(content, list):
        return 2 + sum(_node_size(child) for child in content)
    return 1


def _text_leaves(document: dict[str, Any]):
    leaves: list[tuple[tuple[int, ...], int, int, int, str]] = []

    def walk(node: dict[str, Any], path: tuple[int, ...], start: int, block_id: int | None) -> None:
        node_type = node.get("type")
        if node_type == "text":
            value = str(node.get("text", ""))
            if value:
                leaves.append((path, start, start + len(value), block_id if block_id is not None else start, value))
            return
        if node_type in {"paragraph", "heading"}:
            block_id = start
        children = node.get("content")
        if not isinstance(children, list):
            return
        cursor = start if node_type == "doc" else start + 1
        for index, child in enumerate(children):
            if not isinstance(child, dict):
                raise InvalidSelectionError("invalid_selection")
            walk(child, path + (index,), cursor, block_id)
            cursor += _node_size(child)

    if document.get("type") != "doc" or not isinstance(document.get("content"), list):
        raise InvalidSelectionError("invalid_selection")
    walk(document, (), 0, None)
    return leaves


def selected_text_at(document: dict[str, Any], position: int, length: int) -> str:
    if position < 0 or length < 1:
        raise InvalidSelectionError("invalid_selection")
    end = position + length
    matching = [leaf for leaf in _text_leaves(document) if leaf[2] > position and leaf[1] < end]
    if not matching or len({leaf[3] for leaf in matching}) != 1:
        raise InvalidSelectionError("invalid_selection")
    pieces = []
    for _path, start, stop, _block, value in matching:
        left = max(0, position - start)
        right = min(len(value), end - start)
        pieces.append(value[left:right])
    return "".join(pieces)


def replace_selected_text(document: dict[str, Any], position: int, original: str, replacement: str) -> dict[str, Any]:
    if not original:
        raise InvalidSelectionError("invalid_selection")
    end = position + len(original)
    leaves = _text_leaves(document)
    matching = [leaf for leaf in leaves if leaf[2] > position and leaf[1] < end]
    if not matching or len({leaf[3] for leaf in matching}) != 1:
        raise InvalidSelectionError("invalid_selection")
    if "".join(value[max(0, position - start):min(len(value), end - start)] for _, start, stop, _, value in matching) != original:
        raise InvalidSelectionError("invalid_selection")

    result = deepcopy(document)
    first = True
    for path, start, stop, _block, value in matching:
        left = max(0, position - start)
        right = min(len(value), end - start)
        new_text = value[:left] + (replacement if first else "") + value[right:]
        first = False
        current: Any = result
        for index in path:
            current = current["content"][index]
        current["text"] = new_text

    def prune(node: dict[str, Any]) -> None:
        children = node.get("content")
        if not isinstance(children, list):
            return
        for child in children:
            prune(child)
        node["content"] = [child for child in children if child.get("type") != "text" or child.get("text")]

    prune(result)
    return result
