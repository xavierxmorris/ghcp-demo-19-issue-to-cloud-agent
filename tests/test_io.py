from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from issue_agent import cli
from issue_agent.contracts import ContractError
from issue_agent.evidence import reserve_output, verify_bundle, write_bundle
from issue_agent.github_api import (
    API_VERSION, MAX_RESPONSE, ApiError, NoRedirect, RestApi, check_path, decode_json, gh_json, redact,
)
from issue_agent.service import Evidence
from scripts.check_repo import validate_proposal
from test_contracts import SHA, VALID_DRAFT, VALID_REVIEW


class ApiBoundaryTests(unittest.TestCase):
    def test_credential_is_not_in_repr(self):
        self.assertNotIn("TEST_PRIVATE_TOKEN", repr(RestApi("TEST_PRIVATE_TOKEN")))

    def test_only_github_relative_paths_are_allowed(self):
        for path in ("https://example.com", "//example.com/repos/o/r", "/repos/o/r#x", "/repos/o/r\n", "/repos/o/../r", "/agents/tasks"):
            with self.subTest(path=path), self.assertRaises(ContractError):
                check_path(path)

    def test_agent_task_endpoints_cannot_start_or_mutate_tasks(self):
        check_path("/agents/repos/o/r/tasks", "GET")
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            with self.subTest(method=method), self.assertRaisesRegex(ContractError, "read-only"):
                check_path("/agents/repos/o/r/tasks", method)

    def test_rest_headers_and_fixed_host(self):
        response = MagicMock()
        response.read.return_value = b'{"ok":true}'
        with patch("issue_agent.github_api.build_opener") as factory:
            factory.return_value.open.return_value.__enter__.return_value = response
            self.assertEqual(RestApi("TEST_TOKEN_ONLY").request("GET", "/repos/o/r"), {"ok": True})
            request = factory.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url, "https://api.github.com/repos/o/r")
            self.assertEqual(request.get_header("Authorization"), "Bearer TEST_TOKEN_ONLY")
            self.assertEqual(request.get_header("X-github-api-version"), API_VERSION)
            response.read.assert_called_once_with(MAX_RESPONSE + 1)

    def test_http_error_is_diagnostic_but_redacts_secret(self):
        token = "TEST_PRIVATE_TOKEN"
        error = HTTPError("https://api.github.com/repos/o/r", 403, "Forbidden", {"X-GitHub-Request-Id": "TEST:123"}, io.BytesIO(('denied ' + token).encode()))
        with patch("issue_agent.github_api.build_opener") as factory:
            factory.return_value.open.side_effect = error
            with self.assertRaises(ApiError) as captured:
                RestApi(token).request("GET", "/repos/o/r")
        self.assertNotIn(token, str(captured.exception))
        self.assertIn("HTTP 403", str(captured.exception))
        self.assertIn("TEST:123", str(captured.exception))

    def test_transport_failure_and_redirect_are_not_retried(self):
        with patch("issue_agent.github_api.build_opener") as factory:
            factory.return_value.open.side_effect = URLError("TEST_PRIVATE_TOKEN")
            with self.assertRaises(ApiError) as captured:
                RestApi("TEST_PRIVATE_TOKEN").request("POST", "/repos/o/r/issues", {})
            self.assertNotIn("TEST_PRIVATE_TOKEN", str(captured.exception))
            self.assertEqual(factory.return_value.open.call_count, 1)
        with self.assertRaisesRegex(ApiError, "redirect refused"):
            NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.com")

    def test_missing_and_malformed_tokens_fail_before_network(self):
        with patch("issue_agent.github_api.build_opener") as factory:
            for token in ("", " token", "token\n", "to ken"):
                with self.subTest(token=token), self.assertRaises(ApiError):
                    RestApi(token).request("GET", "/repos/o/r")
            factory.assert_not_called()

    def test_response_size_and_invalid_json_are_explicit(self):
        for raw in (b"not JSON", b"\xff", b"x" * (MAX_RESPONSE + 1)):
            with self.subTest(length=len(raw)), self.assertRaises(ApiError):
                decode_json(raw)

    def test_known_token_shapes_are_redacted(self):
        token = "github_pat_" + "a" * 40
        self.assertEqual(redact("denied " + token), "denied [REDACTED]")

    def test_gh_sends_json_through_stdin_not_arguments(self):
        with patch("issue_agent.github_api.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "{}", "")
            gh_json(["api", "--input", "-"], {"body": "SYNTHETIC_BODY"})
            self.assertNotIn("SYNTHETIC_BODY", " ".join(run.call_args.args[0]))
            self.assertIn("SYNTHETIC_BODY", run.call_args.kwargs["input"])
            self.assertNotIn("shell", run.call_args.kwargs)

    def test_cli_timeout_warns_against_duplicate_mutations(self):
        with patch("issue_agent.github_api.subprocess.run", side_effect=subprocess.TimeoutExpired("gh", 60)):
            with self.assertRaisesRegex(ApiError, "may have succeeded"):
                gh_json(["api"])


class EvidenceTests(unittest.TestCase):
    def test_new_bundle_manifest_binds_every_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            out = reserve_output(root, Path("out") / "first")
            evidence = Evidence("preview", "demo-owner/repo", source_commit=SHA)
            write_bundle(out, evidence)
            manifest = json.loads((out / "bundle-manifest.json").read_text())
            names = {path.name for path in out.iterdir()} - {"bundle-manifest.json"}
            self.assertEqual(names, set(manifest["sha256"]))
            for name, digest in manifest["sha256"].items():
                self.assertEqual(hashlib.sha256((out / name).read_bytes()).hexdigest(), digest)
            with self.assertRaisesRegex(ContractError, "already exists"):
                reserve_output(root, Path("out") / "first")

    def test_retained_evidence_detects_changed_artifact_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            out = reserve_output(Path(directory), Path("out") / "retained")
            write_bundle(out, Evidence("preview", "demo-owner/repo"))
            verify_bundle(out)
            (out / "report.md").write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "artifact changed"):
                verify_bundle(out)

    def test_retained_evidence_rejects_extra_or_missing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for kind in ("extra", "missing"):
                out = reserve_output(root, Path("out") / kind)
                write_bundle(out, Evidence("preview", "demo-owner/repo"))
                if kind == "extra":
                    (out / "unexpected.txt").write_text("extra", encoding="utf-8")
                else:
                    (out / "report.md").unlink()
                with self.subTest(kind=kind), self.assertRaisesRegex(ContractError, "missing or unexpected"):
                    verify_bundle(out)

    def test_observed_model_is_not_overwritten_by_an_unknown_placeholder(self):
        with tempfile.TemporaryDirectory() as directory:
            out = reserve_output(Path(directory), Path("out") / "observed")
            evidence = Evidence("observe", "demo-owner/repo")
            evidence.pull_requests = [{"model": "synthetic-observed-model"}]
            write_bundle(out, evidence)
            report = json.loads((out / "report.json").read_text())
            self.assertEqual(report["model"], "synthetic-observed-model")
            self.assertEqual(report["model_selection"], "platform default; no override requested")

    def test_output_cannot_escape_or_write_active_workflows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in (Path("out"), Path("README.md"), Path(".github") / "workflows", Path("..") / "outside"):
                with self.subTest(path=path), self.assertRaises(ContractError):
                    reserve_output(root, path)

    def test_baseline_does_not_claim_a_proposal_but_required_mode_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            validate_proposal(root)
            with self.assertRaises(ContractError):
                validate_proposal(root, required=True)
            drafts = root / "drafts"
            drafts.mkdir()
            (drafts / "hello-world.yml.draft").write_text(VALID_DRAFT)
            (drafts / "review.md").write_text(VALID_REVIEW)
            validate_proposal(root, required=True)
            (drafts / "extra.yml").write_text("on: push")
            with self.assertRaises(ContractError):
                validate_proposal(root, required=True)


class CliTests(unittest.TestCase):
    def test_preview_has_no_network_or_git_dependency(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(cli, "ROOT", Path(directory)), \
                patch.object(cli, "GhApi", side_effect=AssertionError("network")), \
                patch.object(cli, "RestApi", side_effect=AssertionError("network")), \
                patch.object(cli, "git_output", side_effect=AssertionError("git")), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["preview", "--out", "out/preview"]), 0)
            report = json.loads((Path(directory) / "out" / "preview" / "report.json").read_text())
            self.assertEqual(report["mutations"], [])
            self.assertTrue(report["source_commit_is_fixture"])
            self.assertFalse(report["agent_execution_observed"])

    def test_live_requires_explicit_consent_before_output_or_api(self):
        with patch.object(cli, "GhApi", side_effect=AssertionError("network")), \
                patch.object(cli, "reserve_output", side_effect=AssertionError("write")), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["raise", "--repository", "demo-owner/repo"]), 2)

    def test_dirty_clone_and_mismatched_origin_are_refused(self):
        with patch.object(cli, "git_output", return_value=" M README.md"):
            with self.assertRaisesRegex(ContractError, "clean checkout"):
                cli.local_live_commit("demo-owner/repo")
        with patch.object(cli, "git_output", side_effect=["", "https://github.com/other/repo.git"]):
            with self.assertRaisesRegex(ContractError, "origin"):
                cli.local_live_commit("demo-owner/repo")

    def test_invalid_event_is_retained_as_failure_not_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            event = root / "event.json"
            event.write_text("{broken", encoding="utf-8")
            env = {
                "GITHUB_REPOSITORY": "demo-owner/repo", "GITHUB_EVENT_PATH": str(event),
                "GITHUB_RUN_ID": "123", "GITHUB_TOKEN": "TEST_CONTROL", "COPILOT_USER_TOKEN": "TEST_USER",
            }
            with patch.object(cli, "ROOT", root), patch.dict(os.environ, env), \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(cli.main(["trigger", "--out", "out/failure"]), 2)
            raw = (root / "out" / "failure" / "report.json").read_text()
            self.assertNotIn("TEST_CONTROL", raw)
            self.assertNotIn("TEST_USER", raw)
            self.assertEqual(json.loads(raw)["state"], "blocked")


if __name__ == "__main__":
    unittest.main()
