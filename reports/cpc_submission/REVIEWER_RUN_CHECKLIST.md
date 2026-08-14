# Reviewer-run package checklist

How a referee can exercise the software **without HPC, an AiiDA daemon, or the author's database**. All steps
below are read-only / offline.

## 1. Install from source
```bash
git clone https://github.com/MRHemmati/kkr_ml_tools.git
cd kkr_ml_tools
python -m venv .venv && source .venv/bin/activate
pip install -e .                 # numpy-only runtime core
# optional extras:  pip install -e ".[dev]"   # scikit-learn + pytest (for golden-parity tests)
#                   pip install -e ".[aiida]"  # aiida-core + aiida-kkr (only needed to SUBMIT)
```
The pure-`numpy` core (`aiida_kkr_mlassist` inference, `kkr_convergence_advisor`) imports **without** AiiDA or
scikit-learn.

## 2. Load the advisor / PotentialBank index (no AiiDA)
```python
import kkr_convergence_advisor as adv
idx = adv.load_index()                       # packaged advisor_index_v1.json
print(idx["unique_sha_donors"], idx["n_families"])   # -> 237 8
tips = adv.load_index("advisor_example_tips_v1.json") # -> 8 example tips
```

## 3. Run tests that do NOT require HPC/AiiDA
The runtime tests are self-asserting scripts (the daemon env has no `pytest`):
```bash
for t in tests/test_advisor.py tests/test_per_stratum_advisory.py tests/test_bdg_dual.py \
         tests/test_bdg_parser.py tests/test_cumulative_trajectory.py \
         tests/test_wrapper_pipeline.py tests/test_package_smoke.py ; do
  echo "== $t =="; PYTHONPATH=src python "$t" ; done
# with pytest installed you may instead run:  PYTHONPATH=src pytest tests/ -q
```
Expected: `test_advisor.py` prints `11/11 passed`; the others print a `... PASS` line. (`test_mondrian.py` may
hang while importing the *installed* AiiDA package in some environments — run it only with the `[aiida]` extra,
or skip; it is not required for the offline review.)

## 4. Open / run the walkthrough notebooks
```bash
pip install pandas matplotlib jupyter
# AiiDA-free tour of the frozen PotentialBank v1 artifact:
jupyter nbconvert --to notebook --execute --inplace notebooks/potentialbank_v1_walkthrough.ipynb
# submission tutorial (safe-by-default; forces offline mode so nothing submits):
POTBANK_NB_NO_AIIDA=1 jupyter nbconvert --to notebook --execute --inplace \
    notebooks/aiida_kkr_mlassist_submission_walkthrough.ipynb
```
Both execute to exit 0 with zero error cells; the submission notebook submits **nothing** (dry-run gates
default off).

## 5. Lightweight smoke test — exact expected outputs
```bash
PYTHONPATH=src python -c "import kkr_convergence_advisor as a; d=a.load_index(); \
print(d['unique_sha_donors'], d['certified_donor_nodes'], d['n_families'], \
sum(1 for m in d['materials'] if m['f2_eligible']))"
# expected:  237 238 8 33
```
Optional integrity check of the synthesis bundle:
```bash
cd reports/potentialbank_v1 && sha256sum -c MANIFEST.sha256   # expected: all files OK (22/22)
```

## 6. What CANNOT be reproduced offline
- **Live KKR submissions / warm starts** — require the author's AiiDA database, the JuKKR codes, and iffslurm
  (cluster) access. The manuscript's iteration counts come from those runs; reviewers can inspect the resulting
  manifests/benchmarks but not re-run them without the same environment.
- **Re-deriving the frozen models** from raw trajectories requires the training data (not shipped).

## 7. How raw potentials are represented
Raw KKR potential bytes are **not** in git. Each certified donor row in
`reports/potentialbank_v1/potentialbank_v1_manifest.csv` carries the potential's **SHA-256** plus AiiDA
provenance handles (`seg_pk`, `wc_pk`, `uuid`). The potentials themselves live in the author's AiiDA repository;
the SHA-256 lets anyone with that repository verify byte-exact identity.
