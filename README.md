# Barbados: law history in git

The law of Barbados as a git history: one file per provision, and the law that made each change as the commit's author, so `git blame` names the law behind every line.

It follows the shared design of [lexifina/global-law](https://github.com/lexifina/global-law), which places it at `bb/`.

**What is in it now (first build, retrieved 2026-10-29)**

| Folder | Act | Versions | Source |
| --- | --- | ---: | --- |
| `computer-misuse/` | Computer Misuse Act, Cap. 124B | 1 | Laws of Barbados PDF (L.R.O. 2007) |
| `anti-terrorism/` | Anti-Terrorism Act, Cap. 158 | 1 | Laws of Barbados PDF (L.R.O. 2002) |
| `bail/` | Bail Act, Cap. 122A | 1 | Laws of Barbados PDF |

Language: English. The text is that of the born-digital PDFs published by the Barbados Law Courts; the older scanned Acts (the Constitution, for one) have only an OCR text layer and are not included.

This is a first, small build, not the whole statute book. It has no dated history: each act is one "oldest version available" commit, dated from the source's own date and credited to the publisher. Texts are in the official language shown above; the English is a translation where marked, and the original governs.

Sources and terms are in `LICENSE`; how it was built is in `REPRODUCE.md`. Not legal advice; for anything that matters, read the original.
