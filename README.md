# HDX Scraper Jenkins Builds

Connects to OpenSearch/ELK to retrieve Jenkins build statistics for HDX scraper
pipelines and displays all build records as a formatted table in the console.

## Prerequisites

- Python 3.13
- OpenSearch API key

## Development

Install dependencies with [uv](https://docs.astral.sh/uv/):

    uv sync

Set the required environment variable:

    export APIKEY=<your-opensearch-api-key>

Run:

    uv run python -m hdx.scraper.jenkinsbuilds

## Configuration

The OpenSearch connection and query parameters are configured in
`src/hdx/scraper/jenkinsbuilds/config/project_configuration.yaml`.

## Testing

    uv run pytest

Tests cover the `ElkRetriever.process()` method using mocked OpenSearch responses,
including nested and flat document formats, empty results, timestamp conversion,
and multi-record DataFrames.

## Code Style

Install pre-commit hooks:

    pre-commit install

Run against all files:

    pre-commit run --all-files

## Build

    uv build
