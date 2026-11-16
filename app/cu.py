"""Tiny keyless REST helper for Content Understanding and Document Intelligence (same Foundry resource).
Auth: Entra token via DefaultAzureCredential (no keys). Set CU_ENDPOINT, e.g. https://<name>.cognitiveservices.azure.com"""
import os, time, json, mimetypes
from pathlib import Path
import requests
from azure.identity import DefaultAzureCredential

ENDPOINT = os.environ.get("CU_ENDPOINT", "").rstrip("/")
if not ENDPOINT:
    raise SystemExit("Set CU_ENDPOINT first, e.g. source scripts/00-env.sh (https://<your-foundry-resource>.cognitiveservices.azure.com)")
CU_API = "2025-11-01"
DI_API = "2024-11-30"
_cred = DefaultAzureCredential()

def _hdr(content_type="application/json"):
    tok = _cred.get_token("https://cognitiveservices.azure.com/.default").token
    return {"Authorization": f"Bearer {tok}", "Content-Type": content_type}

def _poll(resp, timeout=600):
    """Follow an async operation (202 + Operation-Location) until it finishes; return the final JSON."""
    if resp.status_code >= 400:
        raise RuntimeError(f"HTTP {resp.status_code} {resp.request.method} {resp.url.split('?')[0]}: {resp.text[:600]}")
    url = resp.headers.get("Operation-Location")
    if not url:
        return resp.json() if resp.content else {}
    t0 = time.time()
    while True:
        r = requests.get(url, headers=_hdr()); r.raise_for_status(); j = r.json()
        status = (j.get("status") or "").lower()
        if status in ("succeeded", "failed", "canceled"):
            if status != "succeeded": raise RuntimeError(json.dumps(j.get("error", j))[:800])
            return j
        if time.time() - t0 > timeout: raise TimeoutError(url)
        time.sleep(3)

# ---- Content Understanding ----
def cu_put_analyzer(analyzer_id, definition, api=CU_API):
    r = requests.put(f"{ENDPOINT}/contentunderstanding/analyzers/{analyzer_id}?api-version={api}&allowReplace=true",
                     headers=_hdr(), json=definition)
    return _poll(r)

def cu_analyze_file(analyzer_id, path, api=CU_API):
    path = Path(path)
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    r = requests.post(f"{ENDPOINT}/contentunderstanding/analyzers/{analyzer_id}:analyzeBinary?api-version={api}",
                      headers=_hdr(ctype), data=path.read_bytes())
    return _poll(r)

def cu_delete_analyzer(analyzer_id):
    return requests.delete(f"{ENDPOINT}/contentunderstanding/analyzers/{analyzer_id}?api-version={CU_API}", headers=_hdr()).status_code

# ---- Document Intelligence ----
def di_analyze_file(model_id, path):
    path = Path(path)
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    r = requests.post(f"{ENDPOINT}/documentintelligence/documentModels/{model_id}:analyze?api-version={DI_API}",
                      headers=_hdr(ctype), data=path.read_bytes())
    return _poll(r)
