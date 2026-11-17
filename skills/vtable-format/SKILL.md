---
name: vtable-format
description: >-
  Apply a standard academic table format to a manuscript's tables (vanilla): a caption above each table
  ("Table N. Title", six words at most, sequential numbering), header row bold and body plain, one font
  and size, sentence-case cells, consistent number formatting, a Note line for source and base, the
  three-line (booktabs) rule style, each table right after the paragraph that first cites it, parallel
  tables in one layout, core models in the main text and robustness in the appendix, no estimated counts.
  Audits first, applies on request. Use when the user says "format the tables", "standardize the tables",
  "fix the table captions", "the tables look amateur", or "vtable-format". Always trigger when the user
  runs /vtable-format.
---

# vtable-format — the standard table format

Works on a Word file, a Google Doc or a LaTeX source. First list what each table does not meet (a
read-only audit); then, on request, fix it.

## The standard
1. **Caption above the table:** `Table N. <Title>`, a descriptive noun phrase of at most six words,
   never a sentence, never a method or threshold in parentheses (those go to the prose or the Note).
   Numbering sequential with no gaps or duplicates; appendix tables lettered (A.1, B.1…). The same
   punctuation and style for every caption in the paper.
2. **Header row bold, every body cell plain.** A whole table in bold is a formatting error.
3. **One font and one size** within a table, the body font, the same size in every table. Never shrink a
   table's type to make it fit: turn it landscape or move columns to an appendix table.
4. **Sentence-case cells:** "Yes"/"No", never "YES"/"NO". Fix case cell by cell, never with a
   document-wide replace ("NO" hides inside words).
5. **Consistent numbers:** comma thousands, period decimals (or the journal's convention), the same in
   every table; dates in one format.
6. **A Note below** giving the source, the base or N, and any threshold. Conceptual framing belongs in the
   prose above the table.
7. **Three-line rule style:** a top rule, a rule under the header, a bottom rule; no vertical lines, no
   lines between data rows, no shading. Check the target journal's own tables first.
8. **Placement:** each table directly after the paragraph that first cites it (or each on its own page
   where the journal asks for that). Appendices lettered in the order the text first mentions them.
9. **Every table cited in the text,** and every "Table N" in the text has a Table N.
10. **A totals row** where the prose quotes a tally ("seven of nine").
11. **Ordered columns:** when columns are political actors, order them left to right ideologically,
    summary columns last, the same order in every table.
12. **Parallel tables share one layout:** two modules reporting the same estimator use the same columns,
    the same statistics under each coefficient, the same footer rows in the same order.
13. **Core models in the main text;** robustness columns in appendix tables of the same layout, which may
    run wider.
14. **No estimated counts:** a table never shows an estimated share multiplied by a base as if it were a
    count. A rate table shows the rate and its interval; a count table shows only counted items.
15. **Widths follow content,** especially in appendix tables: short code columns narrow, the long text
    column takes the rest. A one-word header cannot wrap, so abbreviate it and define it in the Note
    rather than widening the column.
16. **A table and a figure of the same measure name their aggregation** (pooled or averaged) in both
    notes, so a reader does not mistake the difference for an error.

## Workflow
1. **Inventory:** for every table, its caption, number, style, header and body weight, font and size,
   borders, Note, position relative to its first mention.
2. **Titles from content:** derive each missing title from the column headers, the cells and the sentence
   that cites the table; never invent one. Propose titles for the author to adjust.
3. **Apply on request.** Mark new text (titles, notes) for review; format-only corrections need no
   marking. In a Google Doc, re-read the document right before editing and work from the end of the
   document backward so earlier edits do not shift later positions.
4. **Verify by looking:** export to PDF and look at every table page. Border settings read back from an
   editor are not a reliable check; the rendered page is.
5. **Report** what changed, and list deliberate exceptions (an inline matrix that should stay inline, a
   journal convention that overrides an item).

## What not to do
Don't invent a title. Don't bold body cells. Don't renumber unnumbered inline tables silently: that is an
editorial decision with cross-reference consequences, so ask. Don't touch the reference list or the whole
document's styles; this skill covers tables, their captions and their notes.

Companion skills: /vdescriptives · /vresults · /varticle-style.
