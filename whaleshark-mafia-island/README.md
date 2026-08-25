# Predicting whale shark presence at Mafia Island, Tanzania

Machine-learning prediction of whale shark (*Rhincodon typus*) presence, built to help tour
operators **spread out** rather than converge on the same animal.

**Author:** Patrick Silingardi · **Mentor:** Samuel Haghshenas, University of Oxford
**Programme:** Veritas AI Fellowship, 2026

---

## The problem

Whale shark tourism at Mafia Island works because the sharks are there predictably: Rohner et
al. (2020) documented high residency and a repeatable seasonal cycle off the Tanzanian coast.
That finding has never been turned into anything an operator can use on a given morning.

The Whale Shark Tour Operators Network of Tanzania (WATONET) reports that the binding
operational problem is **not finding sharks — it is too many boats converging on the same shark
once one is found**. Encounters get short and contested, boats that guessed wrong burn fuel, and
the animal absorbs the entire day's pressure.

So the useful output is not only *"will there be sharks today?"* but *"where within the bay
should each boat go, so that boats spread out rather than stack up?"*

## Why the objective matters more than the accuracy

A model optimised purely for detection would make this worse, not better. Helping everyone find
the same shark faster is the opposite of the conservation claim. The objective has to include
dispersion, and the intended user is a licensed operator network, not the public. This is stated
here because it constrains what the project is allowed to build.

## Two tracks

| | Plan A — local | Plan B — global |
|---|---|---|
| Scope | Day-level presence and within-bay zone probability, Kilindoni Bay | Presence and seasonality across known aggregation sites worldwide |
| Data | Sharkbook Tanzania export + Cagua et al. (2015) Dryad deposit; MMF archive requested | OBIS + GBIF + Watts et al. (2022) |
| Status | Data in hand, **use gated on data-provider consent** | Runnable today, no permissions needed |
| Risk | High — single point of failure | Low |

Plan B is the backbone and runs regardless. Plan A folds in as a module. The two share roughly
70% of the pipeline, so the work is not wasted under either outcome.

**Decision gate: 7 September 2026.** Without the MMF data or a firm dated commitment by then,
Plan A is reframed as a design specification and data request, and all modelling effort moves to
Plan B.

## What is in here

```
notebooks/   WhaleShark_Dataset_Starter.ipynb   builds the global dataset from OBIS + GBIF
src/         clean_sharkbook_tanzania.py        cleans the Sharkbook Tanzania export
reports/     cleaning_report.txt                what was corrected and what was dropped
data/        (empty by design — see data/README.md)
```

## Reproducing this

```bash
pip install -r requirements.txt
```

**Plan B** is fully reproducible by anyone: open `notebooks/WhaleShark_Dataset_Starter.ipynb`
in Colab and run it top to bottom. It pulls from the OBIS and GBIF APIs itself and writes
`whaleshark_global_clean.csv`. No credentials, no permissions.

**Plan A** is not reproducible from this repository alone, and that is not an oversight — see
"Data availability" below. Given the Sharkbook export, `src/clean_sharkbook_tanzania.py`
reproduces the cleaned dataset exactly:

```bash
python src/clean_sharkbook_tanzania.py <export>.csv data/mafia_whaleshark_clean.csv
```

## Data availability, and why this repository contains no data

The Wildbook citation agreement requires the **prior written consent of the original data
provider** before Sharkbook records are used in any publication or product. For Mafia Island the
largest provider is the Marine Megafauna Foundation, roughly 30% of the records. A formal
request is in progress through WATONET.

The raw exports also contain the names and email addresses of individual contributors — real
people who uploaded to a research platform, not to a public dataset.

For both reasons, no occurrence data is committed here. `.gitignore` blocks data by default and
allow-lists individual safe files back in, rather than the other way round, because git history
is permanent: a file committed once and deleted later is still clonable.

## Findings so far that shaped the design

- **The open global record cannot support a bay-scale model.** Inside the Mafia Island polygon,
  GBIF and OBIS together hold 69 records, 44 of them with coordinates obscured to a median
  uncertainty of 31 km. The bay is about 20 km wide — the error is the size of the study area.
- **The open record does not even recover the known seasonality.** On those 69 records the
  apparent peak is October (33%); the Sharkbook export and the published literature put it in
  December (45%). With this sample size that is noise, not a rival signal — which is precisely
  the argument for the restricted data.
- **Effort is the central gap.** No Sharkbook effort field is populated: these are presence-only
  records with no denominator. The Cagua et al. (2015) deposit is the only source carrying
  search-effort hours, and 14 of its 32 surveyed weeks recorded zero sharks — genuine absences.
- **Sampling effort is not abundance.** ~80% of GBIF records for this species are satellite
  telemetry from a few dozen tagged animals. Untreated, a global model learns tourism
  infrastructure and reports it as ecology.
- **Curation state matters.** Only 53 of the 318 georeferenced Sharkbook records are `approved`.
  The rest are mostly uncurated rather than wrong, so they are retained and curation state is
  used as a sensitivity analysis instead of a hard filter. The December peak survives the strict
  filter.

## Honest limits

This is a ten-week student project. The realistic outcome is a credible prototype, an honest
evaluation against a seasonal-climatology baseline, and a well-specified data request — not a
deployed system and not a demonstrated conservation outcome.

The baseline deserves emphasis: Rohner et al. (2020) already established seasonal
predictability, so *month-of-year* is a strong predictor on its own. If the model does not beat
it, the project has produced nothing operationally new, and the report will say so.

**Conflict of interest:** the author's family operates a small tourism business on Mafia Island.
This is disclosed in the data request to MMF and is stated here for the same reason.

## References

Rohner et al. (2020) *Frontiers in Marine Science* 7:423 · Cagua et al. (2015) *Biology Letters*,
Dryad `10.5061/dryad.g6c5q` · Watts et al. (2022) · Whitehead et al. (2021) ·
Holmberg J, Arzoumanian Z, Pierce S. *Sharkbook: Wildbook for Sharks*, v2025, www.sharkbook.ai
