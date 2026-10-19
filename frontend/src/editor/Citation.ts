import { Node, mergeAttributes } from "@tiptap/core";

export const Citation = Node.create({
  name: "citation",
  group: "inline",
  inline: true,
  atom: true,
  selectable: true,
  addAttributes() {
    return {
      sourceId: { default: null, parseHTML: (element) => element.getAttribute("data-source-id"), renderHTML: (attributes) => ({ "data-source-id": attributes.sourceId }) },
    };
  },
  parseHTML() { return [{ tag: "span[data-source-id]" }]; },
  renderHTML({ HTMLAttributes }) { return ["span", mergeAttributes(HTMLAttributes, { class: "citation-marker" }), "[источник]"]; },
  renderText({ node }) { return `[${String(node.attrs.sourceId ?? "источник").slice(0, 8)}]`; },
});
