import pytest


@pytest.fixture
def sample_configuration():
    return {
        "index_pattern": "jenkins-*",
        "project_prefix": "hdx-scraper-prod-run-",
        "time_range": "now-1M",
        "opensearch_host": "api.elk.aws.ahconu.org",
        "opensearch_port": 443,
    }
