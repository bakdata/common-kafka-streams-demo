import sys
from unittest.mock import MagicMock, patch

import pytest

from spacy_lemmatizer.start import app as lemmatizer_app


@pytest.fixture
def mocked_coroutine():
    def mock_coro(return_value=None, **kwargs):
        async def wrapped(*args, **kwargs):
            return return_value

        return MagicMock(wraps=wrapped, **kwargs)

    return mock_coro()


@pytest.fixture(scope="module")
def app_test():
    sys.argv = []
    lemmatizer_app._FaustApplication__load_app()
    app = lemmatizer_app.app
    app.finalize()
    app.conf.store = 'memory://'
    app.flow_control.resume()
    spacy_agent = lemmatizer_app.app.agents.data.get('spacy_lemmatizer.lemmatizer.agent.spacy_agent')
    return lemmatizer_app, spacy_agent


@pytest.mark.asyncio()
async def test_error_deadletter(app_test, mocked_coroutine):
    lemmatizer_app, spacy_agent = app_test
    with patch.object(lemmatizer_app.error_topic, "send", mocked_coroutine):
        async with spacy_agent.test_context() as agent:
            await agent.put("DummyMessage")
            assert lemmatizer_app.error_topic.send.called, "The error topic should be called"
            deadletter = lemmatizer_app.error_topic.send.call_args[1]["value"]
            assert deadletter.input_value == "DummyMessage", "Message should be the same as the agent input"
            assert deadletter.description == "Could not process text", "The Text should not be able to be processed"


@pytest.mark.asyncio()
async def test_input_sent_success(app_test, test_text, test_lemma_text, mocked_coroutine):
    lemmatizer_app, spacy_agent = app_test
    with patch.object(lemmatizer_app.output_topic, "send", mocked_coroutine):
        async with spacy_agent.test_context() as agent:
            await agent.put(test_text)
            assert lemmatizer_app.output_topic.send.called, "The output topic should be called"
            outputLemmaText = lemmatizer_app.output_topic.send.call_args[1]["value"]
            assert outputLemmaText == test_lemma_text, 'The output should be type LemmaText and only include' \
                                                       ' non-stopword and alpha lemmatized tokens'
