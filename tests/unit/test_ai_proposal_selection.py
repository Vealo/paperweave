import pytest

from paperweave.modules.ai_proposals.errors import InvalidSelectionError
from paperweave.modules.ai_proposals.selection import replace_selected_text, selected_text_at


def test_selected_text_and_replacement_use_tiptap_positions():
    doc = {"type": "doc", "content": [{"type": "paragraph", "content": [
        {"type": "text", "text": "Original"}, {"type": "text", "text": " claim", "marks": [{"type": "bold"}]}
    ]}]}
    assert selected_text_at(doc, 1, 8) == "Original"
    updated = replace_selected_text(doc, 1, "Original", "Suggestion")
    assert updated["content"][0]["content"][0]["text"] == "Suggestion"
    assert updated["content"][0]["content"][1]["text"] == " claim"
    assert doc["content"][0]["content"][0]["text"] == "Original"


def test_selection_cannot_cross_textblock_boundaries():
    doc = {"type": "doc", "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": "One"}]},
        {"type": "paragraph", "content": [{"type": "text", "text": "Two"}]},
    ]}
    with pytest.raises(InvalidSelectionError):
        selected_text_at(doc, 2, 5)
