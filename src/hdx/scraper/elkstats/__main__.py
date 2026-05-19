#!/usr/bin/python
"""
Top level script. Connects to OpenSearch/ELK to retrieve Jenkins build
statistics for HDX scraper pipelines and outputs trigger type analysis.
"""

import logging
from os.path import expanduser, join
from pathlib import Path

from hdx.api.configuration import Configuration
from hdx.api.utilities.url_utils import get_ckan_ready_session
from hdx.data.user import User
from hdx.facades.simple import facade
from hdx.utilities.downloader import Download
from hdx.utilities.path import script_dir_plus_file

from hdx.scraper.elkstats._version import __version__
from hdx.scraper.elkstats.elk_retriever import ElkRetriever

logger = logging.getLogger(__name__)

_LOOKUP = "hdx-scraper-elkstats"


def main() -> None:
    logger.info(f"##### {_LOOKUP} version {__version__} ####")
    configuration = Configuration.read()

    User.check_current_user_write_access("hdx")

    session = get_ckan_ready_session(configuration)
    with Download(session=session) as downloader:
        ElkRetriever(configuration, downloader).process()


if __name__ == "__main__":
    facade(
        main,
        user_agent_config_yaml=Path(expanduser("~"), ".useragents.yaml"),
        user_agent_lookup=_LOOKUP,
        project_config_yaml=script_dir_plus_file(
            join("config", "project_configuration.yaml"), main
        ),
    )
