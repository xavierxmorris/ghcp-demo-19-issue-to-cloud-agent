from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

from issue_agent.cli import observe
from issue_agent.contracts import BOT, ContractError
from issue_agent.github_api import paginated
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
            "id": 12345,
            "html_url": f"https://github.com/{REPO}/pull/2",
            "draft": True, "merged": False, "head": {"sha": "b" * 40},
        }
        self.task = {
            "id": "synthetic-task", "state": "in_progress",
            "artifacts": [{"provider": "github", "type": "pull", "data": {"id": 12345}}],
            "session_count": 1,
            "sessions": [{
                "id": "synthetic-test-session", "task_id": "synthetic-task",
                "state": "in_progress", "model": "synthetic-test-model",
                "created_at": "2026-01-01T00:00:00Z", "completed_at": None,
                "prompt": "EXCLUDED_TEST_PROMPT", "usage": {"amount": 999, "type": "ai_credits"},
            }],
        }
        self.archived = False
        self.hide_task = False
        self.extra_tasks = []
        self.detail_identity = None

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
        if path.startswith(f"/agents/repos/{REPO}/tasks?"):
            selected = ("is_archived=true" in path) == self.archived
            tasks = [self.task, *self.extra_tasks] if selected and not self.hide_task else []
            return {"tasks": [copy.deepcopy({k: v for k, v in task.items() if k != "sessions"}) for task in tasks]}
        if path == f"/agents/repos/{REPO}/tasks/synthetic-task":
            detail = copy.deepcopy(self.task)
            if self.detail_identity is not None:
                detail["id"] = self.detail_identity
            return detail
        raise AssertionError(path)


class ObserveTests(unittest.TestCase):
    def setUp(self):
        self.api = ObservationApi()
        self.session = self.api.task["sessions"][0]
        self.evidence = Evidence("observe", REPO)

    def run_observer(self):
        with patch("issue_agent.cli.GhApi", return_value=self.api):
            observe(REPO, 1, self.evidence)

    def test_real_shaped_session_is_separate_from_assignment_and_acceptance(self):
        self.run_observer()
        self.assertTrue(self.evidence.assignment_verified)
        self.assertTrue(self.evidence.agent_execution_observed)
        self.assertEqual(self.evidence.pull_requests[0]["session_id"], "synthetic-test-session")
        self.assertEqual(self.evidence.migrated_pipeline_definitions, 0)
        self.assertEqual(self.evidence.mutations, [])
        self.assertFalse(self.evidence.pull_requests[0]["merged"])
        self.assertEqual(self.evidence.pull_requests[0]["task_id"], "synthetic-task")
        self.assertEqual(self.evidence.pull_requests[0]["model"], "synthetic-test-model")
        self.assertNotIn("EXCLUDED_TEST_PROMPT", str(self.evidence.json()))
        self.assertNotIn("ai_credits", str(self.evidence.json()))
        self.assertTrue(all(method == "GET" for method, _ in self.api.calls))

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
                with patch("issue_agent.cli.GhApi", return_value=self.api):
                    observe(REPO, 1, self.evidence)
                self.assertFalse(self.evidence.agent_execution_observed)
                self.assertEqual(self.evidence.pull_requests, [])
                self.assertFalse(any(path.startswith("/agents/") for _, path in self.api.calls))

    def test_mismatched_session_identity_is_an_explicit_error(self):
        self.session["task_id"] = "different-task"
        with self.assertRaisesRegex(ContractError, "different task"):
            self.run_observer()
        self.assertFalse(self.evidence.agent_execution_observed)

    def test_archived_task_is_still_observable(self):
        self.api.archived = True
        self.session["state"] = "completed"
        self.run_observer()
        self.assertTrue(self.evidence.agent_execution_observed)

    def test_task_without_a_session_is_not_execution_proof(self):
        self.api.task["session_count"] = 0
        self.api.task["sessions"] = []
        self.api.task["state"] = "queued"
        self.run_observer()
        self.assertFalse(self.evidence.agent_execution_observed)
        self.assertEqual(self.evidence.pull_requests[0]["task_state"], "queued")
        self.assertNotIn("session_id", self.evidence.pull_requests[0])

    def test_latest_session_uses_actual_timestamps_not_lexical_dates(self):
        self.api.task["session_count"] = 2
        self.api.task["sessions"].append({
            **self.session, "id": "later-session", "created_at": "2025-12-31T23:30:00-02:00",
            "state": "completed",
        })
        self.run_observer()
        self.assertEqual(self.evidence.pull_requests[0]["session_id"], "later-session")

    def test_missing_task_keeps_the_observed_pr_as_partial_evidence(self):
        self.api.hide_task = True
        with self.assertRaisesRegex(ContractError, "observed 0"):
            self.run_observer()
        self.assertEqual(self.evidence.pull_requests[0]["url"], self.api.pr["html_url"])
        self.assertFalse(self.evidence.agent_execution_observed)

    def test_multiple_tasks_are_not_silently_collapsed(self):
        self.api.extra_tasks = [{**self.api.task, "id": "another-task"}]
        with self.assertRaisesRegex(ContractError, "observed 2"):
            self.run_observer()

    def test_mismatched_task_detail_is_rejected(self):
        self.api.detail_identity = "another-task"
        with self.assertRaisesRegex(ContractError, "identities disagree"):
            self.run_observer()

    def test_incomplete_session_list_is_rejected(self):
        self.api.task["session_count"] = 2
        with self.assertRaisesRegex(ContractError, "complete session evidence"):
            self.run_observer()

    def test_failed_session_retains_error_without_claiming_execution(self):
        self.session["state"] = "failed"
        self.session["error"] = {"message": "Synthetic runner failure"}
        self.run_observer()
        self.assertFalse(self.evidence.agent_execution_observed)
        self.assertEqual(self.evidence.pull_requests[0]["session_error"], "Synthetic runner failure")

    def test_task_envelope_pagination_has_the_same_hard_limit(self):
        class ManyTasks:
            def request(self, method, path, body=None):
                return {"tasks": [{}] * 100}
        with self.assertRaisesRegex(ContractError, "incomplete"):
            paginated(ManyTasks(), f"/agents/repos/{REPO}/tasks", "tasks")
