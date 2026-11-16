# Troubleshooting and gotchas

Every item below happened to us while building this.

| Symptom | Cause | Fix |
|---|---|---|
| `AuthorizationFailed` on role assignment | You are signed in as an identity with no write access (for example the managing tenant of a delegated subscription) | Sign in with the account that is Owner on the subscription |
| Resource creation denied by policy | A tag policy requires non-empty `Owner` and `Purpose` tags | Pass both (`TAGS` in `00-env.sh`) |
| `400 InvalidAnalyzerId: The 'analyzerId' cannot contain '-'` | Analyzer IDs are letters, digits and underscores | Use `invoiceFields` or `invoice_standard_ga`, not `invoice-fields` |
| `410 Gone: The requested API version has been retired` | You called `2025-05-01-preview`. Pro mode only existed there | Use GA `2025-11-01`. Pro mode cannot be run today (see `05_standard_vs_pro.py`) |
| `cu.py` exits with "Set CU_ENDPOINT first" | The endpoint comes from the environment, not the code | `source scripts/00-env.sh` in the same shell |
| 401/403 from Content Understanding or Document Intelligence | Role propagation, or you are signed in as a different identity than the one with the roles | Wait a few minutes. Needed: **Cognitive Services User** (we also granted Contributor). `az account show` to check who you are |
| Model deployment fails | The region does not offer that model as `GlobalStandard`, or no quota | `az cognitiveservices model list -l $LOC`, or pick another Content Understanding region |
| Scripts use `/tmp` or `/subscriptions/...` paths wrongly | Git Bash rewrites paths that start with `/` | `export MSYS_NO_PATHCONV=1` (in `00-env.sh`) |
| The demo video will not play in the UI | OpenCV writes MPEG-4 Part 2 (`mp4v`), which browsers cannot play | `gen_samples.py` makes an H.264 copy (`safety-briefing-web.mp4`) with `imageio-ffmpeg`. Azure analyzes the original, which is fine |
| Streamlit `StreamlitDuplicateElementId` | Two identical widgets (for example the same PDF shown on two tabs) get the same auto ID | Give each a `key=` (the UI does) |
| UI change to `lib.py` or `theme.py` does not show up | Streamlit only reloads the main script | Restart `streamlit run` |
| Streamlit is reachable from other machines | Default bind address | Always `--server.address localhost` |
| `st.pdf` shows nothing | `streamlit[pdf]` extra not installed | `pip install "streamlit[pdf]"` |
| Real-sample PDFs missing in the UI | They are third-party files and are not in the repo | `bash scripts/02-fetch-real-samples.sh` |
| `Quantity` or a decimal missing on the fax (`79.80` came back as `79`) | The fax is deliberately degraded. Content Understanding dropped characters, Document Intelligence misread digits | Not a bug. It is the point of the test. Validate totals (lines add up to the subtotal) and review low-confidence fields |
| Confidence looks "low" on correct values | Confidence scales differ by tool: the prebuilt Content Understanding analyzer averaged about 0.62 on correct values, Document Intelligence about 0.87 | Never compare confidence across tools. Set a threshold per tool on your own documents |

## Not verified

- The scripts in `scripts/` are assembled from the commands we ran and checked for syntax. **A fresh end-to-end run from the scripts
  has not been done**, so expect small fixes and send a PR. In particular `01-provision.sh` waits 60 seconds for role propagation, which
  we picked and did not tune.
- Prices are list-price estimates from the Azure retail price API at the time. Actual spend was **not** checked in Cost Management.
- Results are one run per document. Content Understanding is language-model based, so repeated runs may differ slightly.
- The scoring of Document Intelligence's customer name on the scribbled invoice (it included an "ATTN:" contact line) is a judgment call.
