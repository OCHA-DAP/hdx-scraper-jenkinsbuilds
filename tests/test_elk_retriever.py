from unittest.mock import patch

import pandas as pd

from hdx.scraper.elkstats.elk_retriever import ElkRetriever


def make_retriever(sample_configuration):
    with (
        patch("hdx.scraper.elkstats.elk_retriever.OpenSearch"),
        patch("hdx.scraper.elkstats.elk_retriever.getenv", return_value="test-api-key"),
    ):
        return ElkRetriever(sample_configuration)


def make_hit(source: dict) -> dict:
    return {"_source": source}


NESTED_SOURCE = {
    "jenkins": {
        "projectName": "hdx-scraper-prod-run-acled",
        "result": "SUCCESS",
        "buildDuration": 120000,
    },
    "@buildTimestamp": "2026-04-01T10:00:00",
    "jenkins.trigger.cause": "timer",
    "jenkins.trigger.related": None,
}

FLAT_SOURCE = {
    "jenkins.projectName": "hdx-scraper-prod-run-fts",
    "jenkins.result": "FAILURE",
    "jenkins.buildDuration": 60000,
    "@buildTimestamp": "2026-04-01T11:00:00",
    "jenkins.trigger.cause": "user",
    "jenkins.trigger.related": "jdoe",
}


def test_process_empty_results(sample_configuration):
    retriever = make_retriever(sample_configuration)
    with patch("hdx.scraper.elkstats.elk_retriever.scan", return_value=iter([])):
        df = retriever.process()

    assert df.empty


def test_process_nested_format(sample_configuration):
    retriever = make_retriever(sample_configuration)
    with patch(
        "hdx.scraper.elkstats.elk_retriever.scan",
        return_value=iter([make_hit(NESTED_SOURCE)]),
    ):
        df = retriever.process()

    assert len(df) == 1
    assert df.iloc[0]["projectName"] == "hdx-scraper-prod-run-acled"
    assert df.iloc[0]["result"] == "SUCCESS"
    assert df.iloc[0]["buildDuration"] == 120000
    assert df.iloc[0]["cause"] == "timer"
    assert pd.isna(df.iloc[0]["user"])


def test_process_flat_format(sample_configuration):
    retriever = make_retriever(sample_configuration)
    with patch(
        "hdx.scraper.elkstats.elk_retriever.scan",
        return_value=iter([make_hit(FLAT_SOURCE)]),
    ):
        df = retriever.process()

    assert len(df) == 1
    assert df.iloc[0]["projectName"] == "hdx-scraper-prod-run-fts"
    assert df.iloc[0]["result"] == "FAILURE"
    assert df.iloc[0]["user"] == "jdoe"


def test_process_timestamp_converted_to_datetime(sample_configuration):
    retriever = make_retriever(sample_configuration)
    with patch(
        "hdx.scraper.elkstats.elk_retriever.scan",
        return_value=iter([make_hit(NESTED_SOURCE)]),
    ):
        df = retriever.process()

    assert pd.api.types.is_datetime64_any_dtype(df["buildTimestamp"])


def test_process_multiple_hits(sample_configuration):
    retriever = make_retriever(sample_configuration)
    with patch(
        "hdx.scraper.elkstats.elk_retriever.scan",
        return_value=iter([make_hit(NESTED_SOURCE), make_hit(FLAT_SOURCE)]),
    ):
        df = retriever.process()

    assert len(df) == 2
    assert set(df.columns) == {
        "projectName",
        "result",
        "buildTimestamp",
        "buildDuration",
        "cause",
        "user",
    }
