import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent.security import SecurityError, SecurityToolkit


class FakeResponse:
    status_code = 200
    url = "http://127.0.0.1:8000/"
    history = []
    text = "<html><body><form></form></body></html>"
    headers = {"content-type": "text/html", "x-content-type-options": "nosniff"}
    cookies = []


class SecurityToolkitTests(unittest.TestCase):
    def test_rejects_unapproved_remote_host(self):
        toolkit = SecurityToolkit(tempfile.mkdtemp())
        with self.assertRaises(SecurityError):
            toolkit.audit("https://example.com")

    def test_local_audit_is_passive_and_writes_report(self):
        workspace = Path(tempfile.mkdtemp())
        session = mock.Mock()
        session.get.return_value = FakeResponse()
        toolkit = SecurityToolkit(workspace, session=session)
        result = toolkit.audit("http://127.0.0.1:8000")
        self.assertIn("kawa-quality", result)
        session.get.assert_called_once()
        self.assertTrue(list((workspace / "kawa-quality").glob("web-audit-*.json")))


if __name__ == "__main__":
    unittest.main()
