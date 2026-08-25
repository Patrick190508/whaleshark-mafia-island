# Data

**This directory is intentionally empty in version control.** `.gitignore` blocks data by
default and allow-lists safe files back in.

## Why

1. **Consent.** The Wildbook citation agreement requires the prior written consent of the
   original data provider before Sharkbook records are used in any publication or product. For
   Mafia Island the largest provider is the Marine Megafauna Foundation (~30% of records). That
   request is in progress through WATONET.
2. **Personal data.** The raw exports carry contributor names and email addresses. Some
   contributors are EU citizens, so GDPR applies. `recorded_by` is retained in local working
   files for attribution and must be stripped before any external sharing.

Git history is permanent. A data file committed once and deleted later remains in the history
and remains clonable, so nothing is committed in the first place.

## How to obtain each source

| Source | Access | Notes |
|---|---|---|
| **OBIS + GBIF (global)** | Open, no registration | Run `notebooks/WhaleShark_Dataset_Starter.ipynb`; it pulls from the APIs and writes `whaleshark_global_clean.csv` |
| **Cagua et al. (2015)** | Open — https://datadryad.org/dataset/doi:10.5061/dryad.g6c5q | 7 files, ~116 KB. `searchinghours.csv` carries the search effort, which is what makes presence/absence defensible |
| **Sharkbook Tanzania** | Researcher account required; no self-registration | Encounter Search → Export. Use is gated on data-provider consent |
| **MMF Tanzania archive** | Requested via WATONET | ~2,600 encounters / 450 trips, 2012–2025. Not yet granted |

## Expected local layout

```
data/
  mafia_whaleshark_clean.csv        output of src/clean_sharkbook_tanzania.py
  encounter_curation_state.csv      encounter_id -> approved / unapproved / unidentifiable
  whaleshark_global_clean.csv       output of the notebook
  cagua2015/                        the unzipped Dryad deposit
```

## Pinning a reference export

The Sharkbook database changes between exports — two extractions days apart differed by three
records. Fix one export with a date in the filename and work only on that, rather than mixing
extractions taken at different times.
