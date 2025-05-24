# tests/conftest.py
import pytest, os
skip_offline = pytest.mark.skipif(
    os.getenv("NO_NET", "1") == "1",
    reason="Network-dependent – skipped in offline CI",
)
import httpx
from typing import Dict, List, Any
import sys
from types import ModuleType

# Provide stub for python-dotenv if not present
try:
    import dotenv  # noqa: F401
except ModuleNotFoundError:
    sys.modules["dotenv"] = ModuleType("dotenv")
    from tests.shims import dotenv as _shim  # type: ignore
    sys.modules["dotenv"].load_dotenv = _shim.FakeLoader.load_dotenv


class MockAsyncClient:
    def __init__(self, response_map: Dict[str, List[str]], call_counts_ref: Dict[str, int]):
        self.response_map = response_map
        self.call_counts = call_counts_ref

    # VVV MODIFICATION HERE VVV
    async def post(self, url: str, json: Dict[str, Any], headers: Dict[str, Any]): # Changed json_payload back to json
    # ^^^ MODIFICATION HERE ^^^
        prompt_content = json.get("messages", [{}])[0].get("content", "") # Use the correct param name 'json'
        
        responses_for_key = None
        chosen_key = None

        for key_substring, agent_responses in self.response_map.items():
            if key_substring in prompt_content:
                responses_for_key = agent_responses
                chosen_key = key_substring
                break
        
        if responses_for_key is None and "default" in self.response_map: 
            responses_for_key = self.response_map["default"]
            chosen_key = "default"

        response_text = "<error_mock_llm_no_response_defined_for_prompt>"
        status_code = 200 

        if responses_for_key and chosen_key:
            count = self.call_counts.get(chosen_key, 0)
            if count < len(responses_for_key):
                response_text = responses_for_key[count]
            else: 
                response_text = f"<error_mock_llm_exhausted_responses_for_{chosen_key}>"
            self.call_counts[chosen_key] = count + 1
            
            mock_response_data = {
                "id": f"fake_completion_id_{chosen_key}_{count}",
                "choices": [{"message": {"content": response_text}}]
            }
        else: 
             mock_response_data = {
                "id": "fake_completion_id_no_key_match",
                "choices": [{"message": {"content": response_text}}]
            }

        response = httpx.Response(status_code, json=mock_response_data)
        response.request = httpx.Request("POST", url, json=json) # Pass original json payload
        return response

    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class MockOpenRouterAPI:
    def __init__(self):
        self.agent_responses: Dict[str, List[str]] = {} 
        self.call_counts: Dict[str, int] = {} 

    def set_responses_for_agents(self, responses: Dict[str, List[str]]):
        self.agent_responses = responses
        self.call_counts.clear() 
        print(f"[MockOpenRouterAPI] Set responses: {self.agent_responses}")

    def __call__(self, monkeypatch): 
        outer_self = self 
        def mock_async_client_constructor(*args, **kwargs):
            return MockAsyncClient(outer_self.agent_responses, outer_self.call_counts)

        monkeypatch.setattr(httpx, "AsyncClient", mock_async_client_constructor)
        print("[MockOpenRouterAPI] httpx.AsyncClient patched.")
        return self 


@pytest.fixture
def mock_openrouter_api(monkeypatch):
    mock_api_instance = MockOpenRouterAPI()
    return mock_api_instance(monkeypatch) 