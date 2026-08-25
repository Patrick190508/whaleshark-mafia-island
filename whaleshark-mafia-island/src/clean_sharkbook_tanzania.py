#!/usr/bin/env python3
"""
Clean the Sharkbook Tanzania encounter export into an analysis-ready dataset.

Input : encounterSearchResults_export_WATONET*.csv   (Sharkbook / Wildbook export)
Output: mafia_whaleshark_clean.csv  + cleaning_report.txt

Every correction is traceable through the `coord_flag` column. Nothing is silently
dropped: out-of-area and unfixable records are kept and flagged, so the counts in the
report can be audited.

Patrick Silingardi — Veritas AI Fellowship — 25 August 2026
"""
import sys, re
import numpy as np
import pandas as pd

IN  = sys.argv[1] if len(sys.argv) > 1 else "encounterSearchResults_export_WATONET.csv"
OUT = sys.argv[2] if len(sys.argv) > 2 else "mafia_whaleshark_clean.csv"
REP = "cleaning_report.txt"

# Study area. Deliberately generous: the point is to catch records that are in the
# wrong ocean, not to trim the edges of a real aggregation.
BBOX = dict(lat_min=-8.4, lat_max=-7.4, lon_min=39.1, lon_max=40.1)

# Plausible coastal-Tanzania bands, used only to repair impossible values
LAT_BAND = (4.0, 12.0)     # absolute value
LON_BAND = (38.0, 42.0)

R = []
def rep(msg=""):
    print(msg)
    R.append(msg)

df = pd.read_csv(IN, low_memory=False)
rep("=" * 70)
rep("SHARKBOOK TANZANIA — CLEANING REPORT")
rep("=" * 70)
rep(f"input file : {IN}")
rep(f"raw shape  : {df.shape[0]} rows x {df.shape[1]} columns")
rep(f"empty cols : {int((df.notna().sum() == 0).sum())} of {df.shape[1]}")
rep("")

out = pd.DataFrame(index=df.index)

# ---------------------------------------------------------------- identifiers
out["encounter_id"] = df["Encounter.catalogNumber"]
out["occurrence_id"] = df.get("Occurrence.occurrenceID")
# Name0.value holds the ECOCEAN individual code (TZ-xxx); later Name slots are aliases
out["individual_id"] = df.get("Name0.value")
out["individual_alt"] = df.get("Name1.value")

# ---------------------------------------------------------------------- date
y = pd.to_numeric(df["Encounter.year"], errors="coerce")
m = pd.to_numeric(df["Encounter.month"], errors="coerce")
d = pd.to_numeric(df["Encounter.day"], errors="coerce")
valid_ymd = y.between(1990, 2030) & m.between(1, 12) & d.between(1, 31)

out["date"] = pd.to_datetime(
    dict(year=y.where(valid_ymd, 2000), month=m.where(valid_ymd, 1), day=d.where(valid_ymd, 1)),
    errors="coerce",
).where(valid_ymd)

# fall back to the epoch-millis field where the y/m/d triplet is unusable
ms = pd.to_numeric(df.get("Encounter.dateInMilliseconds"), errors="coerce")
fallback = out["date"].isna() & ms.notna()
if fallback.any():
    out.loc[fallback, "date"] = pd.to_datetime(ms[fallback], unit="ms", errors="coerce")
rep(f"dates: {int(out['date'].notna().sum())} usable, "
    f"{int(out['date'].isna().sum())} unusable "
    f"({int(fallback.sum())} recovered from dateInMilliseconds)")

hour = pd.to_numeric(df["Encounter.hour"], errors="coerce")
out["hour"] = hour.where(hour.between(0, 23))          # -1 is Wildbook's "unknown"
out["minute"] = pd.to_numeric(df.get("Encounter.minutes"), errors="coerce")
rep(f"time of day: {int(out['hour'].notna().sum())} of {len(df)} records "
    f"({out['hour'].notna().mean():.0%}) — the rest carry hour = -1")
rep("")

# --------------------------------------------------------------- coordinates
lat_raw = pd.to_numeric(df["Encounter.decimalLatitude"], errors="coerce")
lon_raw = pd.to_numeric(df["Encounter.decimalLongitude"], errors="coerce")

def fix_scale(v, band):
    """Repair decimal-point/scale errors. Only touches physically impossible values."""
    if pd.isna(v):
        return v, False
    if abs(v) <= 90 if band is LAT_BAND else abs(v) <= 180:
        return v, False
    x, guard = float(v), 0
    while abs(x) > band[1] and guard < 12:
        x /= 10.0
        guard += 1
    return x, True

lat, lat_scaled = zip(*[fix_scale(v, LAT_BAND) for v in lat_raw])
lon, lon_scaled = zip(*[fix_scale(v, LON_BAND) for v in lon_raw])
lat = pd.Series(lat, index=df.index)
lon = pd.Series(lon, index=df.index)
scaled = pd.Series(lat_scaled, index=df.index) | pd.Series(lon_scaled, index=df.index)

# Mafia Island is in the southern hemisphere. A positive latitude in the mirrored
# band is a sign error, not a location in Ethiopia.
sign_fix = lat.notna() & (lat > 0) & lat.between(*LAT_BAND)
lat = lat.where(~sign_fix, -lat)

out["lat"] = lat
out["lon"] = lon

has_coords = lat.notna() & lon.notna()
in_area = has_coords & lat.between(BBOX["lat_min"], BBOX["lat_max"]) \
                     & lon.between(BBOX["lon_min"], BBOX["lon_max"])

flag = pd.Series("no_coords", index=df.index, dtype=object)
flag[has_coords] = "ok"
flag[scaled & has_coords] = "scale_corrected"
flag[sign_fix] = "sign_corrected"
flag[scaled & sign_fix] = "scale_and_sign_corrected"
flag[has_coords & ~in_area] = "out_of_area"
out["coord_flag"] = flag
out["in_study_area"] = in_area

rep("COORDINATES")
rep(f"  records with a latitude value  : {int(lat_raw.notna().sum())}")
rep(f"  records with a longitude value : {int(lon_raw.notna().sum())}")
rep(f"  records with BOTH              : {int(has_coords.sum())}")
lat_only = lat_raw.notna() & lon_raw.isna()
if int(lat_only.sum()):
    rep(f"  latitude but NO longitude      : {int(lat_only.sum())}  (unusable; raw values "
        f"{sorted(set(lat_raw[lat_only].round(3).tolist()))})")
rep(f"  scale errors repaired          : {int((scaled & has_coords).sum())}  "
    f"(e.g. -7876250.0 -> -7.87625)")
rep(f"  sign errors repaired           : {int(sign_fix.sum())}  "
    f"(positive latitude -> southern hemisphere)")
rep(f"  outside the study area         : {int((has_coords & ~in_area).sum())}  "
    f"(kept, flagged out_of_area)")
rep(f"  >> GEOREFERENCED AND USABLE    : {int(in_area.sum())}")
if int((has_coords & ~in_area).sum()):
    rep("  out-of-area coordinates:")
    for _, r in out.loc[has_coords & ~in_area, ["lat", "lon"]].iterrows():
        rep(f"    {r['lat']:>12.5f}, {r['lon']:>12.5f}")
rep("")

# ------------------------------------------------------------------- locality
loc = df["Encounter.verbatimLocality"].fillna("").astype(str).str.strip()
def norm_loc(s):
    if not isinstance(s, str):
        return "Tanzania (unspecified)"
    t = s.lower().replace(",", " ").replace("-", " ")
    t = re.sub(r"\s+", " ", t).strip()
    if "kilindoni" in t or "kilinoni" in t or "kilindini" in t:
        return "Kilindoni Bay, Mafia Island"
    if "mafia" in t or "mafla" in t or "mafia islans" in t:
        return "Mafia Island"
    if t in ("tanzania", "nan", ""):
        return "Tanzania (unspecified)"
    return s
out["locality"] = loc.map(norm_loc)
rep(f"locality strings: {loc.nunique()} raw spellings -> {out['locality'].nunique()} normalised")
rep("")

# ------------------------------------------------------- measurements & sex
def parse_measure(s):
    if not isinstance(s, str):
        return np.nan
    mm = re.search(r"value:\s*([0-9.]+)", s)
    return float(mm.group(1)) if mm else np.nan

out["length_m"] = df.get("Encounter.measurement.length", pd.Series(dtype=object)).map(parse_measure)
out["sst_insitu_c"] = df.get("Encounter.measurement.temperature", pd.Series(dtype=object)).map(parse_measure)
out["depth_m"] = pd.to_numeric(df.get("Encounter.depth"), errors="coerce")

sex = df["Encounter.sex"].astype(str).str.strip().str.lower()
out["sex"] = sex.map({"male": "M", "female": "F"}).fillna("unknown")

beh = df.get("Encounter.behavior", pd.Series(dtype=object)).astype(str).str.lower()
out["behavior_raw"] = df.get("Encounter.behavior")
out["feeding"] = beh.str.contains("feed", na=False)

rep("MEASUREMENTS")
rep(f"  length recorded   : {int(out['length_m'].notna().sum())} "
    f"(mean {out['length_m'].mean():.2f} m, range {out['length_m'].min():.1f}-{out['length_m'].max():.1f})")
rep(f"  in-situ SST       : {int(out['sst_insitu_c'].notna().sum())} records only")
rep(f"  depth             : {int(out['depth_m'].notna().sum())} records")
rep(f"  behaviour         : {int(out['behavior_raw'].notna().sum())} records, "
    f"{int(out['feeding'].sum())} indicating feeding")
rep(f"  sex               : {(out['sex']=='M').sum()} M / {(out['sex']=='F').sum()} F / "
    f"{(out['sex']=='unknown').sum()} unknown")
rep("")

# ----------------------------------------------------------------- provenance
org = df.get("Encounter.submitterOrganization", pd.Series(dtype=object)).fillna("").astype(str).str.strip()
def norm_org(s):
    if not isinstance(s, str):
        return None
    t = s.lower()
    if "megafauna" in t or t == "mmf":
        return "MMF"
    if "kitu kiblu" in t:
        return "Kitu Kiblu"
    if t in ("nan", ""):
        return None
    return s
out["organisation"] = org.map(norm_org)
out["recorded_by"] = df.get("Encounter.recordedBy")     # attribution only — strip before sharing
out["submitter"] = df.get("Encounter.submitterID")

rep("DATA PROVIDERS (this is the consent list)")
vc = out["organisation"].value_counts()
for k, v in vc.items():
    rep(f"  {str(k):<32} {v:>5}")
rep(f"  {'(no organisation stated)':<32} {int(out['organisation'].isna().sum()):>5}")
rep("")

# ------------------------------------------------- effort fields: check, don't assume
effort_cols = ["Occurrence.effortCode", "Occurrence.transectName", "Occurrence.distance",
               "Occurrence.observer", "Occurrence.seaState", "Occurrence.seaSurfaceTemp",
               "Occurrence.visibilityIndex", "Occurrence.bestGroupSizeEstimate"]
rep("SEARCH-EFFORT AND SURVEY FIELDS")
for c in effort_cols:
    n = int(df[c].notna().sum()) if c in df.columns else -1
    status = "ABSENT from export" if n < 0 else (f"{n} values" if n else "EMPTY")
    rep(f"  {c:<38} {status}")
rep("  -> no effort field is populated: these are presence-only records.")
rep("     Absence has to come from Cagua et al. 2015 (searchinghours.csv) or from")
rep("     background sampling. This is the single most important limitation.")
rep("")

# ------------------------------------------------------------------- features
out["year"] = out["date"].dt.year
out["month"] = out["date"].dt.month
out["day_of_year"] = out["date"].dt.dayofyear
out["doy_sin"] = np.sin(2 * np.pi * out["day_of_year"] / 365.25)
out["doy_cos"] = np.cos(2 * np.pi * out["day_of_year"] / 365.25)

SYNODIC = 29.530588853
REF = pd.Timestamp("2000-01-06 18:14")
out["moon_phase"] = ((out["date"] - REF).dt.total_seconds() / 86400.0 % SYNODIC) / SYNODIC

# 0.01 deg grid cell (~1.1 km) — the finest defensible resolution for this data
out["cell_lat"] = (out["lat"] / 0.01).round() * 0.01
out["cell_lon"] = (out["lon"] / 0.01).round() * 0.01
out["cell_id"] = out["cell_lat"].round(2).astype(str) + "_" + out["cell_lon"].round(2).astype(str)
out.loc[~out["in_study_area"], ["cell_lat", "cell_lon", "cell_id"]] = np.nan

# ----------------------------------------------------------------- diagnostics
geo = out[out["in_study_area"]]
rep("COVERAGE")
rep(f"  date range (all records)   : {out['date'].min()} -> {out['date'].max()}")
rep(f"  distinct days with sightings: {out['date'].nunique()}")
rep(f"  distinct individuals        : {out['individual_id'].nunique()}")
rep(f"  individuals with 5+ records : "
    f"{int((out['individual_id'].value_counts() >= 5).sum())}")
rep(f"  georeferenced records       : {len(geo)}")
rep(f"  distinct georeferenced days : {geo['date'].nunique()}")
rep(f"  distinct 0.01 deg cells     : {geo['cell_id'].nunique()}")
rep("")

rep("SEASONALITY (georeferenced records by month)")
mc = geo["month"].value_counts().sort_values(ascending=False)
for mo, n in mc.items():
    if pd.notna(mo):
        rep(f"  month {int(mo):>2}: {n:>4}  {'#' * int(n / 3)}")
rep("")

rep("RECORDS PER YEAR (georeferenced) — this is survey effort, not abundance")
yc = geo["year"].value_counts().sort_index()
for yr, n in yc.items():
    if pd.notna(yr):
        rep(f"  {int(yr)}: {n:>4}")
rep("")

# --------------------------------------------------------------------- export
cols = ["encounter_id", "occurrence_id", "individual_id", "individual_alt",
        "date", "year", "month", "day_of_year", "doy_sin", "doy_cos", "moon_phase",
        "hour", "minute", "lat", "lon", "coord_flag", "in_study_area",
        "cell_lat", "cell_lon", "cell_id", "locality",
        "length_m", "sex", "depth_m", "sst_insitu_c", "behavior_raw", "feeding",
        "organisation", "recorded_by", "submitter"]
out[cols].to_csv(OUT, index=False)

rep("=" * 70)
rep(f"WRITTEN: {OUT}  ({len(out)} rows x {len(cols)} columns)")
rep(f"         {REP}")
rep("")
rep("BEFORE SHARING THIS FILE ANYWHERE:")
rep("  - drop `recorded_by` and `submitter` (real people's names)")
rep("  - never commit it to a public repository")
rep("  - use in any publication or product requires the written consent of the data")
rep("    providers listed above; MMF is the largest single one")
rep("=" * 70)

with open(REP, "w") as f:
    f.write("\n".join(R))
