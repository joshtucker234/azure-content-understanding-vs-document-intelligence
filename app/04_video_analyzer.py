"""Step 4: video analysis. Runs (a) the prebuilt video search analyzer and (b) a custom video analyzer with our own fields.
Saves raw JSON and the markdown each one produces (used for step 5 comparison)."""
import json, sys
from pathlib import Path
import cu

OUT = Path("out"); OUT.mkdir(exist_ok=True)
VIDEO = Path(sys.argv[1] if len(sys.argv) > 1 else "samples/safety-briefing.mp4")

def f(desc, typ="string", method="generate"):
    return {"type": typ, "method": method, "description": desc}

custom = {
    "description": "Custom safety-briefing video analyzer",
    "baseAnalyzerId": "prebuilt-video",
    "config": {"returnDetails": True},
    "fieldSchema": {
        "name": "SafetyBriefing",
        "fields": {
            "Title": f("Title of the briefing"),
            "Presenter": f("Name and role of the presenter, if shown"),
            "Summary": f("Two sentence summary of the video"),
            "Rules": {"type": "array", "method": "generate", "description": "Each safety rule presented, one short sentence each",
                      "items": {"type": "string"}},
            "ContactExtension": f("Phone extension to report spills, if shown"),
        },
    },
    "models": {"completion": "gpt-4.1", "embedding": "text-embedding-3-large"},
}

if __name__ == "__main__":
    cu.cu_put_analyzer("safetyVideo", custom)
    for aid in ("prebuilt-videoSearch", "safetyVideo"):
        print(f"\n== {aid} on {VIDEO.name}")
        res = cu.cu_analyze_file(aid, VIDEO)
        (OUT / f"video-{aid}.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
        contents = res["result"]["contents"]
        print(f"  segments returned: {len(contents)}")
        for i, c in enumerate(contents):
            md = c.get("markdown", "")
            (OUT / f"video-{aid}-seg{i}.md").write_text(md, encoding="utf-8")
            fields = c.get("fields", {})
            print(f"  [{i}] {c.get('startTimeMs')}-{c.get('endTimeMs')} ms, markdown {len(md)} chars, fields: {list(fields)}")
            if "Summary" in fields: print("      Summary:", fields["Summary"].get("valueString"))
            if "Description" in fields: print("      Description:", (fields["Description"].get("valueString") or "")[:300])
