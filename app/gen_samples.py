"""Generate fully synthetic sample files: 3 invoices (+ ground truth) and a short silent video.
No real company or personal data. Run: python gen_samples.py"""
import json, io
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import numpy as np, cv2

OUT = Path("samples"); OUT.mkdir(exist_ok=True)

INVOICES = [
    dict(file="invoice-01-clean.pdf", vendor="Northwind Fabrication Co.", vendor_addr="1200 Harbor Way, Portland, OR 97201",
         customer="Contoso Labs Ltd.", customer_addr="88 Market Street, Seattle, WA 98101",
         number="NW-2026-0417", date="2026-03-14", due="2026-04-13", po="PO-55812", currency="USD",
         items=[("Steel bracket, 40mm", 120, 4.75), ("Mounting plate, 6mm", 40, 18.20), ("Fastener kit (M6)", 25, 12.00)],
         tax_rate=0.08, layout="clean"),
    dict(file="invoice-02-scanned.pdf", vendor="Fabrikam Office Supply", vendor_addr="410 Elm Avenue, Austin, TX 78701",
         customer="Adventure Works Cycles", customer_addr="3300 Ridge Road, Denver, CO 80202",
         number="FAB-88213", date="2026-02-02", due="2026-03-04", po="AW-7731", currency="USD",
         items=[("Copy paper, case", 18, 42.50), ("Toner cartridge, black", 6, 96.00), ("Desk organizer", 10, 14.99), ("Whiteboard markers (12)", 15, 9.25)],
         tax_rate=0.0825, layout="skewed"),
    dict(file="invoice-03-eu.pdf", vendor="Tailspin Logistik GmbH", vendor_addr="Hafenstrasse 22, 20457 Hamburg, Germany",
         customer="Litware Retail SA", customer_addr="14 Rue de la Paix, 75002 Paris, France",
         number="TL/2026/00931", date="2026-01-21", due="2026-02-20", po="LW-2209", currency="EUR",
         items=[("Pallet freight, Hamburg-Paris", 4, 310.00), ("Customs handling", 1, 145.00), ("Insurance surcharge", 1, 62.50)],
         tax_rate=0.19, layout="eu"),
]

def totals(inv):
    sub = round(sum(q * p for _, q, p in inv["items"]), 2)
    tax = round(sub * inv["tax_rate"], 2)
    return sub, tax, round(sub + tax, 2)

def draw(inv, c):
    sub, tax, tot = totals(inv)
    sym = "$" if inv["currency"] == "USD" else "EUR "
    eu = inv["layout"] == "eu"
    c.setFont("Helvetica-Bold", 20); c.drawString(50, 740, inv["vendor"])
    c.setFont("Helvetica", 10); c.drawString(50, 724, inv["vendor_addr"])
    c.setFont("Helvetica-Bold", 22); c.drawRightString(560, 740, "RECHNUNG / INVOICE" if eu else "INVOICE")
    c.setFont("Helvetica", 10)
    y = 715
    for k, v in [("Invoice No:", inv["number"]), ("Invoice Date:", inv["date"]), ("Due Date:", inv["due"]), ("PO Number:", inv["po"])]:
        c.drawRightString(500, y, k); c.drawString(505, y, v); y -= 14
    c.setFont("Helvetica-Bold", 10); c.drawString(50, 650, "Bill To:")
    c.setFont("Helvetica", 10); c.drawString(50, 636, inv["customer"]); c.drawString(50, 622, inv["customer_addr"])
    ty = 580
    c.setFillColor(colors.lightgrey); c.rect(50, ty - 4, 510, 18, fill=1, stroke=0); c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    for x, h in [(55, "Description"), (330, "Qty"), (390, "Unit Price"), (490, "Amount")]: c.drawString(x, ty, h)
    c.setFont("Helvetica", 10); ty -= 20
    for d, q, p in inv["items"]:
        c.drawString(55, ty, d); c.drawString(330, ty, str(q)); c.drawString(390, ty, f"{sym}{p:,.2f}"); c.drawString(490, ty, f"{sym}{q*p:,.2f}"); ty -= 16
    ty -= 10
    for label, val, bold in [("Subtotal", sub, False), (f"Tax ({inv['tax_rate']*100:.2f}%)", tax, False), ("TOTAL DUE", tot, True)]:
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 11)
        c.drawRightString(470, ty, label); c.drawString(490, ty, f"{sym}{val:,.2f}"); ty -= 16
    c.setFont("Helvetica-Oblique", 9); c.drawString(50, 60, "Payment terms: Net 30. Thank you for your business.")

def make_pdf(inv):
    path = OUT / inv["file"]
    c = canvas.Canvas(str(path), pagesize=letter); draw(inv, c); c.save()
    return path

def make_scanned(inv):
    """Image-only PDF without PyMuPDF: draw text onto a raster with OpenCV, skew + noise, wrap in a PDF."""
    sub, tax, tot = totals(inv)
    W, H = 1275, 1650
    img = np.full((H, W, 3), 245, np.uint8)
    f = cv2.FONT_HERSHEY_SIMPLEX
    def t(txt, x, y, s=0.9, b=2): cv2.putText(img, txt, (x, y), f, s, (30, 30, 30), b, cv2.LINE_AA)
    t(inv["vendor"], 110, 150, 1.3, 3); t(inv["vendor_addr"], 110, 190, 0.8, 1); t("INVOICE", 980, 150, 1.4, 3)
    y = 250
    for k, v in [("Invoice No:", inv["number"]), ("Invoice Date:", inv["date"]), ("Due Date:", inv["due"]), ("PO Number:", inv["po"])]:
        t(k, 800, y, 0.8, 1); t(v, 990, y, 0.8, 1); y += 36
    t("Bill To:", 110, 440, 0.9, 2); t(inv["customer"], 110, 480, 0.8, 1); t(inv["customer_addr"], 110, 516, 0.8, 1)
    y = 620; cv2.rectangle(img, (100, y - 32), (1175, y + 12), (210, 210, 210), -1)
    for x, h in [(110, "Description"), (700, "Qty"), (800, "Unit Price"), (1020, "Amount")]: t(h, x, y, 0.8, 2)
    y += 55
    for d, q, p in inv["items"]:
        t(d, 110, y, 0.8, 1); t(str(q), 710, y, 0.8, 1); t(f"${p:,.2f}", 800, y, 0.8, 1); t(f"${q*p:,.2f}", 1020, y, 0.8, 1); y += 48
    y += 30
    for label, val, bold in [("Subtotal", sub, False), (f"Tax ({inv['tax_rate']*100:.2f}%)", tax, False), ("TOTAL DUE", tot, True)]:
        t(label, 780, y, 0.9, 2 if bold else 1); t(f"${val:,.2f}", 1020, y, 0.9, 2 if bold else 1); y += 44
    # skew + blur + noise
    M = cv2.getRotationMatrix2D((W / 2, H / 2), 1.6, 1.0)
    img = cv2.warpAffine(img, M, (W, H), borderValue=(245, 245, 245))
    img = cv2.GaussianBlur(img, (3, 3), 0)
    rng = np.random.default_rng(7)
    img = np.clip(img.astype(np.int16) + rng.normal(0, 9, img.shape), 0, 255).astype(np.uint8)
    ok, jpg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 70])
    path = OUT / inv["file"]
    c = canvas.Canvas(str(path), pagesize=letter)
    from reportlab.lib.utils import ImageReader
    c.drawImage(ImageReader(io.BytesIO(jpg.tobytes())), 0, 0, width=612, height=792); c.save()
    return path

def make_video(path):
    """30s, 960x540, 10 fps silent slide video with distinct on-screen facts (so there are concrete facts to look for)."""
    slides = [
        ("Contoso Warehouse Safety Briefing", ["Presenter: Dana Whitfield, Safety Lead", "Date: June 3, 2026", "Duration: about 30 seconds"]),
        ("Rule 1: Forklift Zones", ["Pedestrians stay behind the yellow line", "Maximum forklift speed: 5 mph", "Horn required at every intersection"]),
        ("Rule 2: Loading Dock", ["Wheel chocks required on all trailers", "Dock 4 is reserved for hazmat deliveries", "Report spills to extension 5511"]),
        ("Rule 3: Emergency", ["Assembly point: North parking lot", "Eyewash stations: aisles 3, 9 and 14", "Training renewal due every 12 months"]),
    ]
    W, H, FPS, SEC = 960, 540, 10, 7
    vw = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    f = cv2.FONT_HERSHEY_SIMPLEX
    palette = [(120, 60, 20), (40, 90, 30), (30, 60, 120), (90, 30, 90)]
    for i, (title, lines) in enumerate(slides):
        for n in range(FPS * SEC):
            img = np.full((H, W, 3), palette[i], np.uint8)
            cv2.rectangle(img, (0, 0), (W, 90), (20, 20, 20), -1)
            cv2.putText(img, title, (30, 62), f, 1.3, (255, 255, 255), 3, cv2.LINE_AA)
            for j, ln in enumerate(lines):
                cv2.putText(img, ln, (50, 190 + j * 80), f, 1.1, (245, 245, 245), 2, cv2.LINE_AA)
            cv2.rectangle(img, (0, H - 12), (int(W * (n + 1) / (FPS * SEC)), H), (0, 200, 255), -1)  # moving progress bar
            vw.write(img)
    vw.release()

if __name__ == "__main__":
    truth = {}
    for inv in INVOICES:
        sub, tax, tot = totals(inv)
        if inv["layout"] == "skewed": make_scanned(inv)
        else: make_pdf(inv)
        truth[inv["file"]] = dict(VendorName=inv["vendor"], CustomerName=inv["customer"], InvoiceId=inv["number"],
            InvoiceDate=inv["date"], DueDate=inv["due"], PurchaseOrder=inv["po"], SubTotal=sub, TotalTax=tax, InvoiceTotal=tot,
            Currency=inv["currency"], LineItemCount=len(inv["items"]),
            LineItems=[dict(Description=d, Quantity=q, UnitPrice=u, Amount=round(q * u, 2)) for d, q, u in inv["items"]])
    (OUT / "ground-truth.json").write_text(json.dumps(truth, indent=2), encoding="utf-8")
    make_video(OUT / "safety-briefing.mp4")
    try:   # browsers cannot play OpenCV's MPEG-4 Part 2 output, so make an H.264 copy for the UI (analysis still uses the original)
        import subprocess, imageio_ffmpeg
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-i", str(OUT / "safety-briefing.mp4"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-profile:v", "main", "-movflags", "+faststart", "-an", str(OUT / "safety-briefing-web.mp4")], check=True, capture_output=True)
    except Exception as e:
        print("note: could not make the H.264 web copy (pip install imageio-ffmpeg):", e)
    for p in sorted(OUT.iterdir()): print(f"{p.name:28s} {p.stat().st_size/1024:8.1f} KB")
