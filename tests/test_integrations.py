import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import upload
from validate_report import validate


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.file = Path(self.temp.name) / "sbom.json"
        self.file.write_text(json.dumps({"bomFormat": "CycloneDX", "specVersion": "1.6",
                                        "components": [{"type": "library", "name": "flask"}]}))

    def test_empty_sbom_is_rejected(self):
        self.file.write_text('{"bomFormat":"CycloneDX","specVersion":"1.6","components":[]}')
        with self.assertRaises(ValueError):
            validate(self.file)

    def test_sarif_findings_are_allowed_but_execution_failure_is_not(self):
        path = Path(self.temp.name) / "semgrep.sarif"
        data = {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Semgrep"}},
                "results": [{"ruleId": "example"}], "invocations": [{"executionSuccessful": True}]}]}
        path.write_text(json.dumps(data))
        validate(path)
        data["runs"][0]["invocations"][0]["executionSuccessful"] = False
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            validate(path)

    def test_missing_key_fails_before_network(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(upload.requests, "request") as request:
            with self.assertRaises(ValueError):
                upload.dojo(self.file)
            request.assert_not_called()

    def test_remote_cleartext_and_embedded_credentials_are_rejected(self):
        for url in ["http://example.com", "https://user:pass@example.com", "https://example.com?key=value"]:
            with self.subTest(url=url), patch.dict(os.environ, {"SERVICE": url}):
                with self.assertRaises(ValueError):
                    upload.base_url("SERVICE")

    def test_http_failure_and_redirect_are_not_success(self):
        for status in [301, 400, 401, 403, 500]:
            response = Mock(status_code=status, text="sensitive-response")
            with self.subTest(status=status), patch.object(upload.requests, "request", return_value=response):
                with self.assertRaises(RuntimeError) as error:
                    upload.call("POST", "http://localhost")
                self.assertNotIn("sensitive-response", str(error.exception))

    def test_dojo_uses_sarif_and_does_not_auto_verify_or_close(self):
        env = {"DOJO_URL": "http://localhost:8080", "DOJO_API_KEY": "test-key",
               "DOJO_ENGAGEMENT_ID": "12"}
        with patch.dict(os.environ, env, clear=True), patch.object(upload, "call", side_effect=[{"results": []}, {"test": 7}]) as call:
            receipt = upload.dojo(self.file)
        self.assertTrue(call.call_args.args[1].endswith("/import-scan/"))
        fields = call.call_args.kwargs["data"]
        self.assertEqual(fields["scan_type"], "SARIF")
        self.assertEqual(fields["verified"], "false")
        self.assertEqual(fields["close_old_findings"], "false")
        self.assertEqual(receipt["test"], 7)
        self.assertNotIn("test-key", json.dumps(receipt))

    def test_dojo_reuses_existing_test(self):
        env = {"DOJO_URL": "http://localhost:8080", "DOJO_API_KEY": "test-key", "DOJO_ENGAGEMENT_ID": "12"}
        responses = [{"results": [{"id": 7, "title": "VAmPI - Semgrep SARIF"}]}, {"test": 7}]
        with patch.dict(os.environ, env, clear=True), patch.object(upload, "call", side_effect=responses) as call:
            upload.dojo(self.file)
        self.assertTrue(call.call_args.args[1].endswith("/reimport-scan/"))
        self.assertEqual(call.call_args.kwargs["data"]["test"], "7")

    def test_dtrack_waits_for_processing_and_checks_components(self):
        identifier = "12345678-1234-4234-8234-123456789abc"
        env = {"DTRACK_URL": "http://localhost:8081", "DTRACK_API_KEY": "test-key",
               "IMAGE_PROJECT": identifier}
        responses = [{"token": identifier}, {"processing": True}, {"processing": False}, [{"name": "flask"}]]
        with patch.dict(os.environ, env, clear=True), patch.object(upload, "call", side_effect=responses) as call, \
                patch.object(upload.time, "sleep"), contextlib.redirect_stdout(io.StringIO()) as out:
            receipt = upload.dtrack(self.file, "IMAGE_PROJECT")
        self.assertEqual(call.call_args_list[0].kwargs["json"]["project"], identifier)
        self.assertEqual(call.call_count, 4)
        self.assertEqual(receipt["status"], "processed-components-present")
        self.assertNotIn("test-key", out.getvalue())

    def test_dtrack_timeout_is_failure_even_after_acceptance(self):
        identifier = "12345678-1234-4234-8234-123456789abc"
        env = {"DTRACK_URL": "http://localhost:8081", "DTRACK_API_KEY": "test-key", "PROJECT": identifier}
        with patch.dict(os.environ, env), patch.object(upload, "call", side_effect=[{"token": identifier}, {"processing": True}]):
            with self.assertRaises(TimeoutError):
                upload.dtrack(self.file, "PROJECT", poll_seconds=0)

    def test_dtrack_empty_project_is_not_reported_as_success(self):
        identifier = "12345678-1234-4234-8234-123456789abc"
        env = {"DTRACK_URL": "http://localhost:8081", "DTRACK_API_KEY": "test-key", "PROJECT": identifier}
        with patch.dict(os.environ, env), patch.object(upload, "call", side_effect=[{"token": identifier}, {"processing": False}, []]):
            with self.assertRaises(RuntimeError):
                upload.dtrack(self.file, "PROJECT")


if __name__ == "__main__":
    unittest.main()
