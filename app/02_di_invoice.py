"""Step 2: run the same invoices through Document Intelligence (prebuilt-invoice) on the same Foundry resource."""
import json
from pathlib import Path
import cu

OUT = Path("out"); OUT.mkdir(exist_ok=True)

if __name__ == "__main__":
    for pdf in sorted(Path("samples").glob("invoice-*.pdf")):
        res = cu.di_analyze_file("prebuilt-invoice", pdf)
        (OUT / f"di-{pdf.stem}.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
        doc = res["analyzeResult"]["documents"][0]
        print(f"\n== {pdf.name}  (doc confidence {doc.get('confidence')})")
        for k, v in doc["fields"].items():
            if k == "Items": print(f"  {k}: {len(v.get('valueArray', []))} items")
            else: print(f"  {k}: {v.get('content')!r}  (confidence {v.get('confidence')})")
