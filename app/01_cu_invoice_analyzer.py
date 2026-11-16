"""Step 1: create a custom Content Understanding analyzer for invoices and run the samples through it."""
import json
from pathlib import Path
import cu

ANALYZER = "invoiceFields"
OUT = Path("out"); OUT.mkdir(exist_ok=True)

def f(desc, typ="string", method="extract"):
    return {"type": typ, "method": method, "description": desc}

definition = {
    "description": "Custom invoice analyzer",
    "baseAnalyzerId": "prebuilt-document",   # OCR + layout first, then fields
    "config": {"returnDetails": True, "estimateFieldSourceAndConfidence": True, "enableOcr": True, "enableLayout": True},
    "fieldSchema": {
        "name": "InvoiceFields",
        "description": "Header, totals and line items of a supplier invoice",
        "fields": {
            "VendorName": f("Name of the company that issued the invoice"),
            "CustomerName": f("Name of the company being billed"),
            "InvoiceId": f("The invoice number"),
            "InvoiceDate": f("Date the invoice was issued", "date"),
            "DueDate": f("Payment due date", "date"),
            "PurchaseOrder": f("Customer purchase order number"),
            "SubTotal": f("Total before tax", "number"),
            "TotalTax": f("Total tax amount", "number"),
            "InvoiceTotal": f("Final total due including tax", "number"),
            "Currency": f("ISO 4217 currency code such as USD or EUR", "string", "generate"),
            "LineItems": {
                "type": "array", "method": "extract", "description": "Each billed line",
                "items": {"type": "object", "properties": {
                    "Description": f("Item description"),
                    "Quantity": f("Quantity billed", "number"),
                    "UnitPrice": f("Price per unit", "number"),
                    "Amount": f("Line amount", "number"),
                }},
            },
        },
    },
    "models": {"completion": "gpt-4.1", "embedding": "text-embedding-3-large"},
}

if __name__ == "__main__":
    print("creating analyzer", ANALYZER)
    cu.cu_put_analyzer(ANALYZER, definition)
    for pdf in sorted(Path("samples").glob("invoice-*.pdf")):
        res = cu.cu_analyze_file(ANALYZER, pdf)
        (OUT / f"cu-{pdf.stem}.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
        fields = res["result"]["contents"][0].get("fields", {})
        print(f"\n== {pdf.name}")
        for k, v in fields.items():
            if k == "LineItems": print(f"  {k}: {len(v.get('valueArray', []))} items")
            else:
                val = next((v[x] for x in v if x.startswith("value")), None)
                print(f"  {k}: {val}  (confidence {v.get('confidence')})")
