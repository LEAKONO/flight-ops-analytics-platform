# Flight Operations Analytics Platform

A production-style end-to-end data engineering platform that ingests near real-time flight data, models it dimensionally, and surfaces operational insights — built to demonstrate real-world data engineering practices, not just move data from A to B.

## Business Problem

Airline operations and business stakeholders need a way to monitor near real-time flight activity in order to identify delay patterns, evaluate airline reliability, and analyze airport traffic — enabling data-driven operational and strategic decisions.

## Tech Stack

Python · Snowflake · dbt · Apache Airflow · Power BI

## Architecture

AviationStack API → Python Ingestion → Snowflake RAW → dbt Staging → dbt Marts → Power BI
↑
Orchestrated by Airflow

## Key Design Decisions

This project is built against the AviationStack **free tier** (100 requests/month, real-time data only, no historical access or date filtering) — a deliberate constraint, not an oversight. Every component is designed so upgrading to a paid tier later requires no architectural rework, only configuration changes. See `docs/decision_records.md` for the full reasoning behind this and other key choices.

Notable engineering decisions:
- **Grain**: one fact row = one physical (operating) flight occurrence, not one row per codeshare listing — chosen deliberately to match the business questions being answered (see `docs/source_analysis.md`)
- **RAW captures everything**: no field filtering at ingestion; all selection logic lives downstream in dbt staging models
- **Idempotent loads**: safe to retry any pipeline run without creating duplicate data
- **Quota-aware**: a `CONTROL.WATERMARKS` table tracks and enforces the monthly API request budget before any call is made

## Snowflake Schema Layout

| Schema | Purpose |
|---|---|
| `RAW` | Untouched API payloads, stored as VARIANT |
| `STAGING` | Cleaned, typed, flattened records |
| `MARTS` | Dimensional model (facts + dimensions) for BI consumption |
| `AUDIT_LOGS` | Pipeline run history and observability |
| `QUARANTINE` | Records that failed data quality validation |
| `CONTROL` | Watermarks and API quota tracking |

## Ingestion Pipeline (`ingestion/`)

| File | Responsibility |
|---|---|
| `config.py` | Centralized config/secrets loading from environment variables |
| `logger.py` | Shared structured logging (console + `pipeline.log`) |
| `aviationstack_client.py` | API client with retry/backoff and rate-limit handling |
| `snowflake_loader.py` | Idempotent loads into `RAW.FLIGHTS_RAW` |
| `watermark.py` | Monthly API quota tracking and enforcement |
| `audit.py` | Writes pipeline run outcomes to `AUDIT_LOGS.PIPELINE_RUNS` |
| `run_extraction.py` | Orchestrates the full pipeline run end-to-end |

Run it with:
```bash
python3 -m ingestion.run_extraction
```

## Project Status

- [x] Phase 1: Business requirements
- [x] Phase 2: Source system analysis
- [x] Phase 3: Dimensional model design
- [x] Phase 4: Snowflake architecture
- [x] Phase 5: Pipeline design
- [x] Phase 6: Python ingestion (extraction, idempotent loads, audit, watermarking, logging)
- [ ] Phase 7: dbt (staging, marts, tests, documentation)
- [ ] Phase 8: Airflow orchestration
- [ ] Phase 9: Power BI dashboards