# Independent textbook illustrations (2026-09-15)

Update: the restoration now covers chapters 1–8. See [the all-chapter display record](textbook-all-chapters-display.md). The scope below documents the earlier chapter-1 recovery step.

The whole-page preview gallery has been removed at the user's request. Learn again displays individual illustrations beside their associated explanation, with captions and click-to-enlarge links.

## Restored scope

Eight reviewed crops from chapter 1: figures 1.2, 1.4, 1.7a/b, 1.8a/b, 1.10 and 1.13. These cover the existing six illustrated explanation blocks. All eight crops were visually checked for complete axes and labels. This does NOT restore all 262 entries in the figure manifest or add illustrations to chapters 2-8.

The constant-acceleration block incorrectly included an unlabelled asset for figure 1.14 (secants and slope) just because it shared PDF page 20. Removed that association; the block retains figure 1.13 (linear velocity and quadratic distance).

Changed verified_content.json to explicit figure IDs so future ingestion preserves the reviewed associations. Updated only figure_ids and requires_figure metadata for the corresponding six records in the active Chroma collection; documents and embeddings remain unchanged.

## Reproduce

```powershell
python -m scripts.restore_textbook_figures
```

Requires pypdfium2. Reads local PDFs, figures.json and the reviewed fractional crop rectangles in figure_crops.json. Writes crops at the original expected paths under parsed/. Generated assets remain ignored by Git and must be recreated after cloning. The earlier whole-page generation script and assets remain as offline inspection material; they are no longer returned by the concept API or displayed in Learn.

## Validation

- All eight extracted crops visually reviewed against the original pages.
- Six regression tests passed, including unavailable-image handling and the corrected association.
- Frontend build passed; existing bundle-size warning remains.
- Live concept endpoints for sections 1.1, 1.2 and 1.3 returned 2, 5 and 1 available images respectively; all eight URLs returned valid PNGs with HTTP 200.
- Full-page gallery field removed from the API. Browser layout was not visually tested.

---

## Historical whole-page fallback (superseded)

# Textbook image recovery (2026-09-15)

## Implemented

The original parsed image directory was absent. The figure manifest listed 262 image records, but none of the referenced files existed locally. The active vector index linked only six chunks to nine distinct figures.

Recovered 158 whole-page previews directly from the existing chapter PDFs using pypdfium2: chapter 1: 24; chapter 2: 19; chapter 3: 32; chapter 4: 13; chapter 5: 22; chapter 6: 18; chapter 7: 10; chapter 8: 20.

The Learn page now offers an expandable, scrollable source-page gallery with lazy loading and click-to-enlarge links. Pages are selected by chapter and the section PDF page range. Missing individual crops are marked unavailable rather than rendered as broken images. English and Chinese interface labels are provided.

## Reproduce after cloning

The generated PNG files remain under the existing ignored parsed directory. Install pypdfium2 into the chosen Python environment if absent, then run from the project root:

```powershell
python -m scripts.restore_textbook_pages --chapters 1 2 3 4 5 6 7 8
```

The script creates parsed/recovered-pages and source_pages.json. No language model, embedding generation, or vector-index rebuild is required. Keep the local PDFs and figures.json available. Restart the backend if it does not use automatic reload.

## Verification

- Six tests passed: existing RAG regression tests and source-page chapter/range/missing-file tests.
- Frontend production build passed (bundle-size warning remains).
- All 158 generated assets have valid PNG signatures and map to the textbook section ranges.
- Visually inspected chapter 1 PDF page 2: figure 1.2, captions and equations remain readable.
- Running localhost:5175 concept endpoint returned seven source pages for section 1.1; an actual image request returned HTTP 200 and image/png.

## Remaining work

These are explicitly labelled original-page previews, not restored individual figure crops. This does not claim complete extraction of every illustration in the PDFs or repair chunk-level figure associations. For individual figures beside their exact explanation, recover the original MinerU output or reparse and manually verify crops and references before rebuilding the vector index. Full browser layout acceptance has not been performed.

## Formula formatting pilot (chapter 1)

Chapter 1 now has an explicit LaTeX override file at `data/textbook/mit-calculus/formula_overrides.json`. The original verified text remains unchanged; the override is applied when building a concept card, so it can be expanded or corrected without changing indexed text.

The Learn page renders these formulas through KaTeX with centered display blocks, clearer fractions and scripts, consistent spacing, and horizontal overflow for long expressions. The running student page was checked and the visible formulas now use proper fraction bars, limits, subscripts, superscripts, trigonometric notation, and arrows.
