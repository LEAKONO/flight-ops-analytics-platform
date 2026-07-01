-- This test fails if any two fact_flight rows share the same
-- date + flight identifier + route, which would mean
-- our codeshare deduplication logic broke.
-- A passing test returns zero rows.

select
    date_key,
    coalesce(flight_icao, flight_iata)  as flight_identifier,
    departure_airport_key,
    arrival_airport_key,
    count(*)                             as duplicate_count
from {{ ref('fact_flight') }}
group by 1, 2, 3, 4
having count(*) > 1