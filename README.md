# Barbados: law history in git


The law of Barbados as a git history: one file per section, one commit per version on the day it took effect where the text gives that day, and the Act that made it as the commit's author where the edition names one. `git blame` names the Act (or the publisher) behind every line; `git log` lists every change to a section; picking a date gives the text in force that day.

Part of [lexifina/global-law](https://github.com/lexifina/global-law), one git history for every country's law: this is Barbados' national law, which global-law reads at `barbados/national/acts/`.

**What is in it now:** 122 Acts of the Laws of Barbados, each in one version so far (4,695 sections, schedules and preambles): 50 dated by their commencement, from 1994 to 2009, and 72 as the oldest version available. There is no `PLAN.md`; [`REPRODUCE.md`](REPRODUCE.md) lists every Act with its version, and [`data/laws.csv`](data/laws.csv) lists the 227 Acts the record names (the 50 credited Acts and those the other Acts' margin notes name).

Each Act is a folder named after its short title, with one file per section, schedule and preamble, plus a `README.md` listing its provisions (`consumer-protection/sec-007.md` is section 7, Unfair terms, of the Consumer Protection Act, Cap. 326D).

The text is in English, as the Barbados Law Courts' PDFs print it; each margin note gives its section's heading, and the amendment references in the margin are left out.

## Questions as git commands

| Question | Command |
| --- | --- |
| Every change to section 7 of the Consumer Protection Act | `git log -p --word-diff -- consumer-protection/sec-007.md` |
| Which Act wrote each line of section 7? | `git blame consumer-protection/sec-007.md` |
| Every version of the Act, with the day each took effect | `git log --format="%h %(trailers:key=In-force,valueonly,separator=) %an" -- consumer-protection ':!*/README.md'` |
| Section 7 as in force on 1 January 2015 | `python tools/on.py 2015-01-01 consumer-protection 7` |

**Outside git**, we also host this record publicly, for free:

- **[Ask Claude about Barbadian law](https://global-law.lexifina.com/v1/try_claude?country=barbados)**: opens Claude with a first question ready.
- **[Ask ChatGPT](https://global-law.lexifina.com/v1/try_chatgpt?country=barbados)**: the same question in ChatGPT.
- **[Search Barbadian law on our site](https://lexifina.com/law?country=barbados&q=unfair+terms)**: a search for "unfair terms", with each provision's text and its versions, no account needed.
- **[Developer REST API](https://global-law.lexifina.com/v1/search_law?query=unfair+terms&jurisdiction=barbados)**: the same search as JSON, with no key. See the [documentation here](https://lexifina.com/api/global-law).

Both assistants read the record through the free Global law connector (MCP, `https://global-law.lexifina.com/mcp`); the first time, the chat gives you the link that adds it. Ask in English.

**Host it yourself easily.** All it takes is git and Python, and the tools run on your machine:

```sh
git clone --depth 1 https://github.com/lexifina/global-law && cd global-law
python3 tools/countries.py add barbados/national/acts
python3 tools/law.py show 2026-01-01 barbados/national/acts/consumer-protection/sec-007.md
```

Opened in Claude Code, Cursor, VS Code or Codex, the clone also starts a local MCP server with the same tools ([MCP.md](https://github.com/lexifina/global-law/blob/main/MCP.md)).

## Dates

Each commit is dated at noon, America/Barbados, on the day the version took effect, and carries it in its `In-force:` trailer. The editions print only their L.R.O. year, not the day the law is stated at, so:

- an Act whose margin note at the long title names no amending Act is dated by the commencement date printed under its long title (50 Acts);
- every other Act is dated by the day its text was retrieved, 2026-11-03 (the first three, Anti-Terrorism, Bail and Computer Misuse, 2022-08-11, the Last-Modified date of their PDFs).

The 50 are credited to the Act itself (`Act 2002-20`); the other 72 are "oldest version available" commits credited to the publisher, `Supreme Court Registry, Barbados Law Courts (Laws of Barbados)`, and their messages name the Acts in the margin note.

## How it is checked

- `tools/check_repo.py` reads every Act back from git on the day its version took effect, choosing the commit by its `In-force:` trailer, and compares it file by file with the corpus it was built from; it also checks that every commit's trailers parse and that there are no merge commits. [`REPRODUCE.md`](REPRODUCE.md) records no run of it for the current build yet.
- `tools/build.py` writes the history from the corpus in one pass, and the same corpus always gives the same commit hashes; `REPRODUCE.md` gives the corpus's sha256 and the builder's hashes. No second build has been compared yet.
- Only born-digital PDFs are read, from their text layer; scanned PDFs, whose OCR layer is incomplete, are left out rather than read with errors.
- History is append-only: each batch of Acts was appended with its own documentation commit, and nothing is rewritten.

## What it does not show

- **Most Barbados law.** 122 of the 540 PDFs the Barbados Law Courts list: the scanned Acts (the Constitution, Citizenship and Interpretation Acts among them) are not read. No subsidiary legislation and no case law.
- **Amendments after an edition, and earlier versions.** Each Act is one Law Revision Office consolidation; an "oldest version available" text may predate amendments the edition does not show, and no Act's earlier wording is here.
- **The amendment references in the margin**, which say which Act changed a section.

## Sources

| Source | Kind | Past versions | Notes |
| --- | --- | --- | --- |
| [Statutes of Barbados](https://www.barbadoslawcourts.gov.bb/laws/consolidated-laws/statutes-of-barbados/) (Barbados Law Courts) | Consolidated laws, Law Revision Office editions | no, one edition per Act, dated only by its L.R.O. year | Each Act's text, commencement date and margin notes, from its PDF |

## Licence

See [`LICENSE`](LICENSE). The Barbados Law Courts site states no licence (its footer reads "Copyright Barbados Judicial System. All Rights Reserved."); the text of the laws is reproduced for reference with attribution to the publisher. The arrangement of this repository, its commit messages and tools are Lexifina's, under CC BY 4.0.

No AI model wrote, translated or corrected legal text; the scripts that read the sources and build this repository were written by an AI model (see [`REPRODUCE.md`](REPRODUCE.md)).

## More

From [lexifina/global-law](https://github.com/lexifina/global-law):

- [FEATURES.md](https://github.com/lexifina/global-law/blob/main/FEATURES.md): every feature, and what every corpus must support (`git blame`, `law.py`, the MCP tools)
- [FAQ.md](https://github.com/lexifina/global-law/blob/main/FAQ.md): questions and answers · [CONTRIBUTING.md](https://github.com/lexifina/global-law/blob/main/CONTRIBUTING.md): proposing changes · [MCP.md](https://github.com/lexifina/global-law/blob/main/MCP.md): the MCP server · [REPRODUCE.md](https://github.com/lexifina/global-law/blob/main/REPRODUCE.md): how it was built · [CHANGELOG.md](https://github.com/lexifina/global-law/blob/main/CHANGELOG.md)
- [FRESHNESS.md](https://github.com/lexifina/global-law/blob/main/FRESHNESS.md): how current each corpus is · [Monitoring](https://github.com/lexifina/global-law/tree/main/monitoring): whether updates are running · [WATCHING.md](https://github.com/lexifina/global-law/blob/main/WATCHING.md): how each official source is watched for changes
- [performance/](https://github.com/lexifina/global-law/tree/main/performance): how fast the tools are, measured
- [visualisations/](https://github.com/lexifina/global-law/tree/main/visualisations): charts and bridges across the world's law
- [Vulnerabilities](https://github.com/lexifina/global-law/tree/main/vulnerabilities): mistakes in legislation as published
