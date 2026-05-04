#!/usr/bin/python
"""
Top level script. Connects to OpenSearch/ELK to retrieve Jenkins build
statistics for HDX scraper pipelines and outputs trigger type analysis.
"""

import logging
from pathlib import Path

import pandas as pd
import yaml

from hdx.scraper.elkstats._version import __version__
from hdx.scraper.elkstats.elk_retriever import ElkRetriever

logger = logging.getLogger(__name__)

_LOOKUP = "hdx-scraper-elkstats"


def main() -> None:
    logger.info(f"##### {_LOOKUP} version {__version__} ####")
    config_path = Path(__file__).parent / "config" / "project_configuration.yaml"
    with open(config_path) as f:
        configuration = yaml.safe_load(f)

    df = ElkRetriever(configuration).process()

    if not df.empty:
        print(f"Successfully retrieved {len(df)} builds.\n")
        with pd.option_context("display.max_rows", None, "display.max_columns", None, "display.width", None):
            print(df.fillna("").to_string(index=False))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
