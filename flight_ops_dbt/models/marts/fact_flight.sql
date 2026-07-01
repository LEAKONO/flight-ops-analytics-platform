with flights as (

    select * from {{ ref('stg_flights') }}

),

dim_airport as (

    select * from {{ ref('dim_airport') }}

),

dim_airline as (

    select * from {{ ref('dim_airline') }}

),

dim_aircraft as (

    select * from {{ ref('dim_aircraft') }}

),

-- GRAIN DECISION APPLIED HERE:
-- One row per physical (operating) flight occurrence.
-- For codeshare records, the operating carrier's row is identified by
-- is_codeshare = FALSE, OR if all records for a flight are codeshares,
-- we pick the one where the marketing airline matches the operating carrier.
-- We use row_number() to pick exactly one row per logical flight.
deduplicated as (

    select
        *,
        row_number() over (
            partition by
                flight_date,
                coalesce(flight_icao, flight_iata),
                departure_airport_iata,
                arrival_airport_iata
            order by
                is_codeshare asc,   -- prefer non-codeshare rows first (operating carrier)
                airline_iata asc    -- tiebreaker for stability
        ) as row_num

    from flights
    where flight_date is not null
      and departure_airport_iata is not null
      and arrival_airport_iata is not null

),

operating_flights as (

    select * from deduplicated where row_num = 1

),

final as (

    select
        -- Surrogate key for the fact row itself
        md5(
            coalesce(f.flight_date::string, '') || '|' ||
            coalesce(f.flight_icao, f.flight_iata, '') || '|' ||
            coalesce(f.departure_airport_iata, '') || '|' ||
            coalesce(f.arrival_airport_iata, '')
        )                                               as flight_key,

        -- Foreign keys to dimensions
        to_number(to_varchar(f.flight_date, 'YYYYMMDD')) as date_key,
        dep_airport.airport_key                          as departure_airport_key,
        arr_airport.airport_key                          as arrival_airport_key,
        airline.airline_key                              as airline_key,
        aircraft.aircraft_key                            as aircraft_key,

        -- Degenerate dimensions (identifiers, live on fact row)
        f.flight_number,
        f.flight_iata,
        f.flight_icao,

        -- Flight status (categorical fact)
        f.flight_status,

        -- Codeshare metadata
        f.is_codeshare,
        f.codeshare_airline_name,
        f.codeshare_flight_number,

        -- Departure measures
        f.departure_scheduled,
        f.departure_estimated,
        f.departure_actual,
        f.departure_delay_minutes,
        f.departure_terminal,
        f.departure_gate,

        -- Arrival measures
        f.arrival_scheduled,
        f.arrival_estimated,
        f.arrival_actual,
        f.arrival_delay_minutes,
        f.arrival_terminal,
        f.arrival_gate,

        -- Pipeline metadata
        f.raw_id,
        f.batch_id,
        f.ingestion_timestamp,
        current_timestamp()                              as dbt_updated_at

    from operating_flights f

    -- Join to departure airport dimension
    left join dim_airport dep_airport
        on f.departure_airport_iata = dep_airport.airport_iata

    -- Join to arrival airport dimension (same table, different role)
    left join dim_airport arr_airport
        on f.arrival_airport_iata = arr_airport.airport_iata

    -- Join to airline dimension
    left join dim_airline airline
        on coalesce(f.airline_iata, f.airline_icao)
           = coalesce(airline.airline_iata, airline.airline_icao)

    -- Join to aircraft dimension (nullable — sparse on free tier)
    left join dim_aircraft aircraft
        on f.aircraft_icao24 = aircraft.aircraft_icao24

)

select * from final