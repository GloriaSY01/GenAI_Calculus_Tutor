# Language switching fixes (2026-09-14)

- Shared display labels for teacher topics, reasoning grades and conditions; API identifiers and assignment values remain unchanged.
- Localized overview insights use kind and numeric params for both live and demo data. English fields remain for compatibility.
- Teacher assistant requests include language (default English for older clients). Offline summaries and notices follow the UI language; previous messages retain their original text.
- Localized demo badges and practice headers. Textbook content explicitly identified as original English.
- Restart the backend to enable insight params and assistant language handling.
- Unknown topic names and user-authored content retain their original text. This change does not translate the textbook or historical conversations.

## Follow-up: topic health labels

- Verified the running /api/analytics/class endpoint: live topics included names absent from the demo mapping. Added applications of derivatives, continuity, related rates, free chat and trigonometry review.
- Display lookup tolerates case and whitespace variations and preserves textbook section numbers. Original API values and unknown user labels remain unchanged.
