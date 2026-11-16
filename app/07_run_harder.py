"""Step 3c: run the harder documents (synthetic 'hard' + 'real' groups) through all three analyzers, recording wall time.
Output goes to out/ with the same names as the easy set (cu-<stem>.json, cup-<stem>.json, di-<stem>.json) plus an '_elapsed_s' key."""
import json, sys, time
from pathlib import Path
import cu
from lib import OUT, truth, source_path, group_of

if __name__ == "__main__":
    only = sys.argv[1:]                     # optional: file names to run
    for name in sorted(truth()):
        if group_of(name) == "easy" or (only and name not in only): continue
        path = source_path(name); stem = path.stem
        for tag, fn in (("cu", lambda: cu.cu_analyze_file("invoiceFields", path)),
                        ("cup", lambda: cu.cu_analyze_file("prebuilt-invoice", path)),
                        ("di", lambda: cu.di_analyze_file("prebuilt-invoice", path))):
            t0 = time.perf_counter()
            try:
                res = fn(); res["_elapsed_s"] = round(time.perf_counter() - t0, 2)
                (OUT / f"{tag}-{stem}.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
                print(f"{name:34s} {tag:3s} ok   {res['_elapsed_s']:6.1f}s", flush=True)
            except Exception as e:
                print(f"{name:34s} {tag:3s} FAIL {str(e)[:300]}", flush=True)
