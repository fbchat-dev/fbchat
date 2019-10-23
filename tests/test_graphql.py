import pytest
import json
from fbchat._graphql import ConcatJSONDecoder, queries_to_json, response_to_json


@pytest.mark.parametrize(
    "content,result",
    [
        ("", []),
        ('{"a":"b"}', [{"a": "b"}]),
        ('{"a":"b"}{"b":"c"}', [{"a": "b"}, {"b": "c"}]),
        (' \n{"a":  "b"  }     \n {  "b" \n\n : "c" }', [{"a": "b"}, {"b": "c"}]),
    ],
)
def test_concat_json_decoder(content, result):
    assert result == json.loads(content, cls=ConcatJSONDecoder)


def test_queries_to_json():
    assert {"q0": "A", "q1": "B", "q2": "C"} == json.loads(
        queries_to_json("A", "B", "C")
    )


def test_response_to_json():
    data = (
        '{"q1":{"data":{"b":"c"}}}\r\n'
        '{"q0":{"response":[1,2]}}\r\n'
        "{\n"
        '   "successful_results": 2,\n'
        '   "error_results": 0,\n'
        '   "skipped_results": 0\n'
        "}"
    )
    assert [[1, 2], {"b": "c"}] == response_to_json(data)
