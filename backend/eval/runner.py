"""Run sample questions against a repo_id and write results."""

import json
import sys
from pathlib import Path

# Run from repo root; backend on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from rag.chains import answer_with_rag


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m eval.runner <repo_id>")
        sys.exit(1)
    repo_id = sys.argv[1]
    questions_path = Path(__file__).parent / "sample_questions.json"
    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    results = []
    for q in questions:
        try:
            out = answer_with_rag(repo_id, q)
            cited = 1 if out.get("evidence") else 0
            results.append({"question": q, "summary": (out.get("summary") or "")[:200], "cited": cited})
        except Exception as e:
            results.append({"question": q, "error": str(e), "cited": 0})
    cited_count = sum(r.get("cited", 0) for r in results)
    print(f"Citation coverage: {cited_count}/{len(results)}")
    out_path = Path(__file__).parent / "results.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
