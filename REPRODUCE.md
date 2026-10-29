# How this repository was made (Barbados)

This file is written by the build on 2026-10-29, the day the source data was retrieved.

## Sources

| Source | Address | Retrieved | Licence |
| --- | --- | --- | --- |
| Barbados Law Courts: Statutes of Barbados (consolidated laws) | <https://www.barbadoslawcourts.gov.bb/laws/consolidated-laws/statutes-of-barbados/> | 2026-10-29 | no licence stated |

Every word of law in this repository comes from these sources. Lexifina reads them and records each act's dated versions, and the laws that made each change, in one corpus file. This repository is built from that file.

## What is in it

| Act | Title | Versions | Span |
| --- | --- | ---: | --- |
| `computer-misuse` | Computer Misuse Act, Cap. 124B | 1 | 2022-08-11 to 2022-08-11 |
| `anti-terrorism` | Anti-Terrorism Act, Cap. 158 | 1 | 2022-08-11 to 2022-08-11 |
| `bail` | Bail Act, Cap. 122A | 1 | 2022-08-11 to 2022-08-11 |

The build made 3 commits:

| Commits | Kind |
| ---: | --- |
| 3 | first version of an act |
| 0 | one law on its in-force day |
| 0 | changes no amendment note explains, credited to the publisher |

Other counts:
- 0 commits on the branch `future`: laws not yet in force on 2026-10-29.
- 0 commits dated 1 January 1970: in force before 1970, with the real day in their `In-force` trailer.
- 0 laws in the record.
- 3 tags.

## Dates

Each commit is dated at noon (America/Barbados) on the day the change took effect. The other dates, enacted and published, are trailers.

When a law gives no date of its own, the default rule applies: No dated history is published. Each Act is one oldest-version-available commit dated 2022-08-11, the Last-Modified date of the published PDF; the Act commencement dates in the texts are not applied. https://www.barbadoslawcourts.gov.bb/assets/content/pdfs/statutes/

## How the history is built

`tools/build.py` turns the corpus into this history in one pass: one commit per law, on the day it took effect. The same corpus always gives the same commit hashes. `tools/check_repo.py` reads every version back from git and compares it with the corpus. `tools/on.py` shows the law as it stood on any date. The corpus format is described in `tools/SCHEMA.md`.

- Corpus: sha256 `80f6a554c67a48dd7ee840254996a7e75f5bf6137dcae8dc56e473371c75cf3b` (115383 bytes).
- Builder blob hashes (`git hash-object`): `build.py` `6229396f41c9d7f1d6f405becfbe4097b35b82da`, `check.py` `5e112e6a33b7e93d00112e55f01fbb4fb3fdd8da`, `on.py` `644a6c0857fbcc72562032b58d57aa113fee0641`.
- Python 3.12.10; git version 2.46.0.windows.1.

## Checks

Not yet run for this build.

No second build of this corpus has been compared yet.

## Decisions made by hand

- Three Acts were chosen because their PDFs are born-digital (Acrobat Distiller): Computer Misuse Cap. 124B, Anti-Terrorism Cap. 158 and Bail Cap. 122A. The Constitution, Citizenship and Interpretation PDFs are scans with an incomplete OCR layer and were not used (no OCR).
- Sections are split by sequential section number; margin notes, footnotes, page headers and italic sub-headings are dropped; schedules, where present, stay at the end of the last section.
- Version date 2022-08-11 is the Last-Modified header of each PDF (the source gives no consolidation date in the text beyond the L.R.O. year).

## What AI did and did not do

The scripts that read the sources and build this repository were written by Claude Code running Claude Opus 5.5 (`claude-opus-5-5`) under Lexifina's direction.

No model wrote, translated or corrected legal text. No model runs at build time. Every word of law in this repository comes from the official sources above.

The commit messages are written by `build.py` from the source data.

Model use at data-build time:
- Claude Code wrote the parser; it did not write or alter any legal text. 0 model calls at data-build time.
