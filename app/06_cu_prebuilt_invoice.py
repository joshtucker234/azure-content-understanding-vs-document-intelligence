"""Step 3b: Content Understanding's OWN prebuilt invoice analyzer, for a like-for-like comparison with DI prebuilt-invoice."""
import json
from pathlib import Path
import cu

OUT = Path("out"); OUT.mkdir(exist_ok=True)

if __name__ == "__main__":
    for pdf in sorted(Path("samples").glob("invoice-*.pdf")):
        res = cu.cu_analyze_file("prebuilt-invoice", pdf)
        (OUT / f"cup-{pdf.stem}.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
        c = res["result"]["contents"][0]
        print(f"\n== {pdf.name}  fields: {len(c.get('fields', {}))}  usage: {res.get('usage')}")
        for k, v in c.get("fields", {}).items():
            val = next((v[x] for x in v if x.startswith("value")), None)
            if isinstance(val, list): val = f"[{len(val)} items]"
            if isinstance(val, dict): val = json.dumps(val)[:90]
            print(f"  {k}: {val}  (conf {v.get('confidence')})")
