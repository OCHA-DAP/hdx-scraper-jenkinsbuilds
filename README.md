# HDX Scraper ELK Stats

Connects to OpenSearch/ELK to retrieve Jenkins build statistics for HDX scraper
pipelines and outputs trigger type analysis (timer vs. user-triggered builds).

## Prerequisites

- Python 3.13
- Java 17+ (for JPype/Jenkins cron hash resolution)
- OpenSearch API key

## Development

Install dependencies with [uv](https://docs.astral.sh/uv/):

    uv sync

Set the required environment variable:

    export APIKEY=<your-opensearch-api-key>

Run:

    uv run python -m hdx.scraper.elkstats

## Configuration

The OpenSearch connection and query parameters are configured in
`src/hdx/scraper/elkstats/config/project_configuration.yaml`.

## Testing

    uv run pytest

## Code Style

Install pre-commit hooks:

    pre-commit install

Run against all files:

    pre-commit run --all-files

## Build

    uv build
