# Barbados: law history in git

The law of Barbados as a git history: one file per provision, and the law that made each change as the commit's author, so `git blame` names the law behind every line.

It follows the shared design of [lexifina/global-law](https://github.com/lexifina/global-law), which places it at `bb/`.

**What is in it now**

<!-- acts:start -->
| Folder | Act | Versions | Dated |
| --- | --- | ---: | --- |
| `agricultural-development-fund/` | Agricultural Development Fund Act, Cap. 252B | 1 | 2001-06-21, commencement (never amended in this edition) |
| `agricultural-diagnostic-and-other-services-fees/` | Agricultural, Diagnostic and Other Services (Fees) Act, Cap. 252A | 1 | 1995-12-07, commencement (never amended in this edition) |
| `aliens/` | Aliens Act, Cap. 185 | 1 | 2026-11-03, oldest version available |
| `anti-terrorism/` | Anti-Terrorism Act, Cap. 158 | 1 | 2022-08-11, oldest version available |
| `architects-registration/` | Architects Registration Act, Cap. 366 | 1 | 2026-11-03, oldest version available |
| `arts-and-sport-promotion-fund/` | Arts and Sport Promotion Fund Act, Cap. 039 | 1 | 2026-11-03, oldest version available |
| `bail/` | Bail Act, Cap. 122A | 1 | 2022-08-11, oldest version available |
| `bankruptcy-and-insolvency/` | Bankruptcy and Insolvency Act, Cap. 303 | 1 | 2026-11-03, oldest version available |
| `barbados-accreditation-council/` | Barbados Accreditation Council Act, Cap. 038A | 1 | 2004-11-15, commencement (never amended in this edition) |
| `barbados-international-business-promotion-corporation/` | Barbados International Business Promotion Corporation Act, Cap. 340A | 1 | 2026-11-03, oldest version available |
| `caribbean-community/` | Caribbean Community Act, Cap. 015 | 1 | 2026-11-03, oldest version available |
| `caribbean-community-movement-of-skilled-nationals/` | Caribbean Community (Movement of Skilled Nationals) Act, Cap. 186A | 1 | 2005-01-24, commencement (never amended in this edition) |
| `caribbean-court-of-justice/` | Caribbean Court of Justice Act, Cap. 117 | 1 | 2026-11-03, oldest version available |
| `caribbean-disaster-emergency-response-agency/` | Caribbean Disaster Emergency Response Agency Act, Cap. 157A | 1 | 2026-11-03, oldest version available |
| `caribbean-investment-fund/` | Caribbean Investment Fund Act, Cap. 322 | 1 | 1999-07-08, commencement (never amended in this edition) |
| `catastrophe-fund/` | Catastrophe Fund Act, Cap. 039D | 1 | 2026-11-03, oldest version available |
| `caves/` | Caves Act, Cap. 389 | 1 | 2000-09-05, commencement (never amended in this edition) |
| `cemeteries/` | Cemeteries Act, Cap. 039C | 1 | 1999-06-07, commencement (never amended in this edition) |
| `centennial-honour/` | Centennial Honour Act, Cap. 400 | 1 | 2026-11-03, oldest version available |
| `computer-misuse/` | Computer Misuse Act, Cap. 124B | 1 | 2022-08-11, oldest version available |
<!-- acts:end -->

Language: English. The text is that of the born-digital PDFs published by the Barbados Law Courts; the older scanned Acts (the Constitution, for one) have only an OCR text layer and are not included.

Every Act whose PDF is born-digital is included; the many scanned Acts are not (no OCR). Each Act is one version: the Law Revision Office consolidation as published. The editions print only their L.R.O. year, not the day the law is stated at. An Act whose margin note names no amending Act is dated by the commencement date printed under its long title and credited to the Act. Every other Act is an "oldest version available" commit credited to the publisher, dated by the day its text was retrieved (the first three Acts: 2022-08-11, the PDFs' Last-Modified date), and naming the Acts in its margin note; its wording may predate later amendments the edition does not show. Marginal notes give each section's heading; amendment references in the margin are left out.

Sources and terms are in `LICENSE`; how it was built is in `REPRODUCE.md`. Not legal advice; for anything that matters, read the original.
