import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("run_alec_daily", ROOT / "scripts" /
                                               "run-alec-daily.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DailyScriptTests(unittest.TestCase):
    def test_child_python_prefers_project_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(MODULE.python_for_children(root), MODULE.sys.executable)
            child = root / ".venv" / ("Scripts/python.exe" if MODULE.sys.platform == "win32"
                                      else "bin/python")
            child.parent.mkdir(parents=True)
            child.touch()
            self.assertEqual(MODULE.python_for_children(root), str(child))

    def test_invoke_forces_utf8_for_unicode_json(self):
        payload = {"status": "READY", "title": "Trabajo remoto en México"}
        completed = SimpleNamespace(returncode=0,
                                    stdout=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                    stderr=b"")
        with patch.object(MODULE.subprocess, "run", return_value=completed) as run:
            result = MODULE.invoke("getonbrd_preview")

        self.assertEqual(result.payload, payload)
        self.assertEqual(run.call_args.kwargs["env"]["PYTHONIOENCODING"], "utf-8")
        self.assertEqual(run.call_args.args[0][0], MODULE.python_for_children(ROOT))

    def test_fixed_commands_never_claim_or_submit(self):
        steps = ("preflight", "budget", "source_health", "batch_preview",
                 "getonbrd_preview", "prepare")
        commands = [MODULE.command_for_step(name, ROOT, "python-fixture") for name in steps]

        self.assertEqual(commands[-1][-1], "--prepare")
        self.assertTrue(all("--claim" not in command for command in commands))
        self.assertTrue(all("submit" not in " ".join(command).lower() for command in commands))
        self.assertEqual(commands[1][-1], str(ROOT / "scripts" / "check-budget.py"))
        with self.assertRaises(ValueError):
            MODULE.command_for_step("unknown", ROOT, "python-fixture")


if __name__ == "__main__":
    unittest.main()
