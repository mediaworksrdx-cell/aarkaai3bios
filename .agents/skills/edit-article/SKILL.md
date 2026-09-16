---
name: edit-article
description: Edit and improve articles by restructuring sections, improving clarity, and tightening prose. Use when user wants to edit, revise, or improve an article draft.
disable-model-invocation: true
---

1. First, divide the article into sections based on its headings. Think about the main points you want to make during those sections.

Consider that information is a directed acyclic graph, and that pieces of information can depend on other pieces of information. Make sure that the order of the sections and their contents respects these dependencies.

Confirm the sections with the user.

2. For each section:

2a. Rewrite the section to improve clarity, coherence, and flow. Use maximum 240 characters per paragraph.

2b. Remove redundant or filler sentences. Every sentence must carry weight — if deleting it doesn't lose meaning, delete it.

2c. Verify that all claims, terminology, and references introduced in this section have either been grounded earlier in the article or are self-evident. Flag any forward references that assume knowledge the reader doesn't have yet.

2d. Present the rewritten section to the user for approval before moving to the next one. Do not batch multiple sections.

3. After all sections are revised:

3a. Re-read the full article end-to-end. Check for:
   - Repeated points across sections (merge or deduplicate)
   - Inconsistent terminology (pick one canonical term and use it throughout)
   - Abrupt transitions between sections (add bridging sentences where needed)
   - Dangling threads (ideas introduced but never resolved)

3b. Tighten the introduction and conclusion to match the revised body. The introduction should promise exactly what the article delivers; the conclusion should resolve exactly what the introduction promised.

4. Present the final revised article to the user. Summarise the structural changes made (sections reordered, merged, or removed) separately from prose-level changes (clarity, word choice, flow).
