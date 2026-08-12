"""Package the PotentialBank v1 synthesis + advisor assets into a versioned, checksummed bundle.
Offline; no compute/AiiDA/commit/install. Writes VERSION, INDEX.md, MANIFEST.sha256 into the tracked bundle
and a distribution tarball (build artifact) under ../../../../workspace/dist/."""
import os, hashlib, json, tarfile, subprocess, datetime
REPO=os.path.abspath(os.path.join(os.path.dirname(__file__),"..",".."))   # git/kkr_ml_tools
BUNDLE=os.path.join(REPO,"reports","potentialbank_v1")
DIST=os.path.abspath(os.path.join(REPO,"..","..","workspace","dist")); os.makedirs(DIST,exist_ok=True)
def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda:f.read(65536),b""): h.update(c)
    return h.hexdigest()
# file set (repo-relative): the v1 bundle + advisor assets + the root doc
FILES=[]
for root,_,fs in os.walk(BUNDLE):
    for fn in sorted(fs):
        if fn in ("MANIFEST.sha256","VERSION","INDEX.md","build_bundle.py"): continue
        FILES.append(os.path.join(root,fn))
FILES.append(os.path.join(REPO,"src","kkr_convergence_advisor","data","advisor_index_v1.json"))
FILES.append(os.path.join(REPO,"src","kkr_convergence_advisor","data","advisor_example_tips_v1.json"))
FILES.append(os.path.join(REPO,"src","kkr_convergence_advisor","README.md"))
FILES.append(os.path.join(REPO,"POTENTIALBANK_V1.md"))
FILES=sorted(set(FILES))
# VERSION
summary=json.load(open(os.path.join(BUNDLE,"potentialbank_v1_summary.json")))
try: commit=subprocess.check_output(["git","-C",REPO,"rev-parse","--short","HEAD"],text=True).strip()
except Exception: commit="(uncommitted)"
ver=dict(name="kkr_potentialbank_v1_synthesis",version="1.0",frozen="2026-08-11",packaged=datetime.date.today().isoformat(),
         git_commit=commit,certified_donor_nodes=summary["certified_donor_nodes"],unique_sha_donors=summary["unique_sha_donors"],
         families=len(summary["by_family"]),f2_eligible_materials=summary["f2_eligible_material_count"],
         manifest_sha256=summary["manifest_sha256"],note="Same-structure warm-start reuse only; NOT cross-material transfer; CPA/BdG out of scope.")
json.dump(ver,open(os.path.join(BUNDLE,"VERSION"),"w"),indent=2)
# MANIFEST.sha256
man=[]
for p in FILES:
    rel=os.path.relpath(p,REPO); man.append((sha(p),rel))
with open(os.path.join(BUNDLE,"MANIFEST.sha256"),"w") as f:
    for s,rel in man: f.write(f"{s}  {rel}\n")
# INDEX.md
DESC={"potentialbank_v1_manifest.csv":"237 unique certified donors (238 nodes), all E1 fields",
 "potentialbank_v1_summary.json":"counts + dup reconciliation + F2 roster",
 "advisor_index_v1.json":"advisor index (materials, donors, warm-start, parked warnings)",
 "advisor_example_tips_v1.json":"8 worked advisory tips","README.md":"advisor offline usage note",
 "POTENTIALBANK_V1.md":"the v1 document (scope/certification/coverage/limits)"}
with open(os.path.join(BUNDLE,"INDEX.md"),"w") as f:
    f.write("# PotentialBank v1 synthesis bundle — INDEX\n\n")
    f.write(f"Version 1.0 (frozen 2026-08-11) · {ver['unique_sha_donors']} unique donors / {ver['certified_donor_nodes']} nodes · "
            f"{ver['families']} families · {ver['f2_eligible_materials']} F2-eligible. Checksums in MANIFEST.sha256.\n\n")
    f.write("## Contents\n")
    for s,rel in man:
        base=os.path.basename(rel); d=DESC.get(base,"")
        f.write(f"- `{rel}` — {d} (`{s[:12]}…`)\n")
    f.write("\n**Scope:** same-structure warm-start reuse only; no cross-material transfer; no guaranteed "
            "acceleration; CPA/BdG out of scope. See PAPER_CLAIM_LADDER_AFTER_POTBANK_V1.md.\n")
# tarball (build artifact, not tracked)
tarpath=os.path.join(DIST,"kkr_potentialbank_v1_synthesis.tar.gz")
with tarfile.open(tarpath,"w:gz") as tar:
    for p in FILES+[os.path.join(BUNDLE,x) for x in ("VERSION","INDEX.md","MANIFEST.sha256")]:
        tar.add(p,arcname=os.path.join("kkr_potentialbank_v1_synthesis",os.path.relpath(p,REPO)))
tarsha=sha(tarpath); open(tarpath+".sha256","w").write(f"{tarsha}  {os.path.basename(tarpath)}\n")
print(f"bundle files: {len(FILES)} | VERSION+INDEX+MANIFEST written to {os.path.relpath(BUNDLE,REPO)}/")
print(f"tarball: {tarpath} ({os.path.getsize(tarpath)} bytes) sha256 {tarsha[:16]}")
print(f"donors {ver['unique_sha_donors']} unique / {ver['certified_donor_nodes']} nodes · {ver['families']} families · {ver['f2_eligible_materials']} F2-eligible · git {commit}")
