import faust
from spacy_lemmatizer.lemmatizer.lemmatizer import process_text
from spacy_lemmatizer.models import Text

from faust import Record
from faust_bootstrap.core.streams.agent_utils import capture_errors, forward_error, \
    create_deadletter_message


def create_spacy_agent(output_topic, error_topic):
    async def spacy_agent(stream: faust.Stream[Text]):
        async for key, text in stream.items():
            processed = await capture_errors(text, process_text)

            if isinstance(processed, Exception):
                await forward_error(error_topic)
                yield await error_topic.send(key=key, value=create_deadletter_message(processed, text, 'Could not process text'))
            elif isinstance(processed, Record):
                yield await output_topic.send(key=key, value=processed)

    return spacy_agent
