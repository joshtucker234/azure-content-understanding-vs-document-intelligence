"""Harder synthetic invoices (exact ground truth). All data is fabricated.
 hard-01-multipage : 26 line items across 2 pages, totals only on page 2, odd labels ("Inv #", "Issued", "Terms")
 hard-02-fax       : low-resolution, binarized, noisy, skewed, scanned sideways (rotated 90 degrees)
 hard-03-tricky    : 3 dates, discounts, freight/handling, credit + partial payment, a PAID stamp over the totals,
                     currency (AUD) stated only in words, thousands separators
Run: python gen_hard.py"""
import io, json, random
from datetime import date, timedelta
from pathlib import Path

import cv2, numpy as np, pymupdf
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from gen_samples import draw, totals

OUT = Path("samples/hard"); OUT.mkdir(parents=True, exist_ok=True)
rng = random.Random(11)


def lines_block(c, y, rows, cols, sym="$", font=9.5, step=15):
    c.setFont("Helvetica", font)
    for d, q, p, a in rows:
        c.drawString(cols[0], y, d); c.drawString(cols[1], y, str(q)); c.drawString(cols[2], y, f"{sym}{p:,.2f}"); c.drawString(cols[3], y, f"{sym}{a:,.2f}")
        y -= step
    return y


# ---------------------------------------------------------------- hard-01
def make_multipage():
    names = ["Hex bolt M8x40 zinc", "Hex nut M8 zinc", "Flat washer M8", "Lock washer M8", "Carriage bolt M10x80", "Threaded rod M12 1m",
             "Anchor sleeve 10mm", "Angle bracket 50mm", "Corner brace 3in", "Pipe clamp 25mm", "U-bolt 40mm", "Eye bolt M8",
             "Turnbuckle 3/8in", "Wire rope 6mm /m", "Cable tie 300mm (100)", "Self-tap screw 4.8x25 (200)", "Drywall screw 3.5x40 (500)",
             "Concrete screw 6x60 (50)", "Rivet 4mm (250)", "Spring clip 8mm", "Cotter pin 3x30 (100)", "Shackle 8mm", "Hinge 100mm pair",
             "Door pull handle", "Padlock hasp 120mm", "Gate latch 200mm"]
    items = []
    for n in names:
        q = rng.randint(2, 60); p = round(rng.uniform(0.35, 48.0), 2); items.append((n, q, p, round(q * p, 2)))
    sub = round(sum(i[3] for i in items), 2); tax = round(sub * 0.065, 2); tot = round(sub + tax, 2)
    inv = dict(vendor="Globex Industrial Supply", addr="5500 Foundry Rd, Cleveland, OH 44101", number="GL-771204",
               issued=date(2026, 4, 9), due=date(2026, 5, 24), po="4500-88217", customer="Initrode Fabrication LLC", caddr="17 Mill Street, Akron, OH 44308")
    path = OUT / "hard-01-multipage.pdf"
    c = canvas.Canvas(str(path), pagesize=letter); cols = (50, 330, 400, 490)

    def table_head(y):
        c.setFillColor(colors.lightgrey); c.rect(50, y - 4, 510, 16, fill=1, stroke=0); c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 9.5)
        for x, h in zip(cols, ("Item", "Qty", "Unit", "Ext")): c.drawString(x + 4, y, h)
        return y - 20

    c.setFont("Helvetica-Bold", 18); c.drawString(50, 745, inv["vendor"]); c.setFont("Helvetica", 9.5); c.drawString(50, 731, inv["addr"])
    c.drawString(50, 719, "Tel 555-0147 ext 2210  |  Acct no. 000123456  |  Dept 4410")
    c.setFont("Helvetica-Bold", 16); c.drawRightString(560, 745, "Commercial Invoice")
    c.setFont("Helvetica", 10); y = 725
    for k, v in (("Inv #", inv["number"]), ("Issued", inv["issued"].isoformat()), ("Terms", "Net 45"), ("Pay by", inv["due"].isoformat()), ("Customer PO", inv["po"])):
        c.drawRightString(500, y, k); c.drawString(506, y, v); y -= 13
    c.setFont("Helvetica-Bold", 10); c.drawString(50, 650, "Ship / Bill to"); c.setFont("Helvetica", 10)
    c.drawString(50, 636, inv["customer"]); c.drawString(50, 623, inv["caddr"])
    y = table_head(595); y = lines_block(c, y, items[:14], cols)
    c.setFont("Helvetica-Oblique", 9); c.drawString(50, 50, "Continued on next page"); c.drawRightString(560, 50, "Page 1 of 2"); c.showPage()
    c.setFont("Helvetica-Bold", 11); c.drawString(50, 745, f"{inv['vendor']}  -  Invoice {inv['number']} (continued)")
    y = table_head(715); y = lines_block(c, y, items[14:], cols)
    y -= 14
    for label, val, bold in (("Merchandise", sub, False), ("Sales tax 6.5%", tax, False), ("Amount due", tot, True)):
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 11); c.drawRightString(470, y, label); c.drawString(490, y, f"${val:,.2f}"); y -= 16
    c.setFont("Helvetica", 9); c.drawString(50, y - 20, "Remit to: Globex Industrial Supply, PO Box 9917, Cleveland OH 44101. Questions: 555-0147 ext 2210.")
    c.drawRightString(560, 50, "Page 2 of 2"); c.save()
    return path.name, dict(VendorName=inv["vendor"], CustomerName=inv["customer"], InvoiceId=inv["number"], InvoiceDate=inv["issued"].isoformat(),
        DueDate=inv["due"].isoformat(), PurchaseOrder=inv["po"], SubTotal=sub, TotalTax=tax, InvoiceTotal=tot, Currency="USD",
        LineItems=[dict(Description=d, Quantity=q, UnitPrice=p, Amount=a) for d, q, p, a in items])


# ---------------------------------------------------------------- hard-02
def make_fax():
    inv = dict(file="x", vendor="Initech Parts & Service", vendor_addr="9 Cubicle Court, Plano, TX 75024", customer="Hooli Logistics Inc.",
               customer_addr="1401 Elmwood Blvd, Dallas, TX 75201", number="INI-60417", date="2026-05-06", due="2026-06-05", po="HL-30911", currency="USD",
               items=[("Brake pad set, front", 4, 61.40), ("Rotor 320mm", 4, 118.75), ("Caliper rebuild kit", 2, 39.90), ("Labor, 6.5 hrs", 1, 585.00), ("Shop supplies", 1, 28.00)],
               tax_rate=0.07, layout="clean")
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=letter); draw(inv, c); c.save()
    pix = pymupdf.open(stream=buf.getvalue(), filetype="pdf")[0].get_pixmap(dpi=200)
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.h, pix.w, pix.n)[:, :, :3]
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    g = cv2.resize(g, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)                       # ~100 dpi
    M = cv2.getRotationMatrix2D((g.shape[1] / 2, g.shape[0] / 2), 1.2, 1.0); g = cv2.warpAffine(g, M, g.shape[::-1], borderValue=255)
    g = cv2.GaussianBlur(g, (3, 3), 0); g = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 21, 12)
    r = np.random.default_rng(3)
    g[r.random(g.shape) < 0.012] = 0; g[r.random(g.shape) < 0.004] = 255                         # salt and pepper
    for x in r.integers(0, g.shape[1], 3): g[:, x:x + 2] = 120                                   # fax streaks
    g = cv2.rotate(g, cv2.ROTATE_90_CLOCKWISE)                                                    # scanned sideways
    ok, png = cv2.imencode(".png", g)
    path = OUT / "hard-02-fax.pdf"; c = canvas.Canvas(str(path), pagesize=landscape(letter))
    c.drawImage(ImageReader(io.BytesIO(png.tobytes())), 0, 0, width=792, height=612); c.save()
    sub, tax, tot = totals(inv)
    return path.name, dict(VendorName=inv["vendor"], CustomerName=inv["customer"], InvoiceId=inv["number"], InvoiceDate=inv["date"], DueDate=inv["due"],
        PurchaseOrder=inv["po"], SubTotal=sub, TotalTax=tax, InvoiceTotal=tot, Currency="USD",
        LineItems=[dict(Description=d, Quantity=q, UnitPrice=p, Amount=round(q * p, 2)) for d, q, p in inv["items"]])


# ---------------------------------------------------------------- hard-03
def make_tricky():
    items = [("Laminated floor panels, pack of 12", 18, 142.00, 0.10), ("Underlay roll 15m2", 18, 38.50, 0.0),
             ("Skirting board 2.4m", 60, 11.75, 0.05), ("Adhesive 5L", 6, 64.20, 0.0)]
    rows = [(d, q, p, round(q * p * (1 - disc), 2), disc) for d, q, p, disc in items]
    sub = round(sum(r[3] for r in rows), 2); freight, handling = 120.00, 35.00
    gst = round((sub + freight + handling) * 0.10, 2); total = round(sub + freight + handling + gst, 2)
    credit, paid = 150.00, 1000.00; balance = round(total - credit - paid, 2)
    d_order, d_ship, d_inv = date(2026, 5, 2), date(2026, 5, 14), date(2026, 5, 19); d_due = d_inv + timedelta(days=30)
    path = OUT / "hard-03-tricky.pdf"; c = canvas.Canvas(str(path), pagesize=letter)
    c.setFont("Helvetica-Bold", 19); c.drawString(50, 745, "Wide World Importers Pty Ltd"); c.setFont("Helvetica", 9.5)
    c.drawString(50, 731, "ABN 51 824 753 556  |  22 Quayside Drive, Fremantle WA 6160, Australia")
    c.setFont("Helvetica-Bold", 14); c.drawRightString(560, 745, "TAX INVOICE"); c.setFont("Helvetica", 10); y = 725
    for k, v in (("Document no.", "WWI-2026-3318"), ("Your ref", "WW-PO-48820"), ("Order date", d_order.isoformat()), ("Ship date", d_ship.isoformat()),
                 ("Invoice date", d_inv.isoformat()), ("Pay by", d_due.isoformat())):
        c.drawRightString(480, y, k); c.drawString(486, y, v); y -= 13
    c.setFont("Helvetica-Bold", 10); c.drawString(50, 640, "Delivered to"); c.setFont("Helvetica", 10)
    c.drawString(50, 626, "Blackwood Builders Co-operative"); c.drawString(50, 613, "8 Karri Street, Bunbury WA 6230")
    ty = 575; c.setFillColor(colors.lightgrey); c.rect(50, ty - 4, 510, 16, fill=1, stroke=0); c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 9.5)
    for x, h in ((54, "Description"), (270, "Qty"), (315, "Price"), (385, "Disc"), (445, "Line total")): c.drawString(x, ty, h)
    c.setFont("Helvetica", 9.5); ty -= 18
    for d, q, p, a, disc in rows:
        c.drawString(54, ty, d); c.drawString(270, ty, str(q)); c.drawString(315, ty, f"${p:,.2f}"); c.drawString(385, ty, f"{disc*100:.0f}%" if disc else "-"); c.drawString(445, ty, f"${a:,.2f}"); ty -= 15
    ty -= 8
    for label, val, bold in (("Subtotal (goods after discount)", sub, False), ("Freight", freight, False), ("Handling", handling, False), ("GST 10%", gst, False),
                             ("Invoice total (incl. GST)", total, True), ("Credit applied", -credit, False), ("Amount paid to date", -paid, False), ("Balance payable", balance, True)):
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 10.5); c.drawRightString(440, ty, label)
        c.drawString(455, ty, f"-${abs(val):,.2f}" if val < 0 else f"${val:,.2f}"); ty -= 16
    c.setFont("Helvetica-Oblique", 8.5); c.drawString(50, 60, "All amounts are in Australian dollars. Goods remain the property of the seller until paid in full.")
    c.saveState(); c.translate(330, ty + 70); c.rotate(22); c.setFillColor(colors.Color(0.85, 0.1, 0.1, alpha=0.45)); c.setFont("Helvetica-Bold", 70)
    c.drawCentredString(0, 0, "PAID IN PART"); c.restoreState(); c.save()
    return path.name, dict(VendorName="Wide World Importers Pty Ltd", CustomerName="Blackwood Builders Co-operative", InvoiceId="WWI-2026-3318",
        InvoiceDate=d_inv.isoformat(), DueDate=d_due.isoformat(), PurchaseOrder="WW-PO-48820", SubTotal=sub, TotalTax=gst, InvoiceTotal=total, Currency="AUD",
        LineItems=[dict(Description=d, Quantity=q, UnitPrice=p, Amount=a) for d, q, p, a, _ in rows])


if __name__ == "__main__":
    truth = dict(f() for f in (make_multipage, make_fax, make_tricky))
    (OUT / "ground-truth.json").write_text(json.dumps(truth, indent=2), encoding="utf-8")
    for p in sorted(OUT.iterdir()): print(f"{p.name:26s} {p.stat().st_size/1024:8.1f} KB")
    for k, t in truth.items(): print(k, "lines", len(t["LineItems"]), "total", t["InvoiceTotal"])
