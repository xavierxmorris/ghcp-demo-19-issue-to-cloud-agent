from __future__ import annotations

import base64
import copy
import unittest

from issue_agent.contracts import (
    ASSIGNED_LABEL, BOT, HARNESS_WORKFLOWS, QUEUE_LABEL, SOURCE_TEXT,
    START_LABEL, TITLE, ContractError, issue_body,
)
from issue_agent.github_api import ApiError, paginated
from issue_agent.service import Evidence, start_from_event, submit_request

REPO = "demo-owner/hello-world"
SHA = "a" * 40
PREFIX = "/repos/" + REPO


def fixture_issue(number=1):
    return {
        "number": number, "repository_url": "https://api.github.com" + PREFIX,
        "title": TITLE, "body": issue_body(SHA), "state": "open",
        "user": {"login": "demo-owner", "type": "User"},
        "labels": [{"name": QUEUE_LABEL}], "assignees": [], "comments": 0,
    }


class ControlApi:
    def __init__(self):
        self.issue = fixture_issue()
        self.extra = []
        self.calls = []
        self.fail_marker = False
        self.fail_status = False
        self.change_during_preflight = False
        self.issue_reads = 0
        self.variable = "true"
        self.actor = "demo-owner"
        self.head = SHA
        self.metadata = {
            "full_name": REPO, "owner": {"type": "User"},
            "archived": False, "disabled": False, "default_branch": "main",
        }
        self.tree = {
            "truncated": False,
            "tree": [
                {"path": "Jenkinsfile", "type": "blob", "mode": "100644"},
                *[{"path": name, "type": "blob", "mode": "100644"} for name in sorted(HARNESS_WORKFLOWS)],
            ],
        }
        self.content = {
            "type": "file", "encoding": "base64", "size": len(SOURCE_TEXT.encode()),
            "content": base64.b64encode(SOURCE_TEXT.encode()).decode(),
        }
        self.ledger_contains_current = True

    def request(self, method, path, body=None):
        self.calls.append((method, path, copy.deepcopy(body)))
        if method == "GET":
            if path == "/user":
                return {"login": self.actor}
            if path.endswith("/actions/variables/ISSUE_AGENT_ENABLED"):
                return {"value": self.variable}
            if path == PREFIX:
                return copy.deepcopy(self.metadata)
            if path.endswith("/git/ref/heads/main"):
                return {"object": {"type": "commit", "sha": self.head}}
            if "/git/trees/" in path:
                return copy.deepcopy(self.tree)
            if "/contents/Jenkinsfile?" in path:
                return copy.deepcopy(self.content)
            if path.endswith("/issues/1"):
                self.issue_reads += 1
                if self.issue_reads == 2 and self.change_during_preflight:
                    self.issue["comments"] = 1
                return copy.deepcopy(self.issue)
            if "/issues?state=all" in path:
                return copy.deepcopy(([self.issue] if self.ledger_contains_current else []) + self.extra)
        if method == "POST" and path.endswith("/issues"):
            self.issue = fixture_issue(2)
            self.issue.update(body)
            self.issue["labels"] = [{"name": value} for value in body["labels"]]
            return copy.deepcopy(self.issue)
        if method == "POST" and path.endswith("/labels"):
            label = body["labels"][0]
            if (label == START_LABEL and self.fail_marker) or (label == ASSIGNED_LABEL and self.fail_status):
                raise ApiError("Synthetic label write failure")
            self.issue["labels"].append({"name": label})
            return copy.deepcopy(self.issue["labels"])
        raise AssertionError(f"Unexpected control call: {method} {path}")


class UserApi:
    def __init__(self, control):
        self.control = control
        self.calls = []
        self.available = True
        self.fail_assignment = False
        self.accept_then_timeout = False
        self.ignore_assignment = False
        self.assignment_count = 0

    def request(self, method, path, body=None):
        self.calls.append((method, path, copy.deepcopy(body)))
        if path == "/graphql":
            return {"data": {"repository": {"suggestedActors": {
                "nodes": [{"login": "copilot-swe-agent"}] if self.available else [],
                "pageInfo": {"hasNextPage": False},
            }}}}
        if method == "POST" and path.endswith("/assignees"):
            self.assignment_count += 1
            if self.fail_assignment:
                raise ApiError("Synthetic HTTP 403")
            if not self.ignore_assignment:
                self.control.issue["assignees"] = [{"login": BOT}]
            if self.accept_then_timeout:
                raise ApiError("Synthetic timeout after acceptance")
            return copy.deepcopy(self.control.issue)
        raise AssertionError(f"Unexpected user call: {method} {path}")


class TriggerTests(unittest.TestCase):
    def setUp(self):
        self.control = ControlApi()
        self.user = UserApi(self.control)
        self.event = {
            "action": "opened", "repository": {"full_name": REPO},
            "issue": copy.deepcopy(self.control.issue),
        }
        self.evidence = Evidence("trigger", REPO)

    def start(self, **overrides):
        kwargs = dict(enabled=True, event_name="issues", workflow_ref="refs/heads/main", workflow_commit=SHA)
        kwargs.update(overrides)
        start_from_event(self.event, REPO, self.control, self.user, self.evidence, **kwargs)

    def assert_no_assignment(self):
        self.assertEqual(self.user.assignment_count, 0)
        self.assertFalse(self.evidence.assignment_attempted)

    def test_opening_one_valid_issue_assigns_with_the_user_identity_only(self):
        self.start()
        self.assertEqual(self.evidence.state, "assignment-verified")
        self.assertTrue(self.evidence.assignment_verified)
        self.assertFalse(self.evidence.agent_execution_observed)
        self.assertEqual(self.evidence.migrated_pipeline_definitions, 0)
        self.assertEqual(self.user.assignment_count, 1)
        self.assertTrue(all(not path.endswith("/assignees") for _, path, _ in self.control.calls))
        self.assertEqual([path for _, path, _ in self.user.calls], ["/graphql", PREFIX + "/issues/1/assignees"])

    def test_already_assigned_rerun_is_a_noop(self):
        self.start()
        before = len(self.control.calls)
        self.evidence = Evidence("trigger", REPO)
        self.start()
        self.assertEqual(self.evidence.state, "already-assigned")
        self.assertEqual(self.evidence.mutations, [])
        self.assertEqual(self.user.assignment_count, 1)
        self.assertTrue(all(method == "GET" for method, _, _ in self.control.calls[before:]))

    def test_disabled_untrusted_ref_and_other_events_refuse_before_reads(self):
        for options in (
            {"enabled": False}, {"event_name": "issue_comment"},
            {"workflow_ref": "refs/heads/untrusted"},
        ):
            with self.subTest(options=options), self.assertRaises(ContractError):
                self.start(**options)
        self.assertEqual(self.control.calls, [])
        self.assert_no_assignment()

    def test_repository_mismatch_is_rejected(self):
        self.event["repository"]["full_name"] = "other/repo"
        with self.assertRaisesRegex(ContractError, "repository"):
            self.start()
        self.assertEqual(self.control.calls, [])

    def test_controller_revision_must_match_source_revision(self):
        with self.assertRaisesRegex(ContractError, "workflow commit"):
            self.start(workflow_commit="b" * 40)
        self.assertEqual(self.control.calls, [])

    def test_non_owner_cannot_trigger_a_public_repo_task(self):
        self.event["issue"]["user"]["login"] = "someone-else"
        with self.assertRaisesRegex(ContractError, "owner"):
            self.start()
        self.assertEqual(self.control.calls, [])

    def test_edited_title_body_closed_pr_or_missing_label_cannot_start(self):
        for key, value in (
            ("title", "Changed"), ("body", issue_body(SHA) + "extra"),
            ("state", "closed"), ("pull_request", {}),
            ("labels", []), ("comments", 1), ("assignees", [{"login": "human"}]),
        ):
            with self.subTest(key=key):
                self.control.issue = fixture_issue()
                self.control.issue[key] = value
                with self.assertRaises(ContractError):
                    self.start()
                self.assert_no_assignment()

    def test_stale_source_is_rejected(self):
        self.control.head = "b" * 40
        with self.assertRaisesRegex(ContractError, "stale"):
            self.start()
        self.assert_no_assignment()

    def test_truncated_tree_is_not_a_candidate(self):
        self.control.tree["truncated"] = True
        with self.assertRaisesRegex(ContractError, "truncated"):
            self.start()
        self.assert_no_assignment()

    def test_missing_or_multiple_jenkinsfiles_fail_closed(self):
        original = copy.deepcopy(self.control.tree)
        for paths in ([], ["other/Jenkinsfile"], ["unknown.Jenkinsfile"]):
            with self.subTest(paths=paths):
                self.control.tree = copy.deepcopy(original)
                if not paths:
                    self.control.tree["tree"] = self.control.tree["tree"][1:]
                else:
                    self.control.tree["tree"].append({"path": paths[0], "type": "blob", "mode": "100644"})
                with self.assertRaisesRegex(ContractError, "Exactly one"):
                    self.start()
                self.assert_no_assignment()

    def test_existing_application_workflow_is_not_mistaken_for_harness(self):
        self.control.tree["tree"].append({"path": ".github/workflows/application.yml", "type": "blob"})
        with self.assertRaisesRegex(ContractError, "harness"):
            self.start()
        self.assert_no_assignment()

    def test_existing_proposal_is_not_converted_again(self):
        self.control.tree["tree"].append({"path": "drafts/hello-world.yml.draft", "type": "blob"})
        with self.assertRaisesRegex(ContractError, "already exists"):
            self.start()
        self.assert_no_assignment()

    def test_symlink_and_unsupported_source_are_rejected(self):
        self.control.tree["tree"][0]["mode"] = "120000"
        with self.assertRaisesRegex(ContractError, "regular"):
            self.start()
        self.control.tree["tree"][0]["mode"] = "100644"
        self.control.content["content"] = base64.b64encode(b"pipeline { sh 'deploy' }").decode()
        self.control.content["size"] = len(b"pipeline { sh 'deploy' }")
        with self.assertRaisesRegex(ContractError, "exact synthetic"):
            self.start()
        self.assert_no_assignment()

    def test_unknown_archived_org_or_non_main_target_is_rejected(self):
        original = copy.deepcopy(self.control.metadata)
        for key, value in (("archived", True), ("disabled", True), ("default_branch", "trunk"), ("owner", {"type": "Organization"})):
            with self.subTest(key=key):
                self.control.metadata = {**original, key: value}
                with self.assertRaises(ContractError):
                    self.start()
                self.assert_no_assignment()

    def test_changed_issue_during_preflight_refuses_before_marker(self):
        self.control.change_during_preflight = True
        with self.assertRaisesRegex(ContractError, "changed during"):
            self.start()
        self.assert_no_assignment()
        self.assertFalse(any(method == "POST" for method, _, _ in self.control.calls))

    def test_unavailable_copilot_stops_without_start_marker(self):
        self.user.available = False
        with self.assertRaisesRegex(ContractError, "not an available assignee"):
            self.start()
        self.assert_no_assignment()
        self.assertFalse(any(method == "POST" for method, _, _ in self.control.calls))

    def test_missing_ledger_entry_or_earlier_duplicate_stops(self):
        self.control.ledger_contains_current = False
        with self.assertRaisesRegex(ContractError, "Another request"):
            self.start()
        self.control.ledger_contains_current = True
        self.control.extra = [fixture_issue(2)]
        self.control.extra[0]["labels"].append({"name": START_LABEL})
        with self.assertRaisesRegex(ContractError, "already started"):
            self.start()
        self.assert_no_assignment()

    def test_marker_failure_does_not_attempt_assignment(self):
        self.control.fail_marker = True
        with self.assertRaises(ApiError):
            self.start()
        self.assert_no_assignment()

    def test_assignment_failure_preserves_marker_and_blocks_blind_retry(self):
        self.user.fail_assignment = True
        with self.assertRaises(ApiError):
            self.start()
        self.assertEqual(self.evidence.state, "assignment-uncertain")
        self.assertIn({"name": START_LABEL}, self.control.issue["labels"])
        self.evidence = Evidence("trigger", REPO)
        with self.assertRaisesRegex(ContractError, "reconcile"):
            self.start()
        self.assertEqual(self.user.assignment_count, 1)

    def test_accepted_but_lost_response_does_not_start_twice(self):
        self.user.accept_then_timeout = True
        with self.assertRaises(ApiError):
            self.start()
        self.evidence = Evidence("trigger", REPO)
        self.start()
        self.assertEqual(self.evidence.state, "already-assigned")
        self.assertEqual(self.user.assignment_count, 1)

    def test_success_status_without_assignee_is_not_success(self):
        self.user.ignore_assignment = True
        with self.assertRaisesRegex(ApiError, "did not confirm"):
            self.start()
        self.assertFalse(self.evidence.assignment_verified)
        self.assertEqual(self.evidence.state, "assignment-uncertain")

    def test_status_label_failure_does_not_erase_success_or_retry_task(self):
        self.control.fail_status = True
        with self.assertRaises(ApiError):
            self.start()
        self.assertTrue(self.evidence.assignment_verified)
        self.assertEqual(self.evidence.state, "assignment-verified")
        self.evidence = Evidence("trigger", REPO)
        self.start()
        self.assertEqual(self.user.assignment_count, 1)


class SubmissionTests(unittest.TestCase):
    def test_creation_is_one_unassigned_issue(self):
        api = ControlApi()
        api.ledger_contains_current = False
        evidence = Evidence("raise", REPO)
        submit_request(api, REPO, SHA, evidence)
        writes = [(path, body) for method, path, body in api.calls if method == "POST"]
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0][0], PREFIX + "/issues")
        self.assertNotIn("assignees", writes[0][1])
        self.assertEqual(evidence.state, "issue-created")
        self.assertEqual(evidence.issue_number, 2)

    def test_repeat_reuses_even_a_closed_request_without_reassigning(self):
        api = ControlApi()
        api.issue["state"] = "closed"
        evidence = Evidence("raise", REPO)
        submit_request(api, REPO, SHA, evidence)
        self.assertEqual(evidence.state, "existing-request")
        self.assertFalse(any(method == "POST" for method, _, _ in api.calls))

    def test_wrong_identity_or_disabled_trigger_does_not_create(self):
        for attribute, value in (("actor", "other"), ("variable", "false")):
            api = ControlApi()
            setattr(api, attribute, value)
            with self.subTest(attribute=attribute), self.assertRaises(ContractError):
                submit_request(api, REPO, SHA, Evidence("raise", REPO))
            self.assertFalse(any(method == "POST" for method, _, _ in api.calls))

    def test_pagination_is_bounded_and_does_not_silently_truncate(self):
        class ManyIssues:
            def request(self, method, path, body=None):
                return [{}] * 100
        with self.assertRaisesRegex(ContractError, "incomplete"):
            paginated(ManyIssues(), PREFIX + "/issues?state=all")


if __name__ == "__main__":
    unittest.main()
