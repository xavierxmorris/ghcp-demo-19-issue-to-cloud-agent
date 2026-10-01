from __future__ import annotations

import contextlib
import copy
import io
import json
import shutil
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

from issue_agent import cli
from issue_agent.contracts import ContractError
from issue_agent.enterprise import (
    LANE_IDS, parse_policy, parse_requests, policy_decision, read_fixture, rehearse, run_enterprise,
)
from issue_agent.enterprise_ledger import open_queue
from issue_agent.evidence import verify_bundle

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "enterprise"
EXPECTED = {
    "shared-candidate": ("admitted", "LOCAL_RESERVATION_CREATED"),
    "duplicate-same-source": ("duplicate", "WORK_ALREADY_RESERVED"),
    "near-match": ("manual-review", "CATALOG_NEAR_MATCH"),
    "import-not-ready": ("blocked", "IMPORT_NOT_READY"),
    "unsafe-auto-ci": ("blocked", "AUTO_CI_BOUNDARY_UNPROVEN"),
    "runner-escape": ("blocked", "AGENT_RUNNER_OVERRIDE"),
    "direct-candidate": ("admitted", "LOCAL_RESERVATION_CREATED"),
    "queue-limit": ("deferred", "QUEUE_CAPACITY"),
    "opaque-pipeline": ("manual-review", "PIPELINE_BEHAVIOR_UNRESOLVED"),
}


class EnterpriseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.ledger = self.root / "queue.sqlite3"
        self.raw_policy = read_fixture(FIXTURES / "policy.json")
        self.raw_requests = read_fixture(FIXTURES / "requests.json")
        self.policy = parse_policy(self.raw_policy)
        self.requests = parse_requests(self.raw_requests)

    def run_case(self, requests=None, **options):
        return rehearse(
            self.policy, self.requests if requests is None else requests,
            self.ledger, **options,
        )

    def test_complete_walkthrough_matches_independent_expected_outcomes(self):
        report = self.run_case()
        actual = {row["request_id"]: (row["status"], row["reason"]) for row in report["decisions"]}
        self.assertEqual(actual, EXPECTED)
        self.assertEqual(report["decision_counts"], {
            "admitted": 2, "duplicate": 1, "manual-review": 2, "blocked": 3, "deferred": 1,
        })
        self.assertEqual(report["request_count"], 9)
        self.assertEqual(report["pipeline_definition_count"], 8)
        self.assertEqual(report["new_local_work_items"], 2)
        self.assertEqual(report["queue_depth"], 2)
        self.assertTrue(all(row["why"] and row["policy_why"] for row in report["decisions"]))
        for name in ("live_api_calls", "cloud_tasks_started", "workflows_executed", "accepted_migrations"):
            self.assertEqual(report[name], 0)
        self.assertFalse(report["platform_controls_verified"])

    def test_lane_plan_preserves_separate_groups_and_human_release_gates(self):
        decisions = {row["request_id"]: row for row in self.run_case()["decisions"]}
        manual = decisions["shared-candidate"]["planned_lanes"]
        automatic = decisions["direct-candidate"]["planned_lanes"]
        self.assertEqual([lane["lane"] for lane in manual], list(LANE_IDS))
        self.assertEqual(len({lane["runner_group"] for lane in manual}), 5)
        self.assertEqual(len({lane["isolation_boundary"] for lane in manual}), 5)
        self.assertTrue(all(lane["execution"] == "not-run" for lane in manual + automatic))
        self.assertEqual(manual[1]["required_gate"], "human-workflow-approval")
        self.assertEqual(automatic[1]["required_gate"], "reviewed-unprivileged-CI-boundary")
        self.assertEqual(automatic[-1]["required_gate"], "independent-production-approval-and-scoped-identity")
        self.assertEqual(decisions["unsafe-auto-ci"]["planned_lanes"], [])

    def test_replay_after_reopening_database_creates_no_new_work(self):
        first = self.run_case()
        second = self.run_case()
        self.assertEqual(second["new_local_work_items"], 0)
        self.assertEqual(second["decision_counts"]["duplicate"], 3)
        self.assertEqual(first["queue_snapshot"], second["queue_snapshot"])
        with contextlib.closing(sqlite3.connect(self.ledger)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM work_items").fetchone()[0], 2)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM requests").fetchone()[0], 9)

    def test_reused_request_id_with_changed_input_is_blocked(self):
        request = copy.deepcopy(self.requests[0])
        self.run_case([request])
        request["source_revision"] = "a" * 40
        report = self.run_case([request])
        self.assertEqual(report["decisions"][0]["reason"], "REQUEST_ID_CHANGED")
        self.assertEqual(report["new_local_work_items"], 0)

    def test_new_revision_cannot_overlap_an_existing_pipeline_reservation(self):
        first = copy.deepcopy(self.requests[0])
        second = {**first, "request_id": "new-revision", "source_revision": "a" * 40}
        report = self.run_case([first, second])
        self.assertEqual(report["decisions"][1]["reason"], "PIPELINE_ALREADY_QUEUED")
        self.assertEqual(report["queue_depth"], 1)

    def test_duplicate_work_cannot_change_the_original_route_or_approval_plan(self):
        original = self.requests[0]
        self.run_case([original])
        for field, value in (
            ("catalog_match", "none"), ("ci_approval", "automatic"), ("reviewer", "different-reviewer"),
        ):
            request = {**original, "request_id": f"changed-{field}", field: value}
            with self.subTest(field=field):
                report = self.run_case([request])
                self.assertEqual(report["decisions"][0]["reason"], "WORK_INTENT_CHANGED")
                self.assertEqual(report["decisions"][0]["planned_lanes"], [])
                self.assertEqual(report["queue_snapshot"][0]["route"], "shared-workflow-candidate")

    def test_different_pipeline_in_the_same_repository_has_its_own_work_item(self):
        first = copy.deepcopy(self.requests[0])
        second = {**first, "request_id": "second-pipeline", "pipeline_path": "ci/second.Jenkinsfile"}
        report = self.run_case([first, second])
        self.assertEqual(report["new_local_work_items"], 2)
        self.assertEqual(report["pipeline_definition_count"], 2)

    def test_repository_rename_does_not_bypass_immutable_id_deduplication(self):
        first = copy.deepcopy(self.requests[0])
        renamed = {**first, "request_id": "renamed-request", "repository": "synthetic-bank/renamed"}
        report = self.run_case([first, renamed])
        self.assertEqual(report["decisions"][1]["status"], "duplicate")
        self.assertEqual(report["decisions"][1]["canonical_request_id"], first["request_id"])

    def test_stop_switch_admits_nothing_but_does_not_hide_existing_reservations(self):
        stopped = self.run_case(stop_new_work=True)
        self.assertEqual(stopped["new_local_work_items"], 0)
        self.assertEqual(stopped["queue_depth"], 0)
        self.assertEqual(stopped["decision_counts"]["deferred"], 4)
        self.assertEqual(stopped["decisions"][0]["reason"], "STOP_SWITCH")
        self.run_case()
        replay = self.run_case(stop_new_work=True)
        self.assertEqual(replay["new_local_work_items"], 0)
        self.assertEqual(replay["decision_counts"]["duplicate"], 3)

    def test_per_run_limit_counts_admissions_not_duplicate_requests(self):
        report = self.run_case(max_new=1)
        self.assertEqual(report["new_local_work_items"], 1)
        decisions = {row["request_id"]: row for row in report["decisions"]}
        self.assertEqual(decisions["duplicate-same-source"]["status"], "duplicate")
        self.assertEqual(decisions["direct-candidate"]["reason"], "RUN_SUBMISSION_LIMIT")

    def test_operator_cannot_raise_the_policy_limit(self):
        with self.assertRaisesRegex(ContractError, "not raise"):
            self.run_case(max_new=4)
        self.assertFalse(self.ledger.exists())

    def test_invalid_per_run_limits_are_not_coerced(self):
        for value in (0, -1, True, 1.5):
            with self.subTest(value=value), self.assertRaises(ContractError):
                self.run_case(max_new=value)

    def test_each_auto_ci_risk_prevents_admission(self):
        risks = {
            "inventory_complete": False, "boundary_reviewed": False, "read_token_only": False,
            "secrets_available": True, "production_network": True, "privileged_follow_on": True,
        }
        for name, value in risks.items():
            request = copy.deepcopy(self.requests[6])
            request["pr_workflows"][name] = value
            with self.subTest(name=name):
                self.assertEqual(policy_decision(request, self.policy)[:2], ("blocked", "AUTO_CI_BOUNDARY_UNPROVEN"))

    def test_manual_ci_does_not_silently_qualify_an_unsafe_boundary(self):
        request = copy.deepcopy(self.requests[0])
        request["pr_workflows"]["secrets_available"] = True
        self.assertEqual(policy_decision(request, self.policy)[:2], ("manual-review", "CI_BOUNDARY_REVIEW_REQUIRED"))

    def test_requester_owner_and_processing_gates_are_separate(self):
        cases = (
            ("authorized", False, "REQUEST_NOT_AUTHORIZED"),
            ("owner", "", "OWNERSHIP_UNRESOLVED"),
            ("reviewer", "", "OWNERSHIP_UNRESOLVED"),
            ("reviewer", "demo-requester", "INDEPENDENT_REVIEW_REQUIRED"),
            ("ai_processing_allowed", False, "AI_PROCESSING_NOT_APPROVED"),
            ("catalog_match", "unknown", "CATALOG_EVIDENCE_MISSING"),
        )
        for field, value, expected in cases:
            request = {**self.requests[0], field: value}
            with self.subTest(field=field, value=value):
                self.assertEqual(policy_decision(request, self.policy)[1], expected)

    def test_claimed_catalog_match_does_not_override_unknown_pipeline_behavior(self):
        request = {**self.requests[0], "pipeline_shape": "opaque"}
        self.assertEqual(policy_decision(request, self.policy)[1], "PIPELINE_BEHAVIOR_UNRESOLVED")

    def test_pr_runner_cannot_be_a_release_runner(self):
        request = copy.deepcopy(self.requests[0])
        request["pr_workflows"]["runner_group"] = "demo-release-prod"
        self.assertEqual(policy_decision(request, self.policy)[1], "PR_RUNNER_OUTSIDE_VALIDATION_LANE")

    def test_concurrent_duplicate_requests_reserve_exactly_one_item(self):
        with open_queue(self.ledger, self.policy.fingerprint):
            pass
        request = self.requests[0]
        start = Barrier(2)

        def reserve(_):
            start.wait(timeout=5)
            return self.run_case([request])

        with ThreadPoolExecutor(max_workers=2) as executor:
            reports = list(executor.map(reserve, range(2)))
        self.assertEqual(sorted(row["decisions"][0]["status"] for row in reports), ["admitted", "duplicate"])
        with contextlib.closing(sqlite3.connect(self.ledger)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM work_items").fetchone()[0], 1)

    def test_concurrent_different_requests_cannot_overrun_global_capacity(self):
        self.raw_policy["limits"]["max_queued"] = 1
        self.policy = parse_policy(self.raw_policy)
        with open_queue(self.ledger, self.policy.fingerprint):
            pass
        requests = [self.requests[0], self.requests[6]]
        start = Barrier(2)

        def reserve(request):
            start.wait(timeout=5)
            return self.run_case([request])

        with ThreadPoolExecutor(max_workers=2) as executor:
            reports = list(executor.map(reserve, requests))
        self.assertEqual(sorted(row["decisions"][0]["status"] for row in reports), ["admitted", "deferred"])
        self.assertEqual(sum(row["new_local_work_items"] for row in reports), 1)

    def test_foreign_database_is_unchanged(self):
        with contextlib.closing(sqlite3.connect(self.ledger)) as connection, connection:
            connection.execute("CREATE TABLE unrelated(value TEXT)")
            connection.execute("INSERT INTO unrelated VALUES ('keep')")
        before = self.ledger.read_bytes()
        with self.assertRaisesRegex(ContractError, "not an initialized"):
            self.run_case()
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_changed_policy_cannot_reinterpret_existing_ledger(self):
        self.run_case()
        before = self.ledger.read_bytes()
        self.raw_policy["limits"]["max_queued"] = 3
        self.policy = parse_policy(self.raw_policy)
        with self.assertRaisesRegex(ContractError, "policy/engine differs"):
            self.run_case()
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_foreign_schema_version_is_not_upgraded_silently(self):
        self.run_case()
        with contextlib.closing(sqlite3.connect(self.ledger)) as connection, connection:
            connection.execute("PRAGMA user_version = 2")
        with self.assertRaisesRegex(ContractError, "Unsupported enterprise ledger"):
            self.run_case()

    def test_policy_rejects_shared_hosts_even_with_different_labels(self):
        self.raw_policy["lanes"]["pr-validation"]["isolation_boundary"] = "fixture-agent-zone"
        with self.assertRaisesRegex(ContractError, "must not share"):
            parse_policy(self.raw_policy)

    def test_policy_rejects_override_persistence_and_privilege_changes(self):
        changes = (
            ("repository_runner_overrides", True),
            ("runner_lifetime", "persistent"),
            ("data_classification", "customer"),
            ("schema_version", True),
        )
        for field, value in changes:
            with self.subTest(field=field), self.assertRaises(ContractError):
                parse_policy({**self.raw_policy, field: value})
        self.raw_policy["lanes"]["pr-validation"]["credential"] = "artifact-publish"
        with self.assertRaisesRegex(ContractError, "credential boundary"):
            parse_policy(self.raw_policy)

    def test_policy_fingerprint_is_stable_across_json_formatting(self):
        reordered = json.loads(json.dumps(self.raw_policy, sort_keys=True, indent=4))
        self.assertEqual(parse_policy(reordered).fingerprint, self.policy.fingerprint)

    def test_policy_cannot_change_behind_its_fingerprint(self):
        self.raw_policy["lanes"]["agent"]["runner_group"] = "modified"
        self.assertEqual(self.policy.lanes["agent"].runner_group, "demo-agent-sandbox")
        with self.assertRaises(TypeError):
            self.policy.lanes["agent"] = self.policy.lanes["release-prod"]
        with self.assertRaises(FrozenInstanceError):
            self.policy.lanes["agent"].runner_group = "modified"

    def test_request_contract_rejects_unknown_fields_bad_types_and_paths(self):
        for field, value in (
            ("authorized", "true"), ("repository_id", True), ("source_revision", "main"),
            ("pipeline_path", "../Jenkinsfile"), ("pipeline_path", r"C:\Jenkinsfile"),
            ("pipeline_path", "a" * 201), ("pipeline_shape", "maven"),
        ):
            data = copy.deepcopy(self.raw_requests)
            data["requests"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ContractError):
                parse_requests(data)
        data = copy.deepcopy(self.raw_requests)
        data["requests"][0]["secret_value"] = "not-allowed"
        with self.assertRaisesRegex(ContractError, "unknown"):
            parse_requests(data)

    def test_request_envelope_is_explicitly_synthetic_and_bounded(self):
        for field, value in (
            ("identifiers_are_fixtures", False), ("data_classification", "customer"),
            ("schema_version", True), ("requests", []), ("requests", [self.requests[0]] * 101),
        ):
            with self.subTest(field=field), self.assertRaises(ContractError):
                parse_requests({**self.raw_requests, field: value})

    def test_json_duplicate_keys_nonfinite_numbers_and_oversize_fail(self):
        path = self.root / "fixture.json"
        for text in ('{"x":1,"x":2}', '{"x":NaN}', " " * (128 * 1024 + 1), "{broken"):
            path.write_text(text, encoding="utf-8")
            with self.subTest(length=len(text)), self.assertRaises(ContractError):
                read_fixture(path)


class EnterpriseCliTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        shutil.copytree(FIXTURES, self.root / "fixtures" / "enterprise")

    def run_cli(self, *arguments):
        with patch.object(cli, "ROOT", self.root), \
                patch.object(cli, "GhApi", side_effect=AssertionError("no GitHub client")), \
                patch.object(cli, "RestApi", side_effect=AssertionError("no GitHub client")), \
                patch("subprocess.run", side_effect=AssertionError("no external commands")), \
                patch("socket.create_connection", side_effect=AssertionError("no network")), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return cli.main(["enterprise", *arguments])

    def test_cli_is_offline_and_keeps_mutable_state_outside_sealed_bundle(self):
        self.assertEqual(self.run_cli("--out", "out/first"), 0)
        bundle = self.root / "out" / "first"
        verify_bundle(bundle)
        self.assertEqual({path.name for path in bundle.iterdir()}, {
            "enterprise-report.json", "enterprise-report.md", "bundle-manifest.json",
        })
        report = json.loads((bundle / "enterprise-report.json").read_text())
        self.assertFalse(report["platform_controls_verified"])
        self.assertEqual(report["new_local_work_items"], 2)
        self.assertTrue((self.root / "out" / "first.sqlite3").is_file())

    def test_explicit_replay_preserves_previous_bundle_bytes(self):
        self.assertEqual(self.run_cli("--out", "out/first", "--ledger", "out/shared.sqlite3"), 0)
        original = (self.root / "out" / "first" / "enterprise-report.json").read_bytes()
        self.assertEqual(self.run_cli("--out", "out/second", "--ledger", "out/shared.sqlite3"), 0)
        second = json.loads((self.root / "out" / "second" / "enterprise-report.json").read_text())
        self.assertEqual(second["new_local_work_items"], 0)
        self.assertEqual((self.root / "out" / "first" / "enterprise-report.json").read_bytes(), original)
        verify_bundle(self.root / "out" / "first")

    def test_ledger_cannot_be_inside_its_bundle_or_outside_out(self):
        for index, ledger in enumerate(("out/first/queue.sqlite3", "../outside.sqlite3", "state.sqlite3")):
            output = "out/first" if index == 0 else f"out/failure-{index}"
            with self.subTest(ledger=ledger):
                self.assertEqual(self.run_cli("--out", output, "--ledger", ledger), 2)
                report = json.loads((self.root / output / "enterprise-report.json").read_text())
                self.assertEqual(report["status"], "failed")
                verify_bundle(self.root / output)

    def test_output_and_default_ledger_collisions_are_not_overwritten(self):
        self.assertEqual(self.run_cli("--out", "out/first"), 0)
        before = (self.root / "out" / "first.sqlite3").read_bytes()
        self.assertEqual(self.run_cli("--out", "out/first"), 2)
        (self.root / "out" / "collision.sqlite3").write_bytes(before)
        self.assertEqual(self.run_cli("--out", "out/collision"), 2)
        self.assertEqual((self.root / "out" / "collision.sqlite3").read_bytes(), before)

    def test_existing_bundle_cannot_receive_nested_outputs_or_ledger_writes(self):
        self.assertEqual(self.run_cli("--out", "out/first"), 0)
        self.assertEqual(self.run_cli("--out", "out/first/nested"), 2)
        self.assertEqual(self.run_cli("--out", "out/second", "--ledger", "out/first/extra.sqlite3"), 2)
        verify_bundle(self.root / "out" / "first")

    def test_stop_and_reduced_admission_flags_are_wired(self):
        self.assertEqual(self.run_cli("--out", "out/stopped", "--stop-new-work"), 0)
        stopped = json.loads((self.root / "out" / "stopped" / "enterprise-report.json").read_text())
        self.assertEqual(stopped["new_local_work_items"], 0)
        self.assertEqual(self.run_cli("--out", "out/capped", "--max-new", "1"), 0)
        capped = json.loads((self.root / "out" / "capped" / "enterprise-report.json").read_text())
        self.assertEqual(capped["new_local_work_items"], 1)

    def test_invalid_fixture_fails_before_creating_a_ledger(self):
        policy = self.root / "fixtures" / "enterprise" / "policy.json"
        policy.write_text('{"not":"the contract"}', encoding="utf-8")
        self.assertEqual(self.run_cli("--out", "out/invalid"), 2)
        self.assertFalse((self.root / "out" / "invalid.sqlite3").exists())
        report = json.loads((self.root / "out" / "invalid" / "enterprise-report.json").read_text())
        self.assertEqual(report["status"], "failed")


if __name__ == "__main__":
    unittest.main()
