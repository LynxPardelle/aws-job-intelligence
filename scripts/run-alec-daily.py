"""One safe daily command for Alec's AWS pull and local review preparation."""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aji.daily_orchestrator import (StepResult, compact_report, run_daily,
                                    save_daily_report)  # noqa: E402


_TIMEOUTS = {
    "preflight": 30, "budget": 45, "source_health": 45,
    "batch_preview": 60, "getonbrd_preview": 120, "prepare": 240,
}
_MAX_STDOUT_BYTES = 1_000_000


def python_for_children(root: Path) -> str:
    relative = Path("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    project_python = Path(root) / ".venv" / relative
    return str(project_python) if project_python.is_file() else sys.executable


def command_for_step(step: str, root: Path, python_executable: str) -> list[str]:
    scripts = Path(root) / "scripts"
    if step == "preflight":
        return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                str(scripts / "check-aws-local.ps1")]
    names = {
        "budget": "check-budget.py",
        "source_health": "check-source-health.py",
        "batch_preview": "run-alec-pull.py",
        "getonbrd_preview": "preview-getonbrd.py",
        "prepare": "run-alec-pull.py",
    }
    if step not in names:
        raise ValueError("unsupported daily step")
    command = [python_executable, str(scripts / names[step])]
    if step == "prepare":
        command.append("--prepare")
    return command


def invoke(step: str) -> StepResult:
    command = command_for_step(step, ROOT, python_for_children(ROOT))
    child_environment = os.environ.copy()
    child_environment["PYTHONIOENCODING"] = "utf-8"
    try:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True,
                                   timeout=_TIMEOUTS[step], env=child_environment)
    except subprocess.TimeoutExpired:
        return StepResult(2, {"error_code": "STEP_TIMEOUT"})
    except OSError:
        return StepResult(2, {"error_code": "STEP_FAILED"})
    if step == "preflight":
        return StepResult(completed.returncode, None)
    if len(completed.stdout) > _MAX_STDOUT_BYTES:
        return StepResult(2, {"error_code": "STEP_OUTPUT_TOO_LARGE"})
    try:
        payload = json.loads(completed.stdout)
    except (ValueError, UnicodeError):
        payload = {"error_code": "STEP_INVALID_OUTPUT"}
    if not isinstance(payload, dict):
        payload = {"error_code": "STEP_INVALID_OUTPUT"}
    return StepResult(completed.returncode, payload)


def main() -> int:
    report = run_daily(datetime.now(timezone.utc).isoformat(), invoke)
    destination = ROOT / "applications" / "alec" / "daily-report.json"
    try:
        save_daily_report(destination, report)
    except OSError:
        print(json.dumps({"status": "ERROR", "candidate_id": "alec",
                          "local_day": report["local_day"],
                          "error_code": "DAILY_REPORT_IO_ERROR"}))
        return 2
    print(json.dumps(compact_report(report), ensure_ascii=True, indent=2))
    return 2 if report["status"] == "ERROR" else 0


if __name__ == "__main__":
    raise SystemExit(main())
