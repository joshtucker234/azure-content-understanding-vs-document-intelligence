# Replicate the lab, step by step

Run everything in Git Bash (Windows) or any POSIX shell. Each step says what it does, why, and how to check it worked.
The Python scripts run from the `app/` folder.

## 0. Before you start

1. Install: Python 3.11+, Azure CLI, `curl`, Git.
2. Sign in to the tenant that owns your subscription: `az login` (add `--tenant <tenant-id>` if you have several).
   If your Owner access comes through a guest account or delegation, sign in with the account that actually holds the
   roles, otherwise role assignments fail with `AuthorizationFailed`.
3. Copy `scripts/00-env.sh.example` to `scripts/00-env.sh` and edit it. **Pick `SUF` once and hard-code it**, because a
   new random value in a new shell points at resources that don't exist.
4. `source scripts/00-env.sh`
5. `cd app && python -m venv .venv && . .venv/Scripts/activate && pip install -r requirements.txt` (Linux/macOS: `. .venv/bin/activate`)

**Region check.** `LOC` must be a Content Understanding region that offers `gpt-4.1`, `gpt-4.1-mini` and
`text-embedding-3-large` as `GlobalStandard`. East US 2 worked for us. List what a region offers with
`az cognitiveservices model list -l $LOC`.

## 1. Provision

```bash
bash scripts/01-provision.sh
```

| What it creates | Why |
|---|---|
| Resource group (tagged) | One thing to delete at the end. The tags carry owner and purpose, which a subscription tag policy may require |
| Foundry resource (`AIServices`) | **One resource serves both Content Understanding and Document Intelligence.** There is nothing else to create: no Search, no Storage |
| `gpt-4.1`, `gpt-4.1-mini`, `text-embedding-3-large` deployments | Content Understanding calls these models for generated fields and for its prebuilt analyzers. They are billed as normal model tokens |
| Roles for **you**: Cognitive Services User and Contributor | Keyless access to both services' APIs. We granted both and did not test with fewer |
| `PATCH .../contentunderstanding/defaults` | A one-time call that tells Content Understanding which deployment to use for each model |

**Check:** `az role assignment list --scope $(az group show -n $RG --query id -o tsv) -o table` shows your roles, and the last
line of the script prints the defaults mapping. Roles can take a few minutes to start working.

## 2. Get the sample documents

The synthetic invoices, the ground truth and the demo video are **already in the repo** (`app/samples/`), so you can skip
to step 3. To regenerate them: `cd app && python gen_samples.py && python gen_hard.py` (the PDFs differ byte-for-byte because
of embedded timestamps, but the content and ground truth are the same).

Two **real public invoices** are used in the harder test. They are third-party files, so they are not stored here:

```bash
bash scripts/02-fetch-real-samples.sh      # downloads two Apache 2.0 sample invoices from Hugging Face
```

| File set | What it is |
|---|---|
| `invoice-01-clean`, `-02-scanned`, `-03-eu` | The easy set: clean PDF, skewed noisy scan, German/EUR layout |
| `hard-01-multipage`, `-02-fax`, `-03-tricky` | The hard synthetic set: 2 pages and 26 lines; low-resolution fax scanned sideways; discounts, freight, credit, a stamp over the totals, currency only stated in words |
| `hf-invoice`, `hf-invoice_with_scribbles` | The real set: an image-only invoice with comma decimals, and a Spanish invoice covered in handwriting and highlighter |
| `safety-briefing.mp4` | A 28-second silent video with nine planted facts |

The expected values for every invoice are in `ground-truth.json` next to it. All data is fabricated or generated.

## 3. Step 1: a custom Content Understanding analyzer

```bash
cd app
python 01_cu_invoice_analyzer.py
```

It creates an **analyzer** named `invoiceFields` and runs the three easy invoices through it. An analyzer is a base analyzer
(`prebuilt-document`: OCR and layout) plus a **field schema** you define: ten header fields and a `LineItems` array. Each field has a
`method`: `extract` (copy what is on the page), `generate` (the model produces it, we use this for `Currency`) or `classify`.
Raw responses go to `app/out/cu-*.json`. Analyzer IDs cannot contain `-`.

**Check:** every invoice prints its ten fields with a confidence value, and `LineItems: 3 items` (4 for the scan).

## 4. Step 2: Document Intelligence on the same files

```bash
python 02_di_invoice.py
```

Calls `prebuilt-invoice` on the same resource. No schema to write: it returns its own fixed field set (14 to 16 fields).
Raw responses go to `app/out/di-*.json`.

## 5. Step 3: compare them

```bash
python 06_cu_prebuilt_invoice.py        # Content Understanding's own prebuilt-invoice analyzer, for a like-for-like with DI's prebuilt
python 03_compare.py 0.80 easy          # score all three against ground truth -> COMPARE.md
```

`03_compare.py` takes a confidence threshold (the **human review queue** stretch goal: fields below it would go to a person)
and a document group (`easy`, `harder` or `all`). It normalizes the three different output shapes (`lib.py`) and scores:

- **Header fields correct**, with a field that should be absent counted correct only if the tool leaves it empty.
- **Line amounts found** and **invented lines** (amounts the tool returned that are not on the document).
- Time per call, when recorded.

Expect a tie on the easy set: all three score 100%.

### Harder documents

```bash
python 07_run_harder.py                 # 5 documents x 3 analyzers, records seconds per call. Needs step 2 above for the real ones
python 03_compare.py 0.80 harder        # -> COMPARE_HARDER.md
```

## 6. Step 4: the video analyzers

```bash
python 04_video_analyzer.py
```

Runs the video through (a) the prebuilt `prebuilt-videoSearch` analyzer, which splits it into segments with a description each, and
(b) a custom analyzer `safetyVideo` with your own fields (title, presenter, rules, contact extension). Outputs: `app/out/video-*.json`
and one markdown file per segment.

**Check:** the prebuilt run returns 4 segments (one per slide). The custom run returns one segment and nine rules.

## 7. Step 5: single-task mode vs pro mode

```bash
python 05_standard_vs_pro.py
```

Pro mode (multi-step reasoning, several input documents, an external knowledge base) existed only in the preview API
`2025-05-01-preview`. That API is **retired** and returns `410 Gone`, and the current API (`2025-11-01`) is standard mode only. So the
script records the 410 for the preview calls and runs the closest thing you still can: reasoning-style `generate` fields in standard
mode. Learn pro mode as a concept; you cannot run it today.

## 8. Explore everything in a web UI

```bash
streamlit run ui.py --server.address localhost
```

Always pass `--server.address localhost`: Streamlit's default exposes the app to your whole network, and the scripts run with your identity.
The UI only **reads the saved results** in `app/out/`, so it makes no Azure calls and costs nothing. It works straight after cloning because
our results are committed. Run the scripts to replace them with yours.

| Tab | What it shows |
|---|---|
| Overview | What each script did and found |
| Sources | Every file with its correct answers (the real PDFs show a download hint until you run step 2) |
| Invoices side by side | The document next to the three analyzers' fields, line items, confidence and timing. Full-screen and new-tab buttons for the PDF |
| Scorecard and review queue | Easy-set scores and a confidence slider that shows what a review queue would catch and miss |
| Harder documents | The hard and real results, speed, estimated cost, every wrong value and whether confidence flagged it |
| CU vs DI prebuilt | The two prebuilt invoice analyzers compared on measured facts |
| Video | Segment buttons that seek the player, the custom analyzer's fields, and a check of which planted facts each analyzer caught |
| Modes and limits | Standard vs pro mode and the caveats |

Restart `streamlit run` after editing `lib.py` or `theme.py`: Streamlit only reloads the main script.

## Clean up

```bash
bash scripts/99-cleanup.sh        # asks you to type the resource group name, then deletes it
```
