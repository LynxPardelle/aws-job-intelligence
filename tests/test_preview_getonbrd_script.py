import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("preview_getonbrd", ROOT / "scripts" / "preview-getonbrd.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PreviewScriptTests(unittest.TestCase):
    def test_loads_only_alec_prepare_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "private" / "alec"
            folder.mkdir(parents=True)
            path = folder / "search-policy.active.json"
            data = {"candidate_id": "alec", "application_mode": "PREPARE",
                    "shortlist_threshold": 70, "prepare_threshold": 80,
                    "max_jobs_per_day": 10}
            path.write_text(json.dumps(data), encoding="utf-8")
            policy, quota = MODULE.load_private_policy(Path(directory))
            self.assertEqual(policy.candidate_id, "alec")
            self.assertEqual(quota, 10)
            data["application_mode"] = "AUTO_SUBMIT"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.load_private_policy(Path(directory))


if __name__ == "__main__":
    unittest.main()
