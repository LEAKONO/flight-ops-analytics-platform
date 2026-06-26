# Source System Analysis — AviationStack `flights` Endpoint

## API Characteristics
- Endpoint: `/v1/flights` (real-time only on free tier)
- Auth: API key as query parameter
- Pagination: offset-based (`limit`, `offset`, `count`, `total`)
- Quota: 100 requests/month (free tier)
- No date filtering available on free tier — true historical incremental loading is not possible until upgrade

## Data Quality Issues Observed (from real sample payloads)
1. **Null disguised as string** — `airline.name` sometimes returns the literal string `"empty"` instead of a real null
2. **Missing required-seeming fields** — `flight_status` has been observed as `null`
3. **Invalid timezone format** — `departure.timezone` sometimes returns a raw offset (`"+8"`) instead of a valid IANA zone
4. **Duplicate logical flights via codeshare** — one physical flight can appear as multiple records, each under a different marketing airline, all sharing the same operating `codeshared.flight_number`
5. **Inconsistent date logic** — arrival date has been observed appearing before departure date in raw payloads
6. **Sparse `aircraft` data** — almost entirely null on the free tier

## Field Classification Summary
| Field | Classification |
|---|---|
| `airline.*` | Dimension (`dim_airline`) |
| `departure.airport` / `arrival.airport` | Dimension (`dim_airport`, role-played) |
| `aircraft.*` | Dimension (`dim_aircraft`, low-confidence) |
| `flight_date` | Dimension (`dim_date`) |
| `flight_status`, delay fields, scheduled/actual timestamps | Fact measures |
| `flight.number`, `terminal`, `gate` | Degenerate dimensions — stored directly on fact row |
| `codeshared.*` | Second dimension reference (operating airline) + fact flag |