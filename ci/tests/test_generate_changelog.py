"""Test release notes through the CLI against real Git history."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


GENERATOR = Path(__file__).resolve().parents[1] / "generate_changelog.py"


class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "-q")
        self.commit("Initial packs", {
            "KPatchwork.uplugin": json.dumps({"VersionName": "1.2.3"}),
            "DataForge/MkPlusSFPlus/pack.yml": "name: MkPlusSFPlus Pack\nref: MkPlusSFPlus\ncontributer: alice\n",
        })
        self.base = self.git("rev-parse", "HEAD")

    def git(self, *args):
        env = {**os.environ, "GIT_AUTHOR_NAME": "Test Author", "GIT_AUTHOR_EMAIL": "test@example.com",
               "GIT_COMMITTER_NAME": "Test Author", "GIT_COMMITTER_EMAIL": "test@example.com"}
        return subprocess.run(
            ["git", "-C", str(self.root), *args], env=env,
            text=True, capture_output=True, check=True, timeout=10,
        ).stdout.strip()

    def commit(self, subject, files):
        for name, content in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", subject)
        return self.git("rev-parse", "HEAD")

    def generate(self, records=None):
        output = self.root / "release.md"
        command = [sys.executable, str(GENERATOR), "--root", str(self.root),
                   "--base", self.base, "--head", "HEAD", "--output", str(output)]
        if records is not None:
            records_path = self.root / "pulls.json"
            records_path.write_text(json.dumps(records), encoding="utf-8")
            command.extend(["--pull-requests", str(records_path)])
        subprocess.run(command, text=True, capture_output=True, check=True, timeout=20)
        return output.read_text(encoding="utf-8")

    def test_pack_changes_appear_once_without_template_filler(self):
        subjects = ["Updated MkPlusSFPlus Pack", "Updated ProgPrintersSFPlus Pack",
                    "Added missing costs for Base Tech Augmentation",
                    "Cleaned up MkPlusSFPlus, Added NukeRebarSFPlus"]
        for index, subject in enumerate(subjects):
            self.commit(subject, {f"DataForge/MkPlusSFPlus/patch{index}.yml": f"value: {index}\n"})
        result = self.generate()
        for subject in subjects:
            self.assertEqual(result.count(subject + "."), 1)
        self.assertNotIn("Changes for pack authors", result)
        self.assertNotIn("KDataForge patch content", result)
        self.assertNotIn("Updated missing costs", result)

    def test_empty_sections_and_generation_preamble_are_omitted(self):
        self.commit("Add missing costs", {"DataForge/MkPlusSFPlus/costs.yml": "value: 1\n"})
        result = self.generate()
        self.assertTrue(result.startswith("# Patchwork:"))
        self.assertNotIn("## New packs", result)
        self.assertNotIn("No pack author changelogs", result)
        self.assertNotIn("No new packs", result)

    def test_authored_notes_replace_only_their_covered_commits(self):
        covered = self.commit("fix: restore Base Tech Augmentation costs", {
            "DataForge/MkPlusSFPlus/costs.yml": "value: 1\n"})
        self.commit("Add Nuclear Rebar support", {"DataForge/MkPlusSFPlus/rebar.yml": "value: 2\n"})
        result = self.generate([{
            "number": 18, "author": "alice", "title": "Pack updates",
            "url": "https://github.com/example/repo/pull/18", "commits": [covered],
            "body": "## Changelog\n\n- Base Tech Augmentation recipes have their missing costs again.\n\n## Validation\nPassed",
        }])
        self.assertIn("Base Tech Augmentation recipes have their missing costs again.", result)
        self.assertNotIn("restore Base Tech Augmentation costs", result)
        self.assertIn("Added Nuclear Rebar support.", result)
        self.assertIn("[#18](https://github.com/example/repo/pull/18)", result)
        self.assertNotIn("Passed", result)

    def test_empty_authored_notes_leave_commit_fallback(self):
        covered = self.commit("Fix recipe costs", {"DataForge/MkPlusSFPlus/costs.yml": "value: 1\n"})
        result = self.generate([{"number": 18, "commits": [covered],
                                "body": "## Changelog\n<!-- Optional notes -->\n## Validation\nPassed"}])
        self.assertIn("Fixed recipe costs.", result)

    def test_duplicate_commit_subjects_are_listed_once(self):
        self.commit("Fix recipe costs", {"DataForge/MkPlusSFPlus/costs.yml": "value: 1\n"})
        self.commit("fix: recipe costs.", {"DataForge/MkPlusSFPlus/costs.yml": "value: 2\n"})
        self.assertEqual(self.generate().count("Fixed recipe costs."), 1)

    def test_tooling_changes_have_their_own_nonduplicated_section(self):
        self.commit("Fix recipe costs", {"DataForge/MkPlusSFPlus/costs.yml": "value: 1\n"})
        self.commit("fix: contributor list validation", {"ci/policy.py": "# test\n"})
        result = self.generate()
        self.assertIn("## For pack authors", result)
        players, authors = result.split("## For pack authors")
        self.assertIn("Fixed recipe costs.", players)
        self.assertNotIn("Fixed recipe costs.", authors)
        self.assertIn("Fixed contributor list validation.", authors)

    def test_new_pack_names_and_contributors_remain(self):
        self.commit("Add Nuclear Rebar pack", {"DataForge/NukeRebarSFPlus/pack.yml":
                    "name: Nuclear Rebar\nref: NukeRebarSFPlus\ncontributer: [alice, bob]\n"})
        result = self.generate()
        self.assertIn("## New packs", result)
        self.assertIn("Nuclear Rebar", result)
        self.assertIn("`NukeRebarSFPlus`", result)
        self.assertIn("@alice and @bob", result)
        self.assertNotIn("## Updated packs", result)

    def test_ordinary_subject_is_not_given_an_invented_action(self):
        self.commit("Cleaner recipes use less water.", {"DataForge/MkPlusSFPlus/cleaner.yml": "value: 1\n"})
        result = self.generate()
        self.assertIn("- Cleaner recipes use less water.\n", result)
        self.assertNotIn("Updated Cleaner", result)
        self.assertNotIn("water..", result)


if __name__ == "__main__":
    unittest.main()
