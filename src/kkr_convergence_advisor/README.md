# kkr_convergence_advisor (offline)

Retrieval-based, **advisory-only** helper that turns PotentialBank v1 into optional tips for a KKR run. It is
**not installed into the daemon** and takes **no action** on its own — a workflow or user reads the tips and
decides. Advisory-by-default; it never suggests a guessed/uncertified/CPA/BdG donor, and emits *warnings*
(never "safe" tips) for parked hard cases.

## Data
- `data/advisor_index_v1.json` — 237 unique certified donors across 8 families, per material: donor SHA-256s,
  compat class, NSPIN/SOC/LMAX, empty-sphere flag, F2-eligibility, and (where measured) warm-start
  cold/warm/saved with contour caveats; plus 9 parked-case warnings.
- `data/advisor_example_tips_v1.json` — worked example tips (MgO, NaCl, Si/Ge, TiSe₂, Fe/Ni/Co, heavy-SOC,
  WSe₂/MoS₂ warnings). Every tip carries `tip_type, material, evidence_level, n_supporting_runs, confidence,
  recommendation, reason`.

## Usage (read tips as optional advice)
```python
import json
idx = json.load(open("src/kkr_convergence_advisor/data/advisor_index_v1.json"))

def advise(material):
    m = next((x for x in idx["materials"] if x["material"] == material), None)
    if m is None:
        w = next((p for p in idx["parked_warnings"] if p["material"] == material), None)
        return f"WARNING ({w['klass']}): {w['warning']}" if w else "no advice (material not in bank)"
    if m["f2_eligible"] and m["warmstart"]:
        ws = m["warmstart"]
        return (f"donor_start (Level A): warm-start from a certified {material} donor "
                f"(startpot_overwrite); measured {ws['warm']} vs {ws['cold']} iters ({ws['pct']}). "
                f"Caveat: {ws['contour_caveat']}.")
    return f"{material}: {m['n_unique_donors']} certified donor(s); advisory only."

print(advise("MgO"))    # -> donor_start tip with measured savings
print(advise("WSe2"))   # -> parked WARNING (no donor)
```
The tip is **advice**: a stock run ignores it; an opt-in run may inject the suggested certified donor as
`startpot_overwrite`. **Same-structure reuse only** — the advisor makes no cross-material or
guaranteed-acceleration claim.
