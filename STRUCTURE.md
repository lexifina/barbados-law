# Structure

The law of Barbados, laid out by type and year. No folder holds more than 1,000 entries.

```
constitution/                         The Constitution of Barbados (Schedule to the Barbados Independence Order 1966),
                                      Law Revision Office consolidated text, one file per section
revised-laws/cap-NNN-<slug>/          A chapter of the Laws of Barbados (consolidated, L.R.O. editions), NNN being the
                                      chapter number (cap-122a-bail is Cap. 122A, the Bail Act), one file per section
revised-laws/cap-NNN-<slug>/subsidiary/<slug>/
                                      Consolidated subsidiary legislation made under that chapter
acts/<year>/<NNN>-<slug>/             An Act as enacted, from the annual volumes: Act <year>-<NNN>
subsidiary/<year>/<NNN>-<slug>/       A statutory instrument as made, from the annual volumes: S.I. <year> No. <NNN>
data/held.json                        Instruments not committed, each with the reason
```

Files in each folder: `preamble.md` (title, long title, commencement date and anything before section 1),
`sec-NNN.md` (one per section, `sec-012a.md` for section 12A), `schedule-NN.md` (one per schedule, in order). Where
the text layer has no section numbering to split on, the whole text is in `text.md`. The 122 Acts built before
26 November 2026 also carry a `README.md` listing their provisions.

## Commits

One commit per version, dated noon America/Barbados (UTC-04:00) on the day the version took effect. Every commit
carries `In-force:` (the day) and `In-force-basis:` (how it was found); those appended from 26 November 2026 on also
carry `Text-source:` (`PDF text layer`, or `publisher OCR` for a text layer the publisher made over page scans; no OCR
is run for this repository), `Source:` (the PDF) and `Source-sha256:`.

The author is the law that made the version (`Act 2002-20`, `S.I. 2010 No. 5`), or `Law Revision Office` for a
consolidated text whose edition prints no day: those are dated 31 December of the latest year the edition shows (its
L.R.O. page years and the Acts its margin notes cite), and the trailer says it is a placeholder. Nothing is dated by
the day it was retrieved; an instrument with no date in its text is held.

## Corpus

global-law reads this repository as `bb/national/acts`.
