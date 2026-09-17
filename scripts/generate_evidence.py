from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "evidence"
OUT.mkdir(parents=True, exist_ok=True)

def run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=90)
    text = (p.stdout + p.stderr).strip()
    if p.returncode != 0:
        raise SystemExit(f"Command failed: {' '.join(cmd)}\n{text}")
    return text


def main() -> int:
    benchmark = run([sys.executable, "scripts/benchmark.py"])
    zero_pilot = run([sys.executable, "scripts/zero_pilot.py"])
    demo = run([sys.executable, "scripts/demo_pilot.py"])
    (OUT / "benchmark.txt").write_text(benchmark, encoding="utf-8")
    (OUT / "zero_pilot.txt").write_text(zero_pilot, encoding="utf-8")
    (OUT / "demo.txt").write_text(demo, encoding="utf-8")
    summary = {
        "evidence_level": "E2",
        "label": "controlled_synthetic_evidence",
        "artifacts": ["benchmark.txt", "zero_pilot.txt", "demo.txt"],
        "external_customer_validation": False,
    }
    (OUT / "evidence_manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
