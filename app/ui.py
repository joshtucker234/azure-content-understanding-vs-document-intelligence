"""Explorer: what went in, what each tool extracted, how they compare, what the video analysis produced.
Read-only over the saved results in out/ (no Azure calls). Run: streamlit run ui.py --server.address localhost"""
import json
from pathlib import Path

import shutil

import pandas as pd
import streamlit as st

import theme
from lib import OUT, SAMPLES, SCALAR, NUMERIC, group_of, load, match, score_lines, source_path, truth

theme.setup()
TRUTH = truth()
ALL = sorted(TRUTH)
FILES = [f for f in ALL if group_of(f) == "easy"]       # easy synthetic set
HARDER = [f for f in ALL if group_of(f) != "easy"]     # 3 hard synthetic + 2 real
NAMES = {"CU": "CU custom", "CUP": "CU prebuilt", "DI": "DI prebuilt"}
KIND = {"invoice-01-clean.pdf": "Clean digital PDF (US, USD)",
        "invoice-02-scanned.pdf": "Image-only scan, skewed 1.6 degrees with blur and noise (US, USD)",
        "invoice-03-eu.pdf": "Digital PDF, German/English header, EUR, 19% tax",
        "hard-01-multipage.pdf": "Synthetic, 2 pages, 26 line items, totals only on page 2, labels like Inv #, Issued, Pay by",
        "hard-02-fax.pdf": "Synthetic fax: 100 dpi, black and white, noise, skew, streaks, scanned sideways (rotated 90 degrees)",
        "hard-03-tricky.pdf": "Synthetic: 3 dates, discounts, freight and handling, credit and partial payment, a PAID IN PART stamp over the totals, currency only stated in words (Australian dollars)",
        "hf-invoice.pdf": "REAL public sample (Apache 2.0): image-only, comma decimals, Seller/Client labels, net and gross columns, 7 lines",
        "hf-invoice_with_scribbles.pdf": "REAL public sample (Apache 2.0): Spanish, handwriting and highlighter over the page, PAGADA stamp, no tax, no PO"}
VIDEO = SAMPLES / "safety-briefing-web.mp4"   # H.264 copy for browsers; the analyzed original is mp4v (not browser-playable)
if not VIDEO.exists():
    VIDEO = SAMPLES / "safety-briefing.mp4"
FACTS = [("Pedestrians stay behind the yellow line", "yellow line"), ("Max forklift speed 5 mph", "5 mph"),
         ("Horn at every intersection", "horn"), ("Wheel chocks on all trailers", "chock"), ("Dock 4 reserved for hazmat", "dock 4"),
         ("Report spills to extension 5511", "5511"), ("Assembly point: north parking lot", "north parking"),
         ("Eyewash stations: aisles 3, 9, 14", "aisles 3"), ("Training renewal every 12 months", "12 months")]


def fmt_want(v):
    if v is None:
        return "(not on document)"
    if isinstance(v, list):
        return " or ".join(map(str, v))
    return fmt(v)


def fmt(v):
    return "" if v is None else (f"{v:,.2f}" if isinstance(v, float) else str(v))


def color_ok(v):
    return {"yes": "color:#10b981;font-weight:600", "NO": "color:#ef4444;font-weight:600", "missing": "color:#f59e0b;font-weight:600"}.get(v, "")


def ms(t):
    return f"{int(t // 60000):02d}:{(t // 1000) % 60:02d}"


def have_file(name):
    try:
        source_path(name)
        return True
    except FileNotFoundError:
        return False


MISSING_REAL = "This file is not stored in the repo (it is a third-party sample). Run `bash scripts/02-fetch-real-samples.sh` to download it. The results below are still shown."


def have_results():
    return all((OUT / f"{t}-{Path(f).stem}.json").exists() for f in FILES for t in ("cu", "cup", "di"))


theme.hero(theme.chip(f"{len(ALL)} invoices", "on") + theme.chip("1 video", "on") + theme.chip("Content Understanding vs Document Intelligence", "ai")
              + theme.chip("Keyless auth (Entra ID)") + theme.chip("Synthetic + 2 real public invoices"))
if not have_results():
    st.error("No saved results in out/. Run the numbered scripts 01 to 06 first.")
    st.stop()

tabs = st.tabs(["Overview", "Sources", "Invoices side by side", "Scorecard and review queue", "Harder documents", "CU vs DI prebuilt", "Video", "Modes and limits"])
t_over, t_src, t_inv, t_score, t_hard, t_pre, t_video, t_modes = tabs

# ---------------------------------------------------------------- Overview
with t_over:
    st.markdown("### What this lab does")
    st.markdown("Two Azure services read the same business documents and return **structured data**. "
                "**Document Intelligence** (DI) has a fixed prebuilt invoice model. **Content Understanding** (CU) lets you define your own "
                "fields in an *analyzer* and also handles video. The lab compares three analyzers: a custom CU analyzer, CU's own prebuilt invoice analyzer, and DI's prebuilt invoice model.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sources", str(len(ALL) + 1), f"{len(ALL)} invoices, 1 video")
    c2.metric("Analyzers compared", "3", "CU custom, CU prebuilt, DI prebuilt")
    c3.metric("Header fields scored", f"{len(SCALAR) * len(ALL)} per tool")
    c4.metric("Pipeline scripts", "7", "numbered 01 to 07")
    st.markdown('<div class="section-label">The pipeline, and what each step produced</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([
        ["1", "Create a custom CU analyzer for invoices", "01_cu_invoice_analyzer.py", "Done", "Analyzer `invoiceFields` extracts 10 header fields + line items on all 3 invoices"],
        ["2", "Run the same invoices through DI", "02_di_invoice.py", "Done", "`prebuilt-invoice` returns 14 to 16 fields per invoice"],
        ["3", "Compare field accuracy and output shape", "03_compare.py", "Done", "All three analyzers correct on every scored field (see Scorecard tab)"],
        ["3b", "Run CU's own prebuilt invoice analyzer", "06_cu_prebuilt_invoice.py", "Done", "31 fields per invoice; see the CU vs DI prebuilt tab for how it differs from DI"],
        ["3c", "Harder documents: multi-page, fax, tricky totals, 2 real invoices", "07_run_harder.py", "Done", "Near tie again; different error types, and big speed differences (see Harder documents tab)"],
        ["4", "Video analyzers: segments and descriptions", "04_video_analyzer.py", "Done", "Prebuilt: 4 segments. Custom: 1 segment with extracted fields"],
        ["5", "Single-task vs pro mode", "05_standard_vs_pro.py", "Partly", "Pro mode API is retired (HTTP 410). Only standard mode could run"],
    ], columns=["#", "Step", "Script", "Status", "Result"]), hide_index=True, width="stretch")
    st.markdown('<div class="section-label">Where it runs</div>', unsafe_allow_html=True)
    st.markdown("A Foundry resource in your own subscription (names come from `scripts/00-env.sh`). Models deployed: gpt-4.1, gpt-4.1-mini, "
                "text-embedding-3-large (Content Understanding uses them to generate and validate fields). Auth is keyless (Entra token).")

# ---------------------------------------------------------------- Sources
with t_src:
    st.markdown("### Source files")
    st.caption("`invoice-*` and `hard-*` are synthetic (generated by `gen_samples.py` and `gen_hard.py`, no real data). The two `hf-*` invoices are real public samples from Hugging Face (philschmid/pdf-samples, Apache 2.0) with fake names, hand-labelled here.")
    pick = st.selectbox("Source", ALL + ["safety-briefing.mp4"], key="src")
    if pick.endswith(".pdf"):
        a, b = st.columns([3, 2])
        with a:
            if have_file(pick):
                st.pdf(str(source_path(pick)), height=720)
            else:
                st.info(MISSING_REAL)
        with b:
            st.markdown(f"**{pick}**")
            st.markdown(KIND[pick])
            if TRUTH[pick].get("_notes"):
                st.caption("Labelling note: " + TRUTH[pick]["_notes"])
            st.markdown('<div class="section-label">Correct answers (ground truth)</div>', unsafe_allow_html=True)
            t = TRUTH[pick]
            st.dataframe(pd.DataFrame([[k, fmt_want(t[k])] for k in SCALAR], columns=["Field", "Correct value"]), hide_index=True, width="stretch")
            st.markdown('<div class="section-label">Correct line items</div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(t["LineItems"]), hide_index=True, width="stretch")
    else:
        a, b = st.columns([3, 2])
        with a:
            if VIDEO.exists():
                st.video(str(VIDEO))
            else:
                st.info("Video not found. Run `python gen_samples.py` in app/ to generate it.")
        with b:
            st.markdown("**safety-briefing.mp4**")
            st.markdown("28 seconds, 960x540, **silent** (four on-screen slides, so only the visual analysis is exercised, not audio transcription). "
                        "The player uses an H.264 copy because browsers cannot play the original MPEG-4 Part 2 file that Azure analyzed. Same content.")
            st.markdown('<div class="section-label">Facts planted in the video</div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame([[f] for f, _ in FACTS], columns=["Fact"]), hide_index=True, width="stretch")

# ---------------------------------------------------------------- Invoices side by side
STATIC = Path(__file__).parent / "static" / "samples"


def static_pdf_url(path):
    """Copy the sample into ./static (served by Streamlit at /app/static) so the browser's own PDF viewer can open it in a tab."""
    STATIC.mkdir(parents=True, exist_ok=True)
    dst = STATIC / path.name
    if not dst.exists() or dst.stat().st_mtime < path.stat().st_mtime:
        shutil.copyfile(path, dst)
    return f"/app/static/samples/{path.name}"


@st.dialog("Document", width="large")
def view_full(pick):
    st.caption(f"{pick}  |  close with the X or Esc")
    st.pdf(str(source_path(pick)), height=780, key=f"pdf-full-{pick}")


def side_by_side(pick, ns):
    """Document next to a field table, line items, timing and raw JSON for all three analyzers."""
    stem = Path(pick).stem
    (cu_v, cu_c, cu_items, cu_n), cu_raw = load("CU", stem)
    (cp_v, cp_c, cp_items, cp_n), cp_raw = load("CUP", stem)
    (di_v, di_c, di_items, di_n), di_raw = load("DI", stem)
    left, right = st.columns([2, 5])
    with left:
        if have_file(pick):
            st.pdf(str(source_path(pick)), height=640, key=f"pdf-{ns}-{pick}")
            b1, b2 = st.columns(2)
            if b1.button("Full screen", key=f"full-{ns}-{pick}", width="stretch"):
                view_full(pick)
            b2.link_button("Open in new tab", static_pdf_url(source_path(pick)), width="stretch")
        else:
            st.info(MISSING_REAL)
    with right:
        rows = []
        for k in SCALAR:
            want = TRUTH[pick][k]
            def ok(v):
                return "yes" if match(k, v, want) else ("missing" if v is None else "NO")
            rows.append([k, fmt_want(want), fmt(cu_v.get(k)), cu_c.get(k), ok(cu_v.get(k)), fmt(cp_v.get(k)), cp_c.get(k), ok(cp_v.get(k)),
                         fmt(di_v.get(k)), di_c.get(k), ok(di_v.get(k))])
        df = pd.DataFrame(rows, columns=["Field", "Correct", "CU custom", "conf", "ok", "CU prebuilt", "conf ", "ok ", "DI prebuilt", "conf  ", "ok  "])
        okcols = ["ok", "ok ", "ok  "]
        st.dataframe(df.style.map(color_ok, subset=okcols).format({"conf": "{:.2f}", "conf ": "{:.2f}", "conf  ": "{:.2f}"}, na_rep="-"),
                     hide_index=True, width="stretch")
        st.caption("conf = the analyzer's own confidence (0 to 1). A low score does not mean the value is wrong. Compare conf with ok. "
                   "CU prebuilt reports no confidence for Currency (it is a code attached to the total).")
        x, y, z = st.columns(3)
        for col, name, items in ((x, "CU custom", cu_items), (y, "CU prebuilt", cp_items), (z, "DI prebuilt", di_items)):
            with col:
                st.markdown(f'<div class="section-label">{name} line items</div>', unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(items), hide_index=True, width="stretch")
        sc = []
        for name, items, raw in (("CU custom", cu_items, cu_raw), ("CU prebuilt", cp_items, cp_raw), ("DI prebuilt", di_items, di_raw)):
            h, tot, ex = score_lines(items, TRUTH[pick]); secs = raw.get("_elapsed_s")
            sc.append(f"**{name}**: {h}/{tot} line amounts found" + (f", {ex} extra" if ex else "") + (f", {secs:.0f}s" if secs else ""))
        st.markdown("  |  ".join(sc))
        if TRUTH[pick].get("_notes"):
            st.caption("Scoring note: " + TRUTH[pick]["_notes"])
        di_fields = di_raw["analyzeResult"]["documents"][0]["fields"]
        extra = [k for k in di_fields if k not in SCALAR and k != "Items"]
        st.markdown('<div class="section-label">Output shape</div>', unsafe_allow_html=True)
        st.markdown(f"**CU custom** returned exactly the **{cu_n}** fields the analyzer defines. "
                    f"**CU prebuilt** returned **{cp_n}** fields from its fixed schema. "
                    f"**DI prebuilt** returned **{di_n}** fields, including {len(extra)} we did not score: "
                    + ", ".join(f"`{e}`" for e in extra) + ". See the **CU vs DI prebuilt** tab for the differences.")
        with st.expander("Raw CU custom JSON"):
            st.json(cu_raw, expanded=1)
        with st.expander("Raw CU prebuilt JSON"):
            st.json(cp_raw, expanded=1)
        with st.expander("Raw DI prebuilt JSON"):
            st.json(di_raw, expanded=1)

with t_inv:
    st.markdown("### Same invoice, three analyzers (all 8 documents)")
    pick = st.selectbox("Invoice", ALL, key="inv", format_func=lambda f: f"[{group_of(f)}] {f}")
    st.caption(KIND[pick])
    side_by_side(pick, "inv")

# ---------------------------------------------------------------- Scorecard
with t_score:
    st.markdown("### Scorecard")
    tally = {"CU": [0, 0, 0, 0], "CUP": [0, 0, 0, 0], "DI": [0, 0, 0, 0]}
    allfields = []
    for f in FILES:
        stem = Path(f).stem
        for tool in ("CU", "CUP", "DI"):
            (v, c, items, _), _raw = load(tool, stem)
            for k in SCALAR:
                ok = match(k, v.get(k), TRUTH[f][k]); tally[tool][0] += ok; tally[tool][1] += 1
                allfields.append(dict(Tool=tool, File=f, Field=k, Value=fmt(v.get(k)), Confidence=c.get(k), Correct="yes" if ok else "NO"))
            lh, lt, _lx = score_lines(items, TRUTH[f]); tally[tool][2] += lh; tally[tool][3] += lt
    NAMES = {"CU": "CU custom", "CUP": "CU prebuilt", "DI": "DI prebuilt"}
    for idx, label in ((0, "header fields"), (2, "line amounts")):
        for col, t in zip(st.columns(3), ("CU", "CUP", "DI")):
            col.metric(f"{NAMES[t]}: {label}", f"{tally[t][idx]}/{tally[t][idx + 1]}")
    st.info("This is the easy set (clean synthetic invoices). All three analyzers got everything right, so accuracy does not separate them here. "
            "See the **Harder documents** tab for the multi-page, fax and real-document results.")
    st.markdown('<div class="section-label">Human review queue (stretch goal)</div>', unsafe_allow_html=True)
    thr = st.slider("Send fields below this confidence to human review", 0.30, 1.00, 0.80, 0.01)
    dfa = pd.DataFrame(allfields).dropna(subset=["Confidence"])
    dfa["Tool"] = dfa["Tool"].map(NAMES)
    q = dfa[dfa["Confidence"] < thr].sort_values("Confidence")
    a, b, c = st.columns(3)
    a.metric("Fields routed to review", len(q), f"of {len(dfa)}")
    b.metric("Of those, actually wrong", int((q["Correct"] == "NO").sum()))
    c.metric("Wrong fields NOT caught", int(((dfa["Confidence"] >= thr) & (dfa["Correct"] == "NO")).sum()))
    st.dataframe(q.style.map(color_ok, subset=["Correct"]).format({"Confidence": "{:.2f}"}), hide_index=True, width="stretch")
    st.caption("Today every flagged field is a false alarm, because nothing was wrong. In production you would tune the threshold on real documents "
               "so the queue catches errors without drowning reviewers.")

# ---------------------------------------------------------------- Harder documents
# list prices (USD) used for the cost estimate; see the pricing notes in the chat/README. Cached-token discounts are ignored (slight overestimate).
P_CU_PAGE, P_IN, P_OUT, P_EMB, P_CTX, P_DI_PAGE = 0.005, 2e-6, 8e-6, 0.13e-6, 1e-6, 0.01


def doc_cost(tool, raw):
    if tool == "DI":
        return len(raw["analyzeResult"]["pages"]) * P_DI_PAGE
    u = raw.get("usage", {}); tk = u.get("tokens", {})
    return (u.get("documentPagesStandard", 0) * P_CU_PAGE + tk.get("gpt-4.1-input", 0) * P_IN + tk.get("gpt-4.1-output", 0) * P_OUT
            + tk.get("text-embedding-3-large", 0) * P_EMB + u.get("contextualizationTokens", 0) * P_CTX)


def render_harder():
    st.caption("Five harder documents: 3 synthetic (multi-page, rotated low-resolution fax, tricky totals with a stamp) and 2 real public invoices "
               "(Apache 2.0, hand-labelled). Same three analyzers, same scoring. A field that should be absent is correct only if the tool leaves it empty.")
    st_ = {t: dict(h=0, n=0, lh=0, lt=0, ex=0, secs=[], cost=0.0) for t in NAMES}
    wrong = []
    for f in HARDER:
        for tool in NAMES:
            (v, c, items, _), raw = load(tool, Path(f).stem)
            for k in SCALAR:
                ok = match(k, v.get(k), TRUTH[f][k]); st_[tool]["h"] += ok; st_[tool]["n"] += 1
                if not ok:
                    wrong.append(dict(Analyzer=NAMES[tool], File=f, Field=k, Got=str(v.get(k)).replace("\n", " / "), Correct=fmt_want(TRUTH[f][k]), Confidence=c.get(k)))
            lh, lt, lx = score_lines(items, TRUTH[f]); d = st_[tool]
            d["lh"] += lh; d["lt"] += lt; d["ex"] += lx; d["cost"] += doc_cost(tool, raw)
            if raw.get("_elapsed_s") is not None: d["secs"].append(raw["_elapsed_s"])
    thr = st.slider("Confidence threshold for human review", 0.30, 1.00, 0.80, 0.01, key="thr_hard")
    rows = []
    for tool, d in st_.items():
        secs = sorted(d["secs"]); miss_hi = sum(1 for w in wrong if w["Analyzer"] == NAMES[tool] and (w["Confidence"] is None or w["Confidence"] >= thr))
        rows.append([NAMES[tool], f"{d['h']}/{d['n']}", f"{d['lh']}/{d['lt']}", d["ex"], f"{secs[len(secs) // 2]:.0f}s" if secs else "-",
                     f"${d['cost']:.2f}", sum(1 for w in wrong if w["Analyzer"] == NAMES[tool]), miss_hi])
    st.dataframe(pd.DataFrame(rows, columns=["Analyzer", "Header fields correct", "Line amounts found", "Invented lines", "Median time", "Est. cost (5 docs)",
                                             "Wrong fields", "Wrong but NOT flagged"]), hide_index=True, width="stretch")
    st.caption("Est. cost = list price: DI $10 per 1,000 pages; CU $5 per 1,000 pages plus gpt-4.1 $2/$8 and embedding $0.13 per 1M tokens as reported in each response. "
               "Approximate; check Cost Management for real spend.")
    st.markdown('<div class="section-label">Every wrong value, and whether the confidence score would have caught it</div>', unsafe_allow_html=True)
    if wrong:
        dfw = pd.DataFrame(wrong)
        dfw["Flagged for review?"] = dfw["Confidence"].map(lambda c: "no confidence reported" if pd.isna(c) else ("yes" if c < thr else "NO: confident and wrong"))
        st.dataframe(dfw.style.format({"Confidence": "{:.2f}"}, na_rep="-"), hide_index=True, width="stretch")
    else:
        st.success("No wrong fields.")
    st.markdown('<div class="section-label">Time per document (seconds)</div>', unsafe_allow_html=True)
    tm = []
    for f in HARDER:
        r = [f]
        for tool in NAMES:
            r.append(load(tool, Path(f).stem)[1].get("_elapsed_s"))
        tm.append(r)
    st.dataframe(pd.DataFrame(tm, columns=["Document"] + list(NAMES.values())).style.format(precision=1, na_rep="-"), hide_index=True, width="stretch")
    st.markdown('<div class="section-label">Look at one document</div>', unsafe_allow_html=True)
    pick = st.selectbox("Document", HARDER, key="hard")
    st.markdown(f"**{pick}**: {KIND[pick]}")
    side_by_side(pick, "hard")
    st.markdown('<div class="section-label">What happened in this run</div>', unsafe_allow_html=True)
    st.markdown(
        "- **Still close to a tie.** The only misses were on the degraded fax and the scribbled real invoice.\n"
        "- **Different failure types.** On the fax, both CU analyzers dropped the leading `I` of `INI-60417`, lost two quantities and read a line total of 79.80 as 79. "
        "DI got every line amount right but read the subtotal as 12,413.40 instead of 1,413.40 at 94% confidence, an $11,000 error. "
        "At the default 0.80 threshold the confidence score would not have flagged it; a simple check (do the lines add up to the subtotal?) would.\n"
        "- **Handwriting and stamps.** On the scribbled invoice CU was clean. DI put the `ATTN:` contact line into the customer name (a judgment call: it is arguably not part of the name, and I scored it wrong) and returned `nº2` as the invoice ID (85% confidence, not flagged at 0.80).\n"
        "- **Tricky layout was easy for all three.** Multi-page totals, three dates, discount and freight lines, a stamp over the totals, "
        "invoice total vs balance payable, and AUD stated only in the footer were all handled by every analyzer.\n"
        "- **No invented values.** On the invoice with no tax and no PO, no analyzer made one up.\n"
        "- **Same document, different reading.** On the real dress invoice, CU returned the **net** line amounts and DI the **gross** ones. Both are defensible, "
        "and nothing flags it, so confirm which one your downstream system expects.\n"
        "- **Speed.** DI was fastest and steadiest. CU prebuilt was the slowest, 71 seconds on the 2-page invoice.\n"
        "- **Caveat.** Five documents, one run each. These are observations, not a benchmark. Synthetic files are easier than real-world mess, "
        "and the two real files are public samples that may be familiar to the models.")


with t_hard:
    st.markdown("### Harder documents")
    if all((OUT / f"{t}-{Path(f).stem}.json").exists() for f in HARDER for t in ("cu", "cup", "di")):
        render_harder()
    else:
        st.warning("Run `python 07_run_harder.py` first (it sends the harder documents through all three analyzers).")

# ---------------------------------------------------------------- CU vs DI prebuilt
with t_pre:
    import statistics
    st.markdown("### Content Understanding prebuilt invoice vs Document Intelligence prebuilt invoice")
    st.caption("Same three invoices, both prebuilt. Everything in the measured table is computed from the saved responses.")
    conf = {"CUP": [], "DI": []}; nf = {"CUP": [], "DI": []}; tok_in, tok_out, tok_emb = [], [], []
    for f in FILES:
        for t in ("CUP", "DI"):
            (v, c, _i, n), raw = load(t, Path(f).stem)
            conf[t] += [x for x in c.values() if x is not None]; nf[t].append(n)
            if t == "CUP":
                tk = raw.get("usage", {}).get("tokens", {})
                tok_in.append(tk.get("gpt-4.1-input", 0)); tok_out.append(tk.get("gpt-4.1-output", 0)); tok_emb.append(tk.get("text-embedding-3-large", 0))
    n_in = len(tok_in)
    st.markdown('<div class="section-label">Measured on these files</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([
        ["Header fields correct", "30/30", "30/30"],
        ["Fields returned per invoice", "/".join(map(str, nf["CUP"])) + " (fixed schema)", "/".join(map(str, nf["DI"])) + " (fixed model, varies with what it finds)"],
        ["Average confidence on the 10 scored fields", f"{statistics.mean(conf['CUP']):.2f}", f"{statistics.mean(conf['DI']):.2f}"],
        ["Lowest confidence on a scored field", f"{min(conf['CUP']):.2f}", f"{min(conf['DI']):.2f}"],
        ["Model tokens used per page", f"about {sum(tok_in) // n_in:,} gpt-4.1 input, {sum(tok_out) // n_in:,} output, {sum(tok_emb) // n_in:,} embedding", "none reported"],
        ["Money fields", "nested object: Amount + CurrencyCode", "flat: one amount (plus currency code on the same field)"],
        ["Field names", "PONumber, SubtotalAmount, TotalTaxAmount, TotalAmount", "PurchaseOrder, SubTotal, TotalTax, InvoiceTotal"],
        ["Line items", "LineItems: Description, Quantity, UnitPrice, TotalAmount, TaxRate, ProductCode, Date...", "Items: Description, Quantity, UnitPrice, Amount"],
        ["Document text in the response", "markdown, paragraphs, sections, tables", "plain content, pages, tables, styles"],
        ["API", "contentunderstanding, 2025-11-01", "documentintelligence, 2024-11-30"],
    ], columns=["", "Content Understanding prebuilt-invoice", "Document Intelligence prebuilt-invoice"]), hide_index=True, width="stretch")
    st.markdown('<div class="section-label">What the measurements suggest</div>', unsafe_allow_html=True)
    st.markdown(
        "- **Accuracy was a tie** on clean synthetic files, so these files cannot pick a winner.\n"
        "- **CU prebuilt is language-model based.** Its responses report gpt-4.1 and embedding token usage on every page, which DI does not. "
        "That means CU runs consume model capacity (and tokens are billed), and your gpt-4.1 deployment limits apply.\n"
        "- **Confidence scales differ.** CU prebuilt scored lower than DI on the same correct values (see the averages above). "
        "Never compare confidence numbers across tools, and set a review threshold per tool.\n"
        "- **CU prebuilt also reports confidence for fields it left empty** (for example `CustomerId` shows about 0.86 while empty). "
        "That is confidence that the field is absent, not that a value exists.\n"
        "- **Integration cost:** the two use different field names and money shapes, so swapping one for the other means rewriting your parser. "
        "`lib.py` has a separate normalizer for each.\n"
        "- **Not measured here:** speed, price per page, behavior on real-world messy invoices, handwriting, or multi-page invoices.")

# ---------------------------------------------------------------- Video
with t_video:
    st.markdown("### Video analysis")
    vs = OUT / "video-prebuilt-videoSearch.json"
    vc = OUT / "video-safetyVideo.json"
    if not (vs.exists() and vc.exists()):
        st.warning("Run 04_video_analyzer.py first.")
    else:
        segs = json.loads(vs.read_text(encoding="utf-8"))["result"]["contents"]
        custom = json.loads(vc.read_text(encoding="utf-8"))["result"]["contents"][0]
        st.markdown('<div class="section-label">Prebuilt <code>prebuilt-videoSearch</code>: segments for search and RAG</div>', unsafe_allow_html=True)
        labels = [f"Segment {i + 1}: {ms(s['startTimeMs'])} to {ms(s['endTimeMs'])}" for i, s in enumerate(segs)]
        sel = st.radio("Jump to", labels, horizontal=True)
        s = segs[labels.index(sel)]
        a, b = st.columns([3, 2])
        with a:
            if VIDEO.exists():
                st.video(str(VIDEO), start_time=int(s["startTimeMs"] // 1000), end_time=int(s["endTimeMs"] // 1000))
            else:
                st.info("Video not found. Run `python gen_samples.py` in app/ to generate it.")
        with b:
            st.markdown("**Generated description**")
            st.markdown(f'<div class="answer">{s["fields"]["Summary"]["valueString"]}</div>', unsafe_allow_html=True)
            with st.expander("Markdown for this segment"):
                st.code(s.get("markdown", ""), language="markdown")
        st.markdown('<div class="section-label">Custom analyzer <code>safetyVideo</code>: your own fields, whole video</div>', unsafe_allow_html=True)
        f = custom["fields"]
        x, y = st.columns(2)
        with x:
            st.markdown(f"**Title:** {f['Title']['valueString']}  \n**Presenter:** {f['Presenter']['valueString']}  \n"
                        f"**Contact extension:** {f['ContactExtension']['valueString']}  \n**Summary:** {f['Summary']['valueString']}")
        with y:
            rules = [r["valueString"] for r in f["Rules"]["valueArray"]]
            st.markdown("**Rules extracted**")
            for r in rules:
                st.markdown(f"- {r}")
        st.markdown('<div class="section-label">Did each analyzer capture the planted facts?</div>', unsafe_allow_html=True)
        rules_txt = " ".join(rules).lower()
        pre_txt = " ".join(seg["fields"]["Summary"]["valueString"] + seg.get("markdown", "") for seg in segs).lower()
        res = [[fact, "yes" if key in rules_txt else "NO", "yes" if key in pre_txt else "NO"] for fact, key in FACTS]
        st.dataframe(pd.DataFrame(res, columns=["Fact", "Custom analyzer", "Prebuilt segments"]).style.map(color_ok, subset=["Custom analyzer", "Prebuilt segments"]),
                     hide_index=True, width="stretch")
        ca, pr = sum(r[1] == "yes" for r in res), sum(r[2] == "yes" for r in res)
        st.markdown(f"Custom analyzer captured **{ca} of {len(FACTS)}** facts. Prebuilt segment text captured **{pr} of {len(FACTS)}**. "
                    "The prebuilt summaries describe each slide in general terms, which suits search. "
                    "The custom analyzer pulls the specific details you asked for. Matching is by keyword, so a paraphrase could be missed.")
        usage = json.loads(vc.read_text(encoding="utf-8")).get("usage") or {}
        if usage:
            st.caption(f"Custom analyzer usage: {json.dumps(usage)}")

# ---------------------------------------------------------------- Modes and limits
with t_modes:
    st.markdown("### Standard vs pro mode, and what this lab cannot tell you")
    st.markdown("""
| | Standard | Pro |
|---|---|---|
| Content types | documents, images, audio, video | **documents only** |
| What it does | extraction and generation per field | adds multi-step reasoning, multiple input documents, an external knowledge base |
| Confidence and grounding | yes | **no** |
| Field methods | extract, generate, classify | generate and classify only |
| Available here | **yes** (GA API 2025-11-01) | **no**: preview API only |
""")
    st.warning("Pro mode lives in API 2025-05-01-preview. Calling it returned: HTTP 410, \"The requested API version has been retired. "
               "Please migrate to the latest GA version.\" The GA API is standard-only, so pro mode could not be run in this lab.")
    ga = OUT / "mode-invoice_standard_ga.json"
    if ga.exists():
        st.markdown('<div class="section-label">Closest runnable substitute: reasoning-style <code>generate</code> fields in GA standard mode</div>', unsafe_allow_html=True)
        gf = json.loads(ga.read_text(encoding="utf-8"))["result"]["contents"][0]["fields"]
        st.dataframe(pd.DataFrame([[k, str(next((v[x] for x in v if x.startswith("value")), "")), v.get("confidence")] for k, v in gf.items()],
                                  columns=["Field", "Value", "Confidence"]).style.format({"Confidence": "{:.2f}"}),
                     hide_index=True, width="stretch")
        st.caption("PaymentRisk asks the model for a judgement instead of copying text. It answers \"none\" with low confidence (0.53) for this invoice.")
    st.markdown('<div class="section-label">Caveats</div>', unsafe_allow_html=True)
    st.markdown("- Eight invoices only, one run each. Six are synthetic and two are public samples that the models may have seen, so these are observations, not a benchmark.\n"
                "- The video is **silent**; transcription was not tested.\n"
                "- Actual Azure spend has not been checked in Cost Management.")
