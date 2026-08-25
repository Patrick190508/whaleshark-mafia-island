# Reports

Machine-generated audit output. These files contain **counts and diagnostics only, never
records** — that is what makes them safe to commit while `data/` is not.

- `cleaning_report.txt` — every correction applied to the Sharkbook Tanzania export: coordinate
  scale and sign repairs, out-of-area records, locality normalisation, the data-provider list
  (which is also the consent list), and confirmation that no search-effort field is populated.

Regenerate with:

```bash
python src/clean_sharkbook_tanzania.py <export>.csv data/mafia_whaleshark_clean.csv
```
