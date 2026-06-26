# Decision Records

## DR-1: API Tier Scoping
**Context:** AviationStack free tier = 100 requests/month, real-time `flights` endpoint only, no date filtering, no historical data.
**Decision:** Build the full architecture against the free tier now. Design every component so upgrading to a paid plan later requires only a config change — no architectural rework.

## DR-2: Business Problem Statement
**Statement:** Airline operations and business stakeholders need a way to monitor near real-time flight activity in order to identify delay patterns, evaluate airline reliability, and analyze airport traffic — enabling data-driven operational and strategic decisions.
**Why first:** Written before inspecting the API JSON, so the data model serves the business question rather than mirroring the API's incidental shape.

## DR-3: Schema Rename — AUDIT → AUDIT_LOGS
**Context:** `AUDIT` is a reserved keyword in Snowflake.
**Decision:** Renamed to `AUDIT_LOGS` across all design docs, SQL, and Python code.

## DR-4: Fact Grain
**Decision:** One fact row = one physical (operating) flight occurrence per flight date, not one row per codeshare/marketing listing.
**Why:** Delay and airport traffic are properties of the physical flight, not the commercial listing. Codeshare info is preserved as a flag + count on the fact row, not discarded.

## DR-5: RAW Captures Everything
**Decision:** `RAW.FLIGHTS_RAW` stores the entire API payload as VARIANT, regardless of which fields current KPIs use.
**Why:** Field selection is cheap to change later in dbt staging models; re-capturing lost historical data is impossible.

## DR-6: Quota Tracking via CONTROL.WATERMARKS
**Decision:** A dedicated table tracks monthly API usage and is checked before every extraction call, with a one-time manual reconciliation performed on 2026-06-24 to sync tracked usage with actual AviationStack dashboard usage (drift caused by testing done before watermark tracking was implemented).