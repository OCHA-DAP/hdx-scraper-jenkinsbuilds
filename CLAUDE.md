# CLAUDE.md

## Project Overview

**hdx-scraper-jenkinsbuilds** connects to an OpenSearch/ELK cluster to retrieve Jenkins build statistics for HDX scraper pipelines and displays all build records as a formatted table in the console.

## Key Files

- `src/hdx/scraper/jenkinsbuilds/__main__.py` — entry point; loads config, runs retriever, prints summary table
- `src/hdx/scraper/jenkinsbuilds/elk_retriever.py` — core `ElkRetriever` class (OpenSearch query, DataFrame construction)
- `src/hdx/scraper/jenkinsbuilds/config/project_configuration.yaml` — OpenSearch host, index pattern, time range

## Running

```bash
uv run python -m hdx.scraper.jenkinsbuilds
```

Requires:
- `APIKEY` env var — OpenSearch API key for `api.elk.aws.ahconu.org`

## Testing

```bash
uv run pytest
```

Tests in `tests/test_elk_retriever.py` cover `ElkRetriever.process()` using mocked OpenSearch responses.

## Code Style

- Formatted with `ruff` via pre-commit hooks (`uv run ruff format --check` to verify)
- Python ≥ 3.13
- Dependencies managed with `uv` (`uv sync` to install, `uv lock --upgrade` to update lockfile)

## Collaboration Style

- Be objective, not agreeable. Act as a partner, not a sycophant. Push back when you disagree, flag tradeoffs honestly, and don't sugarcoat problems.
- Keep explanations brief and to the point.
- Don't rely on recalled knowledge for facts that could be stale (API behaviour, library versions, external systems). Search or read the actual source first. If you lack verified information, say so rather than speculate.

## Scope of Changes

When fixing a bug or addressing PR feedback, change only what is necessary to resolve the specific issue. Do not refactor surrounding code, rename variables, adjust formatting, or make improvements in the same commit unless they are directly required by the fix. Unrelated changes obscure the intent of the fix and complicate review and blame.
