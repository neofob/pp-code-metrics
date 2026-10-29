# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project Overview

`pp-code-metrics` collects environmental sensor metrics from `pp-code` devices via their local HTTP endpoint and writes them to InfluxDB for visualization in Grafana.

## Repository Layout

- `get_metrics.py` — standalone Python script that fetches metrics from a sensor HTTP endpoint and write them to InfluxDB. `get_metrics.py` is the canonical entry point.
- `tests/` — unit tests for the metrics collector (run with `python -m pytest tests/`).
- `sample_settings.yml`, `my_settings.yml`, `sample_settings.yml.j2` — YAML sensor and InfluxDB configuration.
- `requirements.txt` — Python dependencies (`pyyaml`, `requests`, `influxdb-client`, `yamllint`).
- `Dockerfile`, `docker-compose*.yml`, `Makefile`, `run_get_metrics.sh` — Docker-based deployment.
- `crontab/`, `screenshots/`, `db.json` — operational artifacts.

## Setup and Running

- Requires Python 3.11+ (see `Dockerfile`).
- Install dependencies: `pip install -r requirements.txt`.
- Run a collector: `python get_metrics.py --config my_settings.yml`.

## Code Style

All Python code in this repository must follow PEP 8 and be Pythonic.

- Follow PEP 8: 4-space indentation, max line length of 88 characters.
- Naming: `snake_case` for modules, functions, methods, and variables; `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants. New code must use `snake_case` (e.g., `get_metric`, not `getMetric`).
- Docstrings: use triple double quotes (`"""`) for modules and public functions.
- Formatting: prefer f-strings over `%` formatting or string concatenation.
- Resources: use `with` statements / context managers for files and external clients (e.g., the InfluxDB `WriteApi`).
- Exceptions: avoid bare `except:` clauses; catch specific exception types.
- Structure: keep logic in functions; use the `if __name__ == '__main__':` guard for script entry points.

Note: some legacy scripts (`get_metrics.py`) use older naming conventions; new code should follow the PEP 8 / Pythonic conventions above.

## Verification

- Run the automated Python unit tests with `python -m pytest tests/` (requires `pytest`).
- Validate changes with `python -m py_compile <script>.py`.
- Lint YAML files with `yamllint`.
- Lint Python code with `ruff check .` (line length set to 88).
