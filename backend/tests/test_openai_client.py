from unittest.mock import MagicMock, patch

import pytest

from app.services.llm.base import LLMError
from app.services.llm.openai_client import OpenAIClient


def test_missing_api_key_raises_immediately():
    with pytest.raises(LLMError, match="OPENAI_API_KEY"):
        OpenAIClient(api_key="", model="gpt-5")


def _mock_openai_response(content: str) -> MagicMock:
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=content))]
    return response


@patch("app.services.llm.openai_client.openai.OpenAI")
def test_complete_json_parses_valid_json_content(mock_openai_cls):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_openai_response('{"foo": "bar"}')
    mock_openai_cls.return_value = mock_client

    client = OpenAIClient(api_key="test-key", model="gpt-5")
    result = client.complete_json(system="sys", user="usr")

    assert result == {"foo": "bar"}
    mock_client.chat.completions.create.assert_called_once()
    assert mock_client.chat.completions.create.call_args.kwargs["response_format"] == {"type": "json_object"}


@patch("app.services.llm.openai_client.openai.OpenAI")
def test_complete_json_raises_on_invalid_json(mock_openai_cls):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_openai_response("not json")
    mock_openai_cls.return_value = mock_client

    client = OpenAIClient(api_key="test-key", model="gpt-5")
    with pytest.raises(LLMError, match="not valid JSON"):
        client.complete_json(system="sys", user="usr")


@patch("app.services.llm.openai_client.openai.OpenAI")
def test_complete_json_raises_on_empty_content(mock_openai_cls):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_openai_response(None)
    mock_openai_cls.return_value = mock_client

    client = OpenAIClient(api_key="test-key", model="gpt-5")
    with pytest.raises(LLMError, match="no content"):
        client.complete_json(system="sys", user="usr")


@patch("app.services.llm.openai_client.openai.OpenAI")
def test_complete_text_returns_raw_content(mock_openai_cls):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_openai_response("hello world")
    mock_openai_cls.return_value = mock_client

    client = OpenAIClient(api_key="test-key", model="gpt-5")
    assert client.complete_text(system="sys", user="usr") == "hello world"
