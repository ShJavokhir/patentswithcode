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
        self.scrape_url = URL
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
        self.openai_patch = patch.object(ps, "OpenAI")
        self.openai = self.openai_patch.start().return_value
        self.addCleanup(self.openai_patch.stop)
        self.openai.responses.create.return_value = SimpleNamespace(
            output_text='{"candidate_index": 0}'
        )
        stream = MagicMock()
        stream.__enter__.return_value = stream
        stream.__iter__.return_value = iter([])
        stream.get_final_response.return_value = SimpleNamespace(
            output_text="TITLE: Patent\nABSTRACT: Example\nDESCRIPTION: Text\nCLAIMS: Example"
        )
        self.openai.responses.stream.return_value = stream
        self.client = TestClient(ps.app)
        self.addCleanup(self.client.close)

    def handle(self, request):
        self.requests.append(request)
        if str(request.url) == "https://api.exa.ai/search":
            return httpx.Response(200, json={"results": self.search_results})
        self.assertEqual(str(request.url), "https://api.firecrawl.dev/v2/scrape")
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.headers["Authorization"], "Bearer test-key")
        self.assertEqual(json.loads(request.content), {"url": self.scrape_url, "formats": ["markdown"], "onlyMainContent": True})
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
        response = self.client.post("/search-and-scrape", json={"query": "pull to refresh"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "text": "TITLE: Patent\nABSTRACT: Example\nDESCRIPTION: Text\nCLAIMS: Example"
        })
        args = self.openai.responses.stream.call_args.kwargs
        self.assertEqual(args["input"], "# Patent text")
        self.assertNotIn("tools", args)
        selection_args = self.openai.responses.create.call_args.kwargs
        self.assertEqual(json.loads(selection_args["input"])["query"], "pull to refresh")
        self.assertEqual(selection_args["text"]["format"]["type"], "json_schema")
        self.assertEqual(len(self.requests), 2)

    def test_model_can_select_non_first_patent(self):
        second_url = "https://patents.google.com/patent/US456/en"
        self.search_results.append({"title": "Relevant patent", "url": second_url})
        self.openai.responses.create.return_value.output_text = '{"candidate_index": 1}'
        self.scrape_url = second_url
        response = self.client.post("/search-and-scrape", json={"query": "relevant patent"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(self.requests[-1].content)["url"], second_url)

    def test_model_declining_match_does_not_scrape_or_format(self):
        self.openai.responses.create.return_value.output_text = '{"candidate_index": null}'
        response = self.client.post("/search-and-scrape", json={"query": "unrelated"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(self.requests), 1)
        self.openai.responses.stream.assert_not_called()

    def test_invalid_selection_does_not_scrape_or_format(self):
        for choice in ["", "not json", "[]", "{}", '{"candidate_index": -1}',
                       '{"candidate_index": 100}', '{"candidate_index": true}',
                       '{"candidate_index": "0"}', '{"candidate_index": 0.5}',
                       '{"candidate_index": 0, "url": "https://example.com"}']:
            with self.subTest(choice=choice):
                self.requests.clear()
                self.openai.responses.create.return_value.output_text = choice
                response = self.client.post("/search-and-scrape", json={"query": "patent"})
                self.assertEqual(response.status_code, 502)
                self.assertEqual(len(self.requests), 1)
                self.openai.responses.stream.assert_not_called()

    def test_invalid_candidates_are_not_offered_or_scraped(self):
        self.search_results = [
            {"url": "https://example.com/patent/US123"},
            {"url": "https://patents.google.com.evil.com/patent/US123"},
            {"url": "https://patents.google.com/search"},
            {"url": "https://patents.google.com/patent/"},
            {"url": "http://patents.google.com/patent/US123"},
            {"url": "https://[invalid"},
            {"url": None},
        ]
        response = self.client.post("/search-and-scrape", json={"query": "patent"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(self.requests), 1)
        self.openai.responses.create.assert_not_called()
        self.openai.responses.stream.assert_not_called()

    def test_invalid_candidate_before_valid_candidate_is_filtered(self):
        self.search_results.insert(0, {"url": "https://example.com/patent/US123"})
        response = self.client.post("/search-and-scrape", json={"query": "patent"})
        self.assertEqual(response.status_code, 200)
        candidates = json.loads(self.openai.responses.create.call_args.kwargs["input"])["candidates"]
        self.assertEqual([item["url"] for item in candidates], [URL])

    def test_selection_error_does_not_scrape(self):
        self.openai.responses.create.side_effect = RuntimeError("Selection unavailable")
        response = self.client.post("/search-and-scrape", json={"query": "patent"})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(len(self.requests), 1)
        self.openai.responses.stream.assert_not_called()

    def test_formatting_error_is_reported(self):
        self.openai.responses.stream.side_effect = RuntimeError("Formatting unavailable")
        response = self.client.post("/search-and-scrape", json={"query": "patent"})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(len(self.requests), 2)

    def test_search_with_no_results_does_not_scrape(self):
        self.search_results = []
        response = self.client.post("/search-and-scrape", json={"query": "missing"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(self.requests), 1)

    def test_search_propagates_scrape_error_without_formatting(self):
        self.scrape_status = 402
        response = self.client.post("/search-and-scrape", json={"query": "patent"})
        self.assertEqual(response.status_code, 402)
        self.openai.responses.stream.assert_not_called()

    def test_scrape_network_error(self):
        with patch.object(ps.httpx, "AsyncClient") as client:
            client.return_value.__aenter__.return_value.post.side_effect = httpx.ConnectError("unavailable")
            response = self.client.post("/scrape", json={"url": URL})
        self.assertEqual(response.status_code, 500)
        self.assertIn("HTTP error", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
