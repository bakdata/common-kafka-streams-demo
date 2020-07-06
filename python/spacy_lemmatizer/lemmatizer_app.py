from typing import Dict, Union, List

from faust import TopicT
from faust.serializers.codecs import codecs
from faust_bootstrap.core.app import FaustApplication
from faust_bootstrap.core.streams.models import DeadLetter
from faust_s3_backed_serializer import S3BackedSerializer

from spacy_lemmatizer.lemmatizer.agent import create_spacy_agent
from spacy_lemmatizer.models import Text, LemmaText


class LemmatizerApp(FaustApplication):
    s3_serde: bool
    input_topics: TopicT
    output_topic: TopicT
    error_topic: TopicT

    def __init__(self):
        super(LemmatizerApp, self).__init__()

    def _register_parameters(self):
        self.register_parameter("--s3-serde", False, "Activate s3-backed SerDe as serializer", bool, default=False)

    def get_unique_app_id(self):
        return f'spacy-lemmatizer-{self.output_topic_name}'

    def get_serde_avro_from_topic(self, topic: Union[str, List[str]]):
        value = self.create_avro_serde(topic, False)
        return value

    def create_s3_serde(self, topic: Union[str, List[str]]):
        value_s3_serializer = self.create_s3_backed_serde(topic, self._generate_streams_config())
        value_avro = self.get_serde_avro_from_topic(topic)
        return value_avro | value_s3_serializer

    def create_serde(self, topic: Union[str, List[str]]):
        if self.s3_serde:
            return self.create_s3_serde(topic)
        else:
            return self.get_serde_avro_from_topic(topic)

    def setup_topics(self):
        value_serializer_input = self.create_serde(self.input_topic_names[0])
        value_serializer_output = self.create_serde(self.output_topic_name)

        schema_input = self.create_schema_from(codecs["raw"], value_serializer_input, bytes, Text)
        schema_output = self.create_schema_from(codecs["raw"], value_serializer_output, bytes, LemmaText)

        value_serializer_error = self.create_avro_serde(self.error_topic_name, False)
        schema_error = self.create_schema_from(codecs["raw"], value_serializer_error, bytes, DeadLetter)

        self.input_topics = self.get_topic_from_schema(self.input_topic_names, schema_input)
        self.output_topic = self.get_topic_from_schema(self.output_topic_name, schema_output)

        if self.error_topic_name:
            self.error_topic = self.get_topic_from_schema(self.error_topic_name, schema_error)

    def build_topology(self):
        agent = create_spacy_agent(self.output_topic, self.error_topic)
        self.create_agent(agent, self.input_topics)

    @staticmethod
    def create_s3_backed_serde(topic: str, s3_config: Dict[str, str], is_key: bool = False):
        base_path = s3_config.get("s3backed.base.path")
        max_size = int(s3_config.get("s3backed.max.byte.size"))
        region_name = s3_config.get("s3backed.region")
        faust_s3_serializer = S3BackedSerializer(topic, base_path, region_name, None, max_size,
                                                 is_key)
        return faust_s3_serializer
