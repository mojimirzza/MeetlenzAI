from __future__ import annotations

import asyncio
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def package_ok(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def run_tests() -> tuple[bool, str]:
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, capture_output=True, text=True)
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()[-1200:]


async def main() -> int:
    from app.core.config import get_settings
    from app.services.llm import LLMClient
    from app.storage.db import init_db

    s = get_settings()
    init_db()
    llm = await LLMClient().health()
    deps = {name: package_ok(name) for name in ["fastapi", "uvicorn", "gradio", "httpx", "pydantic", "sqlalchemy", "numpy", "sklearn"]}
    tests_ok, tests_tail = run_tests()
    report = {
        "python": sys.version.split()[0],
        "database": {"type": "sqlite", "url": s.database_url, "status": "ready"},
        "dependencies": deps,
        "llm": llm,
        "tests": {"passed": tests_ok, "tail": tests_tail},
    }
    report["status"] = "READY" if tests_ok and all(deps.values()) and llm.get("available") else ("DEGRADED" if tests_ok and all(deps.values()) else "BLOCKED")
    import json
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] != "BLOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
