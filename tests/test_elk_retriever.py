from pathlib import Path
from unittest.mock import MagicMock, patch

from hdx.scraper.jenkinsbuilds.elk_retriever import ElkRetriever


def make_retriever(sample_configuration):
    config_mock = MagicMock()
    config_mock.__getitem__ = MagicMock(
        side_effect=lambda key: sample_configuration[key]
    )
    config_mock.get_hdx_site_url.return_value = "https://data.humdata.org"

    download_path = MagicMock()
    download_path.rename.return_value = Path("/tmp/jenkins_builds.csv")

    downloader_mock = MagicMock()
    downloader_mock.download_file.return_value = download_path

    with (
        patch("hdx.scraper.jenkinsbuilds.elk_retriever.OpenSearch"),
        patch(
            "hdx.scraper.jenkinsbuilds.elk_retriever.getenv",
            return_value="test-api-key",
        ),
    ):
        return ElkRetriever(config_mock, downloader_mock)


def make_hit(source: dict) -> dict:
    return {"_source": source}


NESTED_SOURCE = {
    "jenkins": {
        "projectName": "hdx-scraper-prod-run-acled",
        "result": "SUCCESS",
        "buildDuration": 450000,
    },
    "@buildTimestamp": "2026-04-01T10:00:00",
    "jenkins.trigger.cause": "timer",
    "jenkins.trigger.related": None,
}

FLAT_SOURCE = {
    "jenkins.projectName": "hdx-scraper-prod-run-fts",
    "jenkins.result": "FAILURE",
    "jenkins.buildDuration": 1800000,
    "@buildTimestamp": "2026-04-01T11:00:00",
    "jenkins.trigger.cause": "user",
    "jenkins.trigger.related": "jdoe",
}


def run_process(retriever, scan_results):
    resource_mock = MagicMock()
    dataset_mock = MagicMock()
    dataset_mock.get_resource.return_value = resource_mock

    with (
        patch(
            "hdx.scraper.jenkinsbuilds.elk_retriever.scan",
            return_value=iter(scan_results),
        ),
        patch(
            "hdx.scraper.jenkinsbuilds.elk_retriever.Dataset.read_from_hdx",
            return_value=dataset_mock,
        ),
        patch.object(retriever, "_upload_to_drive"),
    ):
        retriever.process()

    return resource_mock


def test_process_empty_results(sample_configuration):
    retriever = make_retriever(sample_configuration)
    resource_mock = run_process(retriever, [])
    resource_mock.update_datastore.assert_called_once_with([])


def test_process_nested_format(sample_configuration):
    retriever = make_retriever(sample_configuration)
    resource_mock = run_process(retriever, [make_hit(NESTED_SOURCE)])
    hits = resource_mock.update_datastore.call_args[0][0]
    assert len(hits) == 1
    assert hits[0]["projectName"] == "hdx-scraper-prod-run-acled"
    assert hits[0]["result"] == "SUCCESS"
    assert hits[0]["buildDuration"] == 7.5
    assert hits[0]["cause"] == "timer"
    assert hits[0]["user"] is None


def test_process_flat_format(sample_configuration):
    retriever = make_retriever(sample_configuration)
    resource_mock = run_process(retriever, [make_hit(FLAT_SOURCE)])
    hits = resource_mock.update_datastore.call_args[0][0]
    assert len(hits) == 1
    assert hits[0]["projectName"] == "hdx-scraper-prod-run-fts"
    assert hits[0]["result"] == "FAILURE"
    assert hits[0]["user"] == "jdoe"


def test_process_multiple_hits(sample_configuration):
    retriever = make_retriever(sample_configuration)
    resource_mock = run_process(
        retriever, [make_hit(NESTED_SOURCE), make_hit(FLAT_SOURCE)]
    )
    hits = resource_mock.update_datastore.call_args[0][0]
    assert len(hits) == 2
    assert {h["projectName"] for h in hits} == {
        "hdx-scraper-prod-run-acled",
        "hdx-scraper-prod-run-fts",
    }


def test_process_uploads_dump(sample_configuration):
    retriever = make_retriever(sample_configuration)

    resource_mock = MagicMock()
    resource_mock.__getitem__ = MagicMock(return_value="test-resource-id")
    dataset_mock = MagicMock()
    dataset_mock.get_resource.return_value = resource_mock

    with (
        patch(
            "hdx.scraper.jenkinsbuilds.elk_retriever.scan",
            return_value=iter([make_hit(NESTED_SOURCE)]),
        ),
        patch(
            "hdx.scraper.jenkinsbuilds.elk_retriever.Dataset.read_from_hdx",
            return_value=dataset_mock,
        ),
        patch.object(retriever, "_upload_to_drive"),
    ):
        retriever.process()

    expected_url = "https://data.humdata.org/datastore/dump/test-resource-id"
    resource_mock.__setitem__.assert_called_once_with("url", expected_url)
    resource_mock.pop.assert_called_once_with("url_type", None)
    resource_mock.update_in_hdx.assert_called_once()
    retriever._downloader.download_file.assert_called_once_with(expected_url)
    resource_mock.set_file_to_upload.assert_not_called()


def _make_drive_service(existing_files):
    service_mock = MagicMock()
    service_mock.files.return_value.list.return_value.execute.return_value = {
        "files": existing_files
    }
    return service_mock


def _run_upload_to_drive(retriever, service_mock):
    with (
        patch(
            "hdx.scraper.jenkinsbuilds.elk_retriever.getenv",
            return_value='{"type": "service_account"}',
        ),
        patch(
            "hdx.scraper.jenkinsbuilds.elk_retriever.Credentials.from_service_account_info"
        ),
        patch(
            "hdx.scraper.jenkinsbuilds.elk_retriever.build", return_value=service_mock
        ),
        patch("hdx.scraper.jenkinsbuilds.elk_retriever.MediaFileUpload"),
    ):
        retriever._upload_to_drive(Path("/tmp/test.csv"))


def test_upload_to_drive_creates_new_file(sample_configuration):
    retriever = make_retriever(sample_configuration)
    service_mock = _make_drive_service([])
    _run_upload_to_drive(retriever, service_mock)
    service_mock.files.return_value.create.assert_called_once()
    service_mock.files.return_value.update.assert_not_called()


def test_upload_to_drive_overwrites_existing_file(sample_configuration):
    retriever = make_retriever(sample_configuration)
    service_mock = _make_drive_service([{"id": "existing-file-id"}])
    _run_upload_to_drive(retriever, service_mock)
    service_mock.files.return_value.update.assert_called_once()
    service_mock.files.return_value.create.assert_not_called()
