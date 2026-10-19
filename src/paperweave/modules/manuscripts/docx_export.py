"""Small, dependency-free DOCX export for the supported Tiptap manuscript subset."""

from __future__ import annotations

from html import escape
from io import BytesIO
from typing import Any
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _run(text: str, *, bold: bool = False, italic: bool = False) -> str:
    props = ("<w:rPr>" + ("<w:b/>" if bold else "") + ("<w:i/>" if italic else "") + "</w:rPr>") if bold or italic else ""
    return f"<w:r>{props}<w:t xml:space=\"preserve\">{escape(text)}</w:t></w:r>"


def _inline(nodes: list[dict[str, Any]], numbers: dict[UUID, int], bibliography: dict[UUID, Any], bold=False, italic=False) -> str:
    rendered = []
    for node in nodes:
        kind = node.get("type")
        if kind == "text":
            marks = {mark.get("type") for mark in node.get("marks", [])}
            rendered.append(_run(str(node.get("text", "")), bold=bold or "bold" in marks, italic=italic or "italic" in marks))
        elif kind == "hardBreak":
            rendered.append("<w:r><w:br/></w:r>")
        elif kind == "citation":
            try:
                source_id = UUID(str(node.get("attrs", {}).get("sourceId", "")))
            except ValueError as exc:
                raise ValueError("Citation has an invalid source identifier.") from exc
            if source_id not in numbers:
                source = bibliography.get(source_id)
                if source is None:
                    raise ValueError(f"Citation source {source_id} is not available in this project.")
                numbers[source_id] = len(numbers) + 1
            rendered.append(_run(f"[{numbers[source_id]}]"))
        else:
            rendered.append(_inline(node.get("content", []), numbers, bibliography, bold, italic))
    return "".join(rendered)


def _bibliography_text(source: Any) -> str:
    # The data model intentionally contains only these manually curated fields.
    author = source.authors.strip() if source.authors and source.authors.strip() else "Автор не указан"
    year = str(source.year) if source.year is not None else "год не указан"
    doi = f" DOI: {source.doi}." if source.doi else " DOI не указан."
    return f"{author}. {source.title}. {year}.{doi}"


def render_docx(content: dict[str, Any], sources: list[Any]) -> bytes:
    """Render a Tiptap doc as editable DOCX, with numbered GOST-style references."""
    by_id = {source.id: source for source in sources}
    numbers: dict[UUID, int] = {}
    body: list[str] = []
    for node in content.get("content", []):
        kind = node.get("type")
        text = _inline(node.get("content", []), numbers, by_id)
        if kind == "heading":
            level = max(1, min(6, int(node.get("attrs", {}).get("level", 1))))
            body.append(f'<w:p><w:pPr><w:pStyle w:val="Heading{level}"/></w:pPr>{text}</w:p>')
        elif kind in {"paragraph", "blockquote"}:
            body.append(f"<w:p>{text}</w:p>")
        elif kind in {"bulletList", "orderedList"}:
            for index, item in enumerate(node.get("content", []), 1):
                item_text = _inline(item.get("content", [{}])[0].get("content", []), numbers, by_id)
                prefix = "• " if kind == "bulletList" else f"{index}. "
                body.append(f"<w:p>{_run(prefix)}{item_text}</w:p>")
    if numbers:
        body.append(f'<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>{_run("Список литературы")}</w:p>')
        for source_id, number in sorted(numbers.items(), key=lambda item: item[1]):
            body.append(f"<w:p>{_run(f'[{number}] ' + _bibliography_text(by_id[source_id]))}</w:p>")
    document = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}"><w:body>{''.join(body)}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="850" w:bottom="1134" w:left="1701"/></w:sectPr></w:body></w:document>'''
    styles = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W_NS}"><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="28"/></w:rPr></w:style>{''.join(f'<w:style w:type="paragraph" w:styleId="Heading{i}"><w:name w:val="heading {i}"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="{32 if i == 1 else 28}"/></w:rPr></w:style>' for i in range(1, 7))}</w:styles>'''
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", '''<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>''')
        archive.writestr("_rels/.rels", '''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>''')
        archive.writestr("word/document.xml", document)
        archive.writestr("word/styles.xml", styles)
        archive.writestr("word/_rels/document.xml.rels", '''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>''')
    return output.getvalue()
