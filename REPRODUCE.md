# How this repository was made (Barbados)

## History of the build

- Up to commit `644e13c` (3 to 16 November 2026): 122 Acts of the Laws of Barbados, born-digital PDFs only, built
  from a corpus file by `tools/build.py` and `tools/append.py` (the earlier `REPRODUCE.md`, in the history at
  `644e13c`, describes that build). 72 of those commits are "oldest version available" texts; 69 of them are dated
  2026-11-03, the day the text was retrieved, which the current rules no longer allow. The history is append-only,
  so they stay as published; correcting their dates needs a rewrite of `main`, which has not been done.
- `a0d6bff` (26 November 2026): those 122 folders moved from `<slug>/` to `revised-laws/cap-NNN-<slug>/`, renames only.
- After it: everything is appended by `tools/bb_build.py` in the layout of [`STRUCTURE.md`](STRUCTURE.md).

## Sources

| Source | Address | Retrieved | Licence |
| --- | --- | --- | --- |
| Statutes of Barbados (consolidated, L.R.O.) | <https://www.barbadoslawcourts.gov.bb/laws/consolidated-laws/statutes-of-barbados> | from 2026-11-26 | None stated; footer "Copyright Barbados Judicial System. All Rights Reserved." |
| Subsidiary Legislation of Barbados (consolidated) | <https://www.barbadoslawcourts.gov.bb/laws/consolidated-laws/subsidiary-legislation-of-barbados> | from 2026-11-26 | as above |
| Acts, annual volumes 2009 to 2015 | <https://www.barbadoslawcourts.gov.bb/laws/annuals/acts-annual> | from 2026-11-26 | as above |
| Statutory instruments, annual volumes 2009 to 2015 | <https://www.barbadoslawcourts.gov.bb/laws/annuals> | from 2026-11-26 | as above |

robots.txt of www.barbadoslawcourts.gov.bb: `Crawl-delay: 10`, nothing under `/assets/` or `/laws/` disallowed.

Not used: the Parliament's laws portal (barbadosparliament-laws.com), whose API answers only requests carrying a key
its own scripts generate (an anti-automation gate, not bypassed); barbadosparliament.com, which publishes Bills, not
Acts as passed.

## Steps

1. `fetch_runner.py`: the listing pages, then each PDF, one request at a time 10.5 s apart (the site's crawl delay),
   backing off on 429/5xx and stopping after three blocks in a row. Order: the Constitution, core statutes, all
   statutes, annual Acts, consolidated subsidiary legislation, annual statutory instruments. For each file it records
   pages, text-layer size, pages that are whole-page images, the PDF producer and a word-quality score
   (`state/fetched.json`).
2. `bb_build.py`: one commit per instrument, appended to `main` with `git fast-import`, in batches of 300.
3. `ship_runner.py`: runs the build every 15 minutes and pushes after each batch (fast-forward only; checked with
   `git ls-remote`); refreshes [`data/held.json`](data/held.json).

## Reading the text

- No OCR is run. Born-digital PDFs (PageMaker/Distiller) are read from their text layer; lines set well below the body
  type size are the marginal notes (section headings and the Acts that made or amended a section) and are left out
  of the text, but read for dating. PDFs made with Acrobat's Scan Plug-in carry the publisher's own OCR layer; it is
  taken as served when its word-quality score is 0.9 or more, with marginal notes mixed in, and tagged
  `Text-source: publisher OCR`. Files with no usable text layer, or an unreadable one, are held.
- Running heads ("L.R.O. 2002 Bail CAP. 122A", "THE LAWS OF BARBADOS", page numbers) are removed at page edges.
- Sections are numbered paragraphs at the start of a line ("12. ", "12A. "); the longest ascending run of substantial
  sections is taken, so the arrangement of sections stays in `preamble.md`. Schedules follow the last section.

## Dating

- Consolidated texts (Constitution, chapters, consolidated subsidiary legislation): if the margin names only the Act
  itself and a commencement date is printed in brackets under the long title, that day, credited to the Act.
  Otherwise 31 December of the latest year the edition shows (the L.R.O. year on its pages and the Acts its margin
  notes cite), credited to the Law Revision Office and marked as a placeholder in `In-force-basis`.
- Annual Acts and statutory instruments, in order: a commencement day stated in the text; the date printed in
  brackets under the long title; the Gazette day; the Governor-General's assent (Acts); the day the Act passed
  Parliament; the day the instrument was made. With none of these the instrument is held.
- Nothing is dated by the day it was retrieved.
