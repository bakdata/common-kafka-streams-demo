from unittest.mock import MagicMock

from faust.serializers import codecs
from faust_avro_serializer import FaustAvroSerializer
from schema_registry.client import SchemaRegistryClient

from spacy_lemmatizer.lemmatizer.lemmatizer import process_text

APP_SCHEMA_REGISTRY = "http://127.0.0.1:8081"
APP_INPUT_TOPIC = "dummy-input"

# Mock schema registry
client = SchemaRegistryClient(APP_SCHEMA_REGISTRY)
client.register = MagicMock(name="register")
client.register.return_value = 1

faust_avro_serializer = FaustAvroSerializer(client, APP_INPUT_TOPIC)


def avro_dto_serializer():
    return faust_avro_serializer


codecs.register("avro_serializer", avro_dto_serializer())


def test_process_text(test_text, test_lemma_text):
    processed_output = process_text(test_text)
    assert test_lemma_text.dumps(serializer='avro_serializer') == processed_output.dumps(serializer='avro_serializer')
