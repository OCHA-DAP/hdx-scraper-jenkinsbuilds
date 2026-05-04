import logging
from os import getenv

import pandas as pd
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.helpers import scan

logger = logging.getLogger(__name__)


class ElkRetriever:
    def __init__(self, configuration: dict):
        self._index_pattern = configuration["index_pattern"]
        self._project_prefix = configuration["project_prefix"]
        self._time_range = configuration.get("time_range", "now-1M")
        self._opensearch_host = configuration.get("opensearch_host", "api.elk.aws.ahconu.org")
        self._opensearch_port = configuration.get("opensearch_port", 443)
        self._client = self._setup_client()

    def _setup_client(self) -> OpenSearch:
        api_key = getenv("APIKEY")
        return OpenSearch(
            hosts=[{"host": self._opensearch_host, "port": self._opensearch_port}],
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

    def process(self) -> pd.DataFrame:
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"prefix": {"jenkins.projectName.keyword": self._project_prefix}},
                        {"range": {"@buildTimestamp": {"gte": self._time_range, "lte": "now"}}},
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
            index=self._index_pattern,
            scroll="2m",
            size=1000,
        )

        all_hits = []
        for hit in results:
            source = hit["_source"]
            all_hits.append({
                "projectName": self._get_field(source, "projectName", "jenkins.projectName"),
                "result": self._get_field(source, "result", "jenkins.result"),
                "buildTimestamp": source.get("@buildTimestamp"),
                "buildDuration": self._get_field(source, "buildDuration", "jenkins.buildDuration"),
                "cause": source.get("jenkins.trigger.cause"),
                "user": source.get("jenkins.trigger.related"),
            })

        df = pd.DataFrame(all_hits)

        if df.empty:
            logger.info("No builds found.")
            return df

        if not pd.api.types.is_datetime64_any_dtype(df["buildTimestamp"]):
            df["buildTimestamp"] = pd.to_datetime(df["buildTimestamp"])

        logger.info(f"Successfully retrieved {len(df)} builds.")
        return df
