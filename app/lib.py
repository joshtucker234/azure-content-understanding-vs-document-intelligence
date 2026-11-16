"""Shared loading + normalizing of the saved results (used by 03_compare.py and ui.py). No Azure calls."""
import json
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"
SAMPLES = HERE / "samples"
SCALAR = ["VendorName", "CustomerName", "InvoiceId", "InvoiceDate", "DueDate", "PurchaseOrder", "SubTotal", "TotalTax", "InvoiceTotal", "Currency"]
NUMERIC = {"SubTotal", "TotalTax", "InvoiceTotal"}


GROUPS = {"": "easy", "hard": "hard", "real": "real"}   # subfolder of samples/ -> group name


_group = {}


def truth():
    """Merged ground truth for every sample set (easy: samples/, hard: samples/hard, real: samples/real). Keys are file names.
    Also records each file's group, so a document's group never depends on its PDF being present (the real PDFs are downloaded separately)."""
    out = {}
    for sub, grp in GROUPS.items():
        p = SAMPLES / sub / "ground-truth.json"
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            out.update(d)
            _group.update({k: grp for k in d})
    return out


def source_path(name):
    """Where a sample file lives, whatever its group."""
    for sub in GROUPS:
        p = SAMPLES / sub / name
        if p.exists(): return p
    raise FileNotFoundError(name)


def group_of(name):
    if name not in _group:
        truth()
    return _group[name]


def _val(v):
    return next((v[x] for x in v if x.startswith("value")), None)


def cu_norm(res):
    """-> (scalar values, confidences, line items [{Description, Quantity, UnitPrice, Amount}], total fields returned)"""
    fields = res["result"]["contents"][0].get("fields", {}); out, conf, items = {}, {}, []
    for k in SCALAR:
        v = fields.get(k)
        if v: out[k], conf[k] = _val(v), v.get("confidence")
    for it in fields.get("LineItems", {}).get("valueArray", []):
        o = it.get("valueObject", {})
        items.append({k: _val(o[k]) if k in o else None for k in ("Description", "Quantity", "UnitPrice", "Amount")})
    return out, conf, items, len(fields)


def _di_num(a):
    if not a: return None
    return a["valueCurrency"]["amount"] if "valueCurrency" in a else a.get("valueNumber")


def di_norm(res):
    fields = res["analyzeResult"]["documents"][0]["fields"]; out, conf, items = {}, {}, []
    for k in SCALAR:
        v = fields.get(k)
        if not v: continue
        out[k] = v["valueCurrency"]["amount"] if "valueCurrency" in v else (v.get("valueString") or v.get("valueDate") or v.get("content"))
        conf[k] = v.get("confidence")
    cur = fields.get("InvoiceTotal", {}).get("valueCurrency", {}).get("currencyCode")
    if cur: out["Currency"], conf["Currency"] = cur, fields["InvoiceTotal"].get("confidence")
    for it in fields.get("Items", {}).get("valueArray", []):
        o = it.get("valueObject", {})
        items.append({"Description": o.get("Description", {}).get("valueString"), "Quantity": o.get("Quantity", {}).get("valueNumber"),
                      "UnitPrice": _di_num(o.get("UnitPrice")), "Amount": _di_num(o.get("Amount"))})
    return out, conf, items, len(fields)


def _money(f):
    """CU prebuilt money object -> (amount, currency code, confidence of the amount)"""
    o = (f or {}).get("valueObject", {}); a = o.get("Amount", {}); c = o.get("CurrencyCode", {})
    return a.get("valueNumber"), c.get("valueString"), a.get("confidence")


def cup_norm(res):
    """Content Understanding PREBUILT invoice analyzer: different names (PONumber, SubtotalAmount, TotalAmount...) and nested money objects."""
    fields = res["result"]["contents"][0].get("fields", {}); out, conf, items = {}, {}, []
    for k in ("VendorName", "CustomerName", "InvoiceId", "InvoiceDate", "DueDate"):
        v = fields.get(k)
        if v: out[k], conf[k] = _val(v), v.get("confidence")
    v = fields.get("PONumber")
    if v: out["PurchaseOrder"], conf["PurchaseOrder"] = _val(v), v.get("confidence")
    for ours, theirs in (("SubTotal", "SubtotalAmount"), ("TotalTax", "TotalTaxAmount"), ("InvoiceTotal", "TotalAmount")):
        amt, _cur, c = _money(fields.get(theirs))
        if amt is not None: out[ours], conf[ours] = amt, c
    _a, cur, _c = _money(fields.get("TotalAmount"))
    if cur: out["Currency"], conf["Currency"] = cur, None   # currency code carries no confidence of its own
    for it in fields.get("LineItems", {}).get("valueArray", []):
        o = it.get("valueObject", {})
        items.append({"Description": _val(o["Description"]) if "Description" in o else None,
                      "Quantity": _val(o["Quantity"]) if "Quantity" in o else None,
                      "UnitPrice": _money(o.get("UnitPrice"))[0], "Amount": _money(o.get("TotalAmount"))[0]})
    return out, conf, items, len(fields)


def match(k, got, want):
    """want may be None (field is absent: empty or 0 is right, a value is invented) or a list of acceptable values."""
    if want is None:
        return got in (None, "", 0, 0.0)
    if got is None: return False
    if isinstance(want, list): return any(match(k, got, w) for w in want)
    if k in NUMERIC: return abs(float(got) - float(want)) < 0.01
    return str(got).strip().lower() == str(want).strip().lower()


def score_lines(items, t):
    """Line-item score: (expected amounts found, expected total, extra amounts the tool invented).
    Each expected line may list an alternative amount (AmountAlt, e.g. gross instead of net); the better of the two readings counts."""
    from collections import Counter
    got = Counter(round(float(i["Amount"]), 2) for i in items if i.get("Amount") is not None)
    want = [round(i["Amount"], 2) for i in t["LineItems"]]
    best = sum((got & Counter(want)).values())
    if all("AmountAlt" in i for i in t["LineItems"]):
        best = max(best, sum((got & Counter(round(i["AmountAlt"], 2) for i in t["LineItems"])).values()))
    return best, len(want), max(0, sum(got.values()) - best)


def load(tool, stem):
    path = OUT / f"{tool.lower()}-{stem}.json"
    res = json.loads(path.read_text(encoding="utf-8"))
    return {"CU": cu_norm, "DI": di_norm, "CUP": cup_norm}[tool](res), res
