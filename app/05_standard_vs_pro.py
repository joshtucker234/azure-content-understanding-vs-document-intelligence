"""Step 5: standard vs pro mode. Pro mode only existed in the PREVIEW API (2025-05-01-preview), documents only, and that API
is now retired (HTTP 410 Gone). This script (a) records that, and (b) runs the same reasoning-style generate fields in GA
standard mode, which is the closest thing you can still run."""
import json, sys
from pathlib import Path
import cu

PREVIEW = "2025-05-01-preview"
OUT = Path("out"); OUT.mkdir(exist_ok=True)
FILE = Path(sys.argv[1] if len(sys.argv) > 1 else "samples/invoice-02-scanned.pdf")

def gen(desc, typ="string"): return {"type": typ, "method": "generate", "description": desc}   # pro mode: classify/generate only

def definition(mode, api):
    d = {"description": f"Invoice analyzer, {mode} mode", "baseAnalyzerId": "prebuilt-document",
            "models": {"completion": "gpt-4.1", "embedding": "text-embedding-3-large"},
            "config": {"returnDetails": True},
            "fieldSchema": {"name": "Inv", "fields": {
                "VendorName": gen("Company that issued the invoice"), "InvoiceId": gen("Invoice number"),
                "InvoiceTotal": gen("Final total due including tax", "number"),
                "PaymentRisk": gen("One sentence: anything unusual or risky about this invoice, such as odd dates, "
                                   "totals that do not add up, or missing PO number. Say 'none' if nothing.")}}}
    if api == PREVIEW: d["mode"] = mode; d.pop("models")   # preview API had a mode switch and no per-analyzer models
    return d

if __name__ == "__main__":
    for mode, api in (("standard", cu.CU_API), ("standard", PREVIEW), ("pro", PREVIEW)):
        aid = f"invoice_{mode}_{'ga' if api == cu.CU_API else 'preview'}"
        print(f"\n== {mode} mode, {api}")
        try:
            cu.cu_put_analyzer(aid, definition(mode, api), api=api)
            res = cu.cu_analyze_file(aid, FILE, api=api)
            (OUT / f"mode-{aid}.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
            fields = res["result"]["contents"][0]["fields"]
            for k, v in fields.items():
                print(f"  {k}: {next((v[x] for x in v if x.startswith('value')), None)}  (confidence {v.get('confidence')})")
        except Exception as e:
            print("  FAILED:", str(e)[:600])
