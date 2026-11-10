"""Offline wire-contract tests: never contact Firecrawl, Exa, OpenAI, or E2B."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

import httpx
from fastapi.testclient import TestClient

spec = importlib.util.spec_from_file_location(
    "patent_search", Path(__file__).resolve().parents[1] / "patent-search" / "ps.py"
)
ps = importlib.util.module_from_spec(spec)
# Do not read a developer's credentials while importing the application.
with patch("dotenv.load_dotenv"):
    spec.loader.exec_module(ps)

URL = "https://patents.google.com/patent/US123/en"
REAL_ASYNC_CLIENT = httpx.AsyncClient


class FirecrawlV2Tests(unittest.TestCase):
    def setUp(self):
        self.requests = []
        self.scrape_status = 200
        self.scrape_data = {"success": True, "data": {"markdown": "# Patent text"}}
        self.search_results = [{"title": "Patent", "url": URL}]
        self.env = patch.dict(ps.os.environ, {"FIRECRAWL_API_KEY": "test-key", "EXA_API_KEY": "test-exa"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.http = patch.object(ps.httpx, "AsyncClient", side_effect=lambda **kw: REAL_ASYNC_CLIENT(transport=httpx.MockTransport(self.handle), **kw))
        self.http.start()
        self.addCleanup(self.http.stop)
        self.sandbox = patch.object(ps.Sandbox, "create", side_effect=AssertionError("No sandbox should be created"))
        self.sandbox.start()
        self.addCleanup(self.sandbox.stop)
        self.client = TestClient(ps.app)
        self.addCleanup(self.client.close)

    def handle(self, request):
        self.requests.append(request)
        if str(request.url) == "https://api.exa.ai/search":
            return httpx.Response(200, json={"results": self.search_results})
        self.assertEqual(str(request.url), "https://api.firecrawl.dev/v2/scrape")
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.headers["Authorization"], "Bearer test-key")
        self.assertEqual(json.loads(request.content), {"url": URL, "formats": ["markdown"], "onlyMainContent": True})
        return httpx.Response(self.scrape_status, json=self.scrape_data)

    def test_scrape_v2_wire_contract_and_markdown(self):
        response = self.client.post("/scrape", json={"url": URL})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"text": "# Patent text"})
        self.assertEqual(len(self.requests), 1)

    def test_scrape_empty_content_fallback(self):
        self.scrape_data = {"success": True, "data": {}}
        response = self.client.post("/scrape", json={"url": URL})
        self.assertEqual(response.json(), {"text": "No content extracted"})

    def test_scrape_upstream_error_is_preserved(self):
        self.scrape_status = 429
        self.scrape_data = {"success": False, "error": "rate limited"}
        response = self.client.post("/scrape", json={"url": URL})
        self.assertEqual(response.status_code, 429)
        self.assertIn("rate limited", response.json()["detail"])

    def test_search_and_scrape_uses_same_v2_endpoint(self):
        stream = MagicMock()
        stream.__enter__.return_value = stream
        stream.__iter__.return_value = iter([])
        stream.get_final_response.return_value = SimpleNamespace(output_text="TITLE: Patent")
        with patch.object(ps, "OpenAI") as openai:
            openai.return_value.responses.stream.return_value = stream
            response = self.client.post("/search-and-scrape", json={"query": "pull to refresh"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"text": "TITLE: Patent"})
            args = openai.return_value.responses.stream.call_args.kwargs
            self.assertEqual(args["input"], "# Patent text")
            self.assertNotIn("tools", args)
        self.assertEqual(len(self.requests), 2)

    def test_search_with_no_results_does_not_scrape(self):
        self.search_results = []
        response = self.client.post("/search-and-scrape", json={"query": "missing"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(self.requests), 1)

    def test_search_propagates_scrape_error_without_openai(self):
        self.scrape_status = 402
        with patch.object(ps, "OpenAI") as openai:
            response = self.client.post("/search-and-scrape", json={"query": "patent"})
            self.assertEqual(response.status_code, 402)
            openai.assert_not_called()

    def test_scrape_network_error(self):
        with patch.object(ps.httpx, "AsyncClient") as client:
            client.return_value.__aenter__.return_value.post.side_effect = httpx.ConnectError("unavailable")
            response = self.client.post("/scrape", json={"url": URL})
        self.assertEqual(response.status_code, 500)
        self.assertIn("HTTP error", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
