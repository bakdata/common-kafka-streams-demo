from typing import List

from faust import Record


class Text(Record):
    _schema = {
        "fields": [
            {
                "name": "content",
                "type": {
                    "avro.java.string": "String",
                    "type": "string"
                }
            }
        ],
        "name": "Text",
        "namespace": "com.bakdata.kafka",
        "type": "record"
    }
    content: str


class LemmaText(Record):
    _schema = {
        "fields": [
            {
                "name": "lemmas",
                "type": {
                    "items": "string",
                    "type": "array"
                }
            }
        ],
        "name": "LemmaText",
        "namespace": "com.bakdata.kafka",
        "type": "record"
    }
    lemmas: List[str] = []
