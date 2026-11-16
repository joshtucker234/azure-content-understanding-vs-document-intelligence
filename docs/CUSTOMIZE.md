# Make it your own

The lab is deliberately small. These are the knobs and the next experiments, roughly in order of learning value.

## Settings you can change without touching much code

| What | Where | Try |
|---|---|---|
| Fields to extract | `definition` in `app/01_cu_invoice_analyzer.py` | Add `PaymentTerms`, `ShipTo`, a `Discount` line field. Each field has a `type`, a `method` (`extract`, `generate`, `classify`) and a `description`. The description is the instruction: rewrite it and re-run |
| Analyzer base | `baseAnalyzerId` | `prebuilt-document` for documents, `prebuilt-video` for video. Other base analyzers are listed in the Content Understanding docs |
| Models | `models` in the analyzer, and the deployments in `scripts/01-provision.sh` | Try `gpt-4.1-mini` as the completion model for cost, and compare accuracy |
| Confidence threshold | `python 03_compare.py <threshold> <group>`, and the slider in the UI | Find the threshold that catches the wrong fields without flooding reviewers (the UI shows both numbers) |
| Which documents count | `app/samples/*/ground-truth.json` | Add your own file and its expected values, run the three analyzers on it, re-score |
| Region | `00-env.sh` | Any Content Understanding region with the three models |

## Use your own documents

1. Put a non-sensitive invoice PDF in `app/samples/` (or `hard/`, `real/`). Do **not** use customer or confidential documents.
2. Add an entry to that folder's `ground-truth.json`: the ten header fields, plus `LineItems` with `Description`, `Quantity`, `UnitPrice`, `Amount`.
   Use `null` for a field that is not on the document (a tool that invents a value is then scored wrong), a list for several acceptable
   values (ambiguous dates), and `AmountAlt` on a line if both net and gross are reasonable.
3. Run the three analyzers on it (`07_run_harder.py <file name>` works for any non-easy file), then `python 03_compare.py 0.80 all`.
4. Label real documents by reading them yourself. Do not label them by asking one of the tools you are testing.

## Stretch exercises

- **Validate, don't trust.** Add a check that the line amounts sum to the subtotal and the subtotal plus tax equals the total. On the fax,
  this catches Document Intelligence's wrong subtotal even though its confidence was 94%. Route failures to a review queue.
- **Add audio.** The demo video is silent, so transcription was never exercised. Add narration (any text-to-speech) and mux it with the
  bundled ffmpeg (`imageio_ffmpeg.get_ffmpeg_exe()`), then see what `prebuilt-videoSearch` adds.
- **Repeat runs.** Run each document five times and measure how often the language-model-based analyzers change their answer.
- **Harder real documents.** Redacted invoices from your own work (with approval) will separate the tools far better than any synthetic file.
- **Make the net-vs-gross choice explicit.** On the real dress invoice, Content Understanding returned net line amounts and Document
  Intelligence returned gross. Work out how your downstream system should decide, and test it.
- **Price it for your volume.** Plug your page counts into the cost table in the README and decide where the crossover is.

## Where to go next

A companion project, a [keyless RAG chat app on Microsoft Foundry + Azure AI Search](https://github.com/joshtucker234/keyless-rag-azure-foundry-search), builds a RAG app
over documents with Azure AI Search. The Layout skill it uses is the same Document Intelligence capability you compared here.
