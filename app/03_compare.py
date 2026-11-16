"""Step 3 (+ stretch): compare the three analyzers against ground truth.
Usage: python 03_compare.py [confidence_threshold] [easy|harder|all]   (default 0.80 easy)
Writes COMPARE.md (easy), COMPARE_HARDER.md or COMPARE_ALL.md, and out/review-queue-<group>.json."""
import json, sys
from pathlib import Path
from lib import OUT, SCALAR, cu_norm, cup_norm, di_norm, match, score_lines, truth, group_of

THRESH = float(sys.argv[1]) if len(sys.argv) > 1 else 0.80
GROUP = sys.argv[2] if len(sys.argv) > 2 else "easy"
TRUTH = truth()
FILES = [f for f in sorted(TRUTH) if GROUP == "all" or (GROUP == "easy" and group_of(f) == "easy") or (GROUP == "harder" and group_of(f) != "easy")]
TOOLS = [("CU", cu_norm), ("CUP", cup_norm), ("DI", di_norm)]
NAMES = {"CU": "Content Understanding custom analyzer `invoiceFields`", "CUP": "Content Understanding `prebuilt-invoice`", "DI": "Document Intelligence `prebuilt-invoice`"}


def shown(v):
    return "absent" if v is None else v


tally = {t: dict(hit=0, tot=0, lh=0, lt=0, extra=0, secs=[]) for t, _ in TOOLS}
rows, review = [], []
for f in FILES:
    stem = Path(f).stem
    for tool, norm in TOOLS:
        raw = json.loads((OUT / f"{tool.lower()}-{stem}.json").read_text(encoding="utf-8"))
        vals, conf, items, nfields = norm(raw)
        miss = []; ok_n = 0
        for k in SCALAR:
            ok = match(k, vals.get(k), TRUTH[f][k]); ok_n += ok
            if not ok: miss.append(f"{k}: got {shown(vals.get(k))!r}, want {shown(TRUTH[f][k])!r}")
            c = conf.get(k)
            if c is not None and c < THRESH: review.append(dict(tool=tool, file=f, field=k, value=vals.get(k), confidence=c, correct=ok))
        lh, lt, lx = score_lines(items, TRUTH[f]); secs = raw.get("_elapsed_s")
        t = tally[tool]; t["hit"] += ok_n; t["tot"] += len(SCALAR); t["lh"] += lh; t["lt"] += lt; t["extra"] += lx
        if secs is not None: t["secs"].append(secs)
        rows.append((f, tool, ok_n, len(SCALAR), lh, lt, lx, nfields, secs, miss))


def pct(a, b):
    return f"{100 * a / b:.0f}%" if b else "-"


title = {"easy": "easy synthetic invoices", "harder": "harder documents (synthetic hard + real)", "all": "all documents"}[GROUP]
md = [f"# Content Understanding vs Document Intelligence: {title}", "",
      f"{len(FILES)} documents, three analyzers, scored against known values. A field expected to be absent counts correct only if the tool leaves it empty. "
      "'Extra' lines are amounts a tool returned that are not on the document.", "",
      "| Analyzer | Header fields correct | Line amounts found | Extra (invented) lines | Median seconds |", "|---|---|---|---|---|"]
for t, _ in TOOLS:
    x = tally[t]; secs = sorted(x["secs"]); med = f"{secs[len(secs) // 2]:.1f}" if secs else "-"
    md.append(f"| {NAMES[t]} | {x['hit']}/{x['tot']} ({pct(x['hit'], x['tot'])}) | {x['lh']}/{x['lt']} ({pct(x['lh'], x['lt'])}) | {x['extra']} | {med} |")
md += ["", "## Per file", "", "| File | Analyzer | Header | Lines found | Extra | Seconds | Misses |", "|---|---|---|---|---|---|---|"]
for f, tool, h, ht, lh, lt, lx, nf, secs, miss in rows:
    md.append(f"| {f} | {tool} | {h}/{ht} | {lh}/{lt} | {lx} | {secs if secs is not None else '-'} | {'; '.join(miss).replace(chr(10), ' / ') or '-'} |")
md += ["", f"## Human review queue: fields with confidence < {THRESH}", "", "| Analyzer | File | Field | Value | Confidence | Actually correct? |", "|---|---|---|---|---|---|"]
for r in sorted(review, key=lambda r: r["confidence"]):
    md.append(f"| {r['tool']} | {r['file']} | {r['field']} | {str(r['value']).replace(chr(10), ' / ')} | {r['confidence']:.2f} | {'yes' if r['correct'] else 'NO'} |")
if not review: md.append("| - | - | - | - | - | - |")
out_name = {"easy": "COMPARE.md", "harder": "COMPARE_HARDER.md", "all": "COMPARE_ALL.md"}[GROUP]
Path(out_name).write_text("\n".join(md) + "\n", encoding="utf-8"); (OUT / f"review-queue-{GROUP}.json").write_text(json.dumps(review, indent=2), encoding="utf-8")
print(f"wrote {out_name}\n"); print("\n".join(md[:9]))
print("\nMISSES"); print("\n".join(f"{f:30s} {tool:3s} lines {lh}/{lt} extra {lx} | " + ("; ".join(m).replace(chr(10), ' / ') or "-") for f, tool, h, ht, lh, lt, lx, nf, s, m in rows if m or lh < lt or lx))
