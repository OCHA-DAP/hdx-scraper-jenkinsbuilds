# CLAUDE.md

## Project Overview

**hdx-scraper-elkstats** connects to an OpenSearch/ELK cluster to retrieve Jenkins build statistics for HDX scraper pipelines and classifies each build's trigger type (timer-scheduled vs. user-initiated). It uses JPype to call Jenkins Hash and cron-utils Java libraries to resolve `H`-placeholder cron expressions.

## Key Files

- `src/hdx/scraper/elkstats/__main__.py` — entry point; loads config, runs retriever, prints summary table
- `src/hdx/scraper/elkstats/elk_retriever.py` — core `ElkRetriever` class (JVM setup, OpenSearch query, trigger classification)
- `src/hdx/scraper/elkstats/config/project_configuration.yaml` — OpenSearch host, index pattern, time range, tolerance
- `src/hdx/scraper/elkstats/jars/` — bundled Java JARs (`jenkins-core`, `cron-utils`, `slf4j-api`)

## Running

```bash
uv run python -m hdx.scraper.elkstats
```

Requires:
- `APIKEY` env var — OpenSearch API key for `api.elk.aws.ahconu.org`
- Java (OpenJDK 17+) available for JPype JVM startup

## Testing

```bash
uv run pytest
```

The single test (`tests/test_elkstats.py`) verifies that Jenkins Hash correctly resolves `H` placeholders in cron expressions using known seed/expected-value pairs. It starts the JVM directly via JPype.

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
