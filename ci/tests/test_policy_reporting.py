"""Exercise the workflow's actual reporting script without GitHub writes."""

import json
from pathlib import Path
import subprocess
import unittest

import yaml


WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/ci.yml"

HARNESS = r"""
const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const calls = [];
const summary = [];
const warnings = [];
const context = { repo: { owner: 'test', repo: 'patchwork' }, issue: { number: 18 } };
const core = {
  summary: {
    addRaw(body) { summary.push(body); return this; },
    async write() {},
  },
  warning(message) { warnings.push(message); },
};
const comments = input.existing ? [
  { id: 42, user: { login: 'github-actions[bot]' }, body: '<!-- kpatchwork-auto-merge-status -->' },
] : [];
const github = { rest: { issues: {
  async listComments() {
    if (input.failAt === 'list') throw Object.assign(new Error('API error'), { status: input.status });
    return { data: comments };
  },
  async createComment(args) {
    if (input.failAt === 'create') throw Object.assign(new Error('API error'), { status: input.status });
    calls.push({ action: 'create', ...args });
  },
  async updateComment(args) {
    if (input.failAt === 'update') throw Object.assign(new Error('API error'), { status: input.status });
    calls.push({ action: 'update', ...args });
  },
} } };
process.env.REASON = 'pack.yml: contributer field changed';
const AsyncFunction = Object.getPrototypeOf(async function() {}).constructor;
(async () => {
  let error = null;
  try { await new AsyncFunction('github', 'context', 'core', input.script)(github, context, core); }
  catch (caught) { error = { message: caught.message, status: caught.status }; }
  console.log(JSON.stringify({ calls, summary, warnings, error }));
})();
"""


class PolicyReportingTests(unittest.TestCase):
    def setUp(self):
        self.job = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["report-pack-policy"]

    def report(self, **options):
        script = self.job["steps"][0]["with"]["script"]
        result = subprocess.run(
            ["node", "-e", HARNESS],
            input=json.dumps({"script": script, **options}),
            capture_output=True, text=True, check=True, timeout=10,
        )
        return json.loads(result.stdout)

    def test_report_job_has_pull_request_write_permission(self):
        self.assertEqual(self.job["permissions"].get("pull-requests"), "write")

    def test_creates_comment_and_preserves_reason_in_summary(self):
        result = self.report()
        self.assertIsNone(result["error"])
        self.assertEqual(result["calls"][0]["action"], "create")
        self.assertEqual(result["calls"][0]["issue_number"], 18)
        self.assertIn("contributer field changed", "".join(result["summary"]))

    def test_updates_existing_bot_comment(self):
        result = self.report(existing=True)
        self.assertIsNone(result["error"])
        self.assertEqual(result["calls"][0]["action"], "update")
        self.assertEqual(result["calls"][0]["comment_id"], 42)

    def test_forbidden_reporting_warns_without_failing_ci(self):
        for operation in ("list", "create", "update"):
            with self.subTest(operation=operation):
                result = self.report(failAt=operation, status=403, existing=operation == "update")
                self.assertIsNone(result["error"])
                self.assertTrue(result["warnings"])
                self.assertIn("contributer field changed", "".join(result["summary"]))

    def test_unexpected_api_errors_still_fail(self):
        result = self.report(failAt="create", status=500)
        self.assertEqual(result["error"]["status"], 500)


if __name__ == "__main__":
    unittest.main()
