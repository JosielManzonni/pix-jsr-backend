---
id: ref-bacen-pix-dict
title: BACEN Pix/DICT Canonical Reference
type: index
status: active
created: 2026-08-09
updated: 2026-08-09
tags: [reference, bacen, pix, dict, canon]
relations:
  - type: related_to
    target: ctx-payment
  - type: related_to
    target: ctx-decoding
---

# BACEN Pix/DICT Canonical Reference

Verbatim copies of the Brazilian Central Bank (BACEN) Pix documentation that this
repo treats as external canon. Architecture notes under `docs/architecture/` cite
these files as the point of reference for the Pix domain model (see
[[CTX-PAYMENT]]).

These are external documents: do not edit their content. Corrections happen by
re-fetching a newer upstream version and updating the table below.

## Documents

| File | Source document | Version | Lang | Source |
|---|---|---|---|---|
| `Resolution-BCB-1.md` | Resolution BCB 1/2020 — Pix Regulation (official EN translation) | 2020, consolidated as retrieved | EN | Wayback snapshot of bcb.gov.br PDF |
| `Manual-Operacional-DICT.md` | Manual Operacional do DICT | v8.4 (v8.5 announced, vigencia 2026-09-01) | PT | bcb.gov.br PDF |
| `API-DICT-spec.json` | DICT API — OpenAPI 3.0.0 spec | 2.12.1 | EN | Extracted from Redocly-embedded spec, bcb.gov.br pix/api-dict |
| `FAQ-Participantes.md` | FAQ — Participantes do Pix (devolution topics) | as retrieved | PT | bcb.gov.br PDF |

## Retrieval and refresh

All files were fetched and converted on 2026-08-09 (anydoc CLI for the PDF-to-Markdown conversions). To refresh: download the newest upstream document, convert, replace the file, and update the Version and date in the table above — never hand-edit content.
