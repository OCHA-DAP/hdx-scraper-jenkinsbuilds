import json
import logging
from os import getenv
from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from hdx.api.configuration import Configuration
from hdx.data.dataset import Dataset
from hdx.utilities.downloader import Download
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.helpers import scan

logger = logging.getLogger(__name__)


class ElkRetriever:
    def __init__(self, configuration: Configuration, downloader: Download):
        self._configuration = configuration
        self._downloader = downloader
        self._client = self._setup_client()

    def _setup_client(self) -> OpenSearch:
        api_key = getenv("APIKEY")
        return OpenSearch(
            hosts=[
                {
                    "host": self._configuration["opensearch_host"],
                    "port": self._configuration["opensearch_port"],
                }
            ],
            connection_class=RequestsHttpConnection,
            http_compress=True,
            use_ssl=True,
            verify_certs=True,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
            send_get_body_as="POST",
            headers={
                "Authorization": f"ApiKey {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "python-requests/2.31.0",
            },
        )

    @staticmethod
    def _get_field(doc: dict, nested_key: str, flat_key: str):
        if "jenkins" in doc and isinstance(doc["jenkins"], dict):
            return doc["jenkins"].get(nested_key)
        return doc.get(flat_key)

    def process(self) -> None:
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "prefix": {
                                "jenkins.projectName.keyword": self._configuration[
                                    "project_prefix"
                                ]
                            }
                        },
                        {
                            "range": {
                                "@buildTimestamp": {
                                    "gte": self._configuration["time_range"],
                                    "lte": "now",
                                }
                            }
                        },
                    ]
                }
            },
            "_source": [
                "jenkins.projectName",
                "jenkins.result",
                "@buildTimestamp",
                "jenkins.buildDuration",
                "jenkins.trigger.cause",
                "jenkins.trigger.related",
            ],
        }

        logger.info("Executing scan query with OpenSearch...")
        results = scan(
            client=self._client,
            query=query,
            index=self._configuration["index_pattern"],
            scroll="2m",
            size=1000,
        )

        all_hits = []
        for hit in results:
            source = hit["_source"]
            all_hits.append(
                {
                    "projectName": self._get_field(
                        source, "projectName", "jenkins.projectName"
                    ),
                    "result": self._get_field(source, "result", "jenkins.result"),
                    "buildTimestamp": source.get("@buildTimestamp"),
                    "buildDuration": self._get_field(
                        source, "buildDuration", "jenkins.buildDuration"
                    ),
                    "cause": source.get("jenkins.trigger.cause"),
                    "user": source.get("jenkins.trigger.related"),
                }
            )

        dataset = Dataset.read_from_hdx("jenkins-builds")
        resource = dataset.get_resource()
        schema = [
            {"id": "projectName", "type": "text"},
            {"id": "result", "type": "text"},
            {"id": "buildTimestamp", "type": "timestamp"},
            {"id": "buildDuration", "type": "text"},
            {"id": "cause", "type": "text"},
            {"id": "user", "type": "text"},
        ]
        resource.create_datastore(schema, ("projectName", "buildTimestamp"))
        resource.update_datastore(all_hits)

        resource_id = resource["id"]
        dump_url = (
            f"{self._configuration.get_hdx_site_url()}/datastore/dump/{resource_id}"
        )
        file = self._downloader.download_file(dump_url)
        file = file.rename(file.parent / "jenkins_builds.csv")
        resource.set_file_to_upload(file)
        resource.update_in_hdx()
        self._upload_to_drive(file)

    def _upload_to_drive(self, file: Path) -> None:
        credentials = Credentials.from_service_account_info(
            json.loads(getenv("GOOGLE_SERVICE_ACCOUNT")),
            scopes=["https://www.googleapis.com/auth/drive"],
        )
        service = build("drive", "v3", credentials=credentials)
        folder_id = "1x8-HeuhrwEWYeoCZdbCc7DKD-ONPSVHU"
        media = MediaFileUpload(str(file), mimetype="text/csv")
        existing = (
            service.files()
            .list(
                q=f"name='{file.name}' and '{folder_id}' in parents and trashed=false",
                fields="files(id)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
            .get("files", [])
        )
        if existing:
            service.files().update(
                fileId=existing[0]["id"],
                media_body=media,
                supportsAllDrives=True,
            ).execute()
        else:
            service.files().create(
                body={"name": file.name, "parents": [folder_id]},
                media_body=media,
                fields="id",
                supportsAllDrives=True,
            ).execute()
