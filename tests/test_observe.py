from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

from issue_agent.cli import observe
from issue_agent.contracts import BOT, ContractError
from issue_agent.service import Evidence
from test_service import PREFIX, REPO, fixture_issue


class ObservationApi:
    def __init__(self):
        self.calls = []
        self.issue = fixture_issue()
        self.issue["assignees"] = [{"login": BOT}]
        self.linked = {
            "number": 2, "repository_url": "https://api.github.com" + PREFIX,
            "pull_request": {}, "user": {"login": BOT},
        }
        self.pr = {
            "html_url": f"https://github.com/{REPO}/pull/2",
            "draft": True, "merged": False, "head": {"sha": "b" * 40},
        }

    def request(self, method, path, body=None):
        self.calls.append((method, path))
        if method != "GET":
            raise AssertionError("Observation must never mutate")
        if path.endswith("/issues/1"):
            return copy.deepcopy(self.issue)
        if "/timeline?" in path:
            return [{"event": "cross-referenced", "source": {"issue": copy.deepcopy(self.linked)}}]
        if path.endswith("/pulls/2"):
            return copy.deepcopy(self.pr)
        raise AssertionError(path)


class ObserveTests(unittest.TestCase):
    def setUp(self):
        self.api = ObservationApi()
        self.session = {
            "id": "synthetic-test-session", "state": "in_progress",
            "pullRequestUrl": f"https://github.com/{REPO}/pull/2",
            "createdAt": "2026-01-01T00:00:00Z", "completedAt": None,
        }
        self.evidence = Evidence("observe", REPO)

    def run_observer(self):
        with patch("issue_agent.cli.GhApi", return_value=self.api), \
                patch("issue_agent.cli.gh_json", return_value=self.session):
            observe(REPO, 1, self.evidence)

    def test_real_shaped_session_is_separate_from_assignment_and_acceptance(self):
        self.run_observer()
        self.assertTrue(self.evidence.assignment_verified)
        self.assertTrue(self.evidence.agent_execution_observed)
        self.assertEqual(self.evidence.pull_requests[0]["session_id"], "synthetic-test-session")
        self.assertEqual(self.evidence.migrated_pipeline_definitions, 0)
        self.assertEqual(self.evidence.mutations, [])
        self.assertFalse(self.evidence.pull_requests[0]["merged"])

    def test_queued_task_and_existing_pr_do_not_claim_agent_execution(self):
        self.session["state"] = "queued"
        self.run_observer()
        self.assertEqual(self.evidence.state, "linked-pr-observed")
        self.assertFalse(self.evidence.agent_execution_observed)

    def test_foreign_or_human_pr_is_not_cloud_task_proof(self):
        for field, value in (
            ("repository_url", "https://api.github.com/repos/other/repo"),
            ("user", {"login": "human"}),
        ):
            with self.subTest(field=field):
                self.api = ObservationApi()
                self.api.linked[field] = value
                self.evidence = Evidence("observe", REPO)
                with patch("issue_agent.cli.GhApi", return_value=self.api), \
                        patch("issue_agent.cli.gh_json", side_effect=AssertionError("not an agent PR")):
                    observe(REPO, 1, self.evidence)
                self.assertFalse(self.evidence.agent_execution_observed)
                self.assertEqual(self.evidence.pull_requests, [])

    def test_mismatched_session_identity_is_an_explicit_error(self):
        self.session["pullRequestUrl"] = "https://github.com/other/repo/pull/2"
        with self.assertRaisesRegex(ContractError, "identities disagree"):
            self.run_observer()
        self.assertFalse(self.evidence.agent_execution_observed)
