# PotentialBank v1 manifest — 2026-08-11

Frozen, auditable merge of **all certified donors through Stage T-cleanup**. Offline synthesis; read-only (reads
the per-stage certification manifests only); **no AiiDA writes, no new certification, no compute.**

## Headline count (reconciled)
- **238 certified donor *nodes*** across all stages (161 E1 + 77 expansion).
- **237 unique-sha donors** in v1 — **1 duplicate-sha exclusion**: the E1 Bi2X4 potentials **pk 24009 and 24011
  are byte-identical** (sha `0fe18594…`), so the historical "161 E1" contains 1 internal byte-duplicate →
  **160 unique E1 donors**. This is the only duplicate excluded (exactly the "intentionally recorded
  duplicate-sha exclusion" to verify). Every other row is a distinct potential.
- Manifest: `workspace/synthesis_v1/potentialbank_v1_manifest.csv` (sha256 `4186813d…`), summary
  `potentialbank_v1_summary.json`.

## Per-source (certified, unique)
| stage | donors | what |
|---|---|---|
| E1 | 160 | NbSe2/Bi historical families (161 rows − 1 byte-dup) |
| F1c | 9 | simple metals Nb/Al/Cu/Ag/Mo |
| F1h/F1k/F1lm | 1/3/1 | heavy-SOC Au / W,Pt,Sb / Pb (1st chains) |
| F1p | 8 | heavy-SOC 2nd chains + magnetic Fe/Ni/Co (1st) |
| F1q | 3 | magnetic Fe/Ni/Co (2nd chains) |
| F2d | 36 | metals/heavy-SOC/magnetic 3rd chains (Branch A) |
| G | 4 | covalent empty-sphere Si/Ge |
| I | 6 | ordered intermetallics CuZn/Ni3Al/FeAl |
| R | 2 | metallic layered chalcogenide TiSe2 |
| J | 1 | ionic rocksalt MgO (1st) |
| T | 3 | MgO (2nd) + NaCl (1st,2nd) |
| **total** | **237** | (+1 dup node = 238 nodes) |

## By family (unique donors)
NbSe2/Bi (E1) 160 · simple metals 24 · heavy-SOC 24 · magnetic 13 · ordered intermetallic 6 · covalent
empty-sphere (Si/Ge) 4 · metallic layered chalcogenide (TiSe2) 2 · ionic rocksalt (MgO/NaCl) 4.
**35 distinct materials, 42 compatibility classes, 33 F2-eligible materials.**

## Per-donor fields (in the manifest CSV)
`source_stage, family, material, formula, seg_pk, wc_pk, uuid, sha256, z_sequence, natyp, nspin, soc, lmax,
compat_class, empty_sphere, cpa(=False), bdg(=False), final_rms, integrity_ok, roundtrip_ok, f2_eligible`.
All rows are **CERTIFIED** (E1 verbatim at their stage: parse + byte-exact round-trip + exact Z-sequence +
NATYP match + non-CPA + non-BdG + parsed NSPIN/SOC/LMAX/mesh + no guessed mapping + 3-way sha). CPA and BdG are
**excluded by construction** (never certified). `f2_eligible` = the material has ≥2 unique-sha certified donors.

## Integrity
No duplicate donor rows remain except the single recorded E1 Bi2X4 byte-duplicate (collapsed). Empty-sphere
donors: Si/Ge only (explicit, certified X/Z=0 mapping). All other families are no-empty-sphere. This manifest is
the v1 freeze; downstream coverage/warm-start/advisor artifacts derive from it.
