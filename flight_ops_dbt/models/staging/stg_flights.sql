with source as (
    select
        raw_id,
        batch_id,
        pipeline_run_id,
        ingestion_timestamp,
        raw_payload
    from {{ source('raw', 'flights_raw') }}

),

cleaned as (

    select
        raw_id,
        batch_id,
        pipeline_run_id,
        ingestion_timestamp,

        -- Date / status
        raw_payload:flight_date::date                              as flight_date,
        raw_payload:flight_status::string                          as flight_status,

        -- Departure
        raw_payload:departure.airport::string                      as departure_airport_name,
        raw_payload:departure.iata::string                         as departure_airport_iata,
        raw_payload:departure.icao::string                         as departure_airport_icao,
        raw_payload:departure.timezone::string                     as departure_timezone,
        raw_payload:departure.terminal::string                     as departure_terminal,
        raw_payload:departure.gate::string                         as departure_gate,
        raw_payload:departure.delay::number                        as departure_delay_minutes,
        raw_payload:departure.scheduled::timestamp_tz               as departure_scheduled,
        raw_payload:departure.estimated::timestamp_tz               as departure_estimated,
        raw_payload:departure.actual::timestamp_tz                  as departure_actual,

        -- Arrival
        raw_payload:arrival.airport::string                        as arrival_airport_name,
        raw_payload:arrival.iata::string                           as arrival_airport_iata,
        raw_payload:arrival.icao::string                           as arrival_airport_icao,
        raw_payload:arrival.timezone::string                       as arrival_timezone,
        raw_payload:arrival.terminal::string                       as arrival_terminal,
        raw_payload:arrival.gate::string                           as arrival_gate,
        raw_payload:arrival.delay::number                          as arrival_delay_minutes,
        raw_payload:arrival.scheduled::timestamp_tz                 as arrival_scheduled,
        raw_payload:arrival.estimated::timestamp_tz                 as arrival_estimated,
        raw_payload:arrival.actual::timestamp_tz                    as arrival_actual,

        -- Airline (marketing carrier on this record)
        case
            when raw_payload:airline.name::string = 'empty' then null
            else raw_payload:airline.name::string
        end                                                          as airline_name,
        raw_payload:airline.iata::string                           as airline_iata,
        raw_payload:airline.icao::string                           as airline_icao,

        -- Flight identifiers (degenerate dimension)
        raw_payload:flight.number::string                          as flight_number,
        raw_payload:flight.iata::string                            as flight_iata,
        raw_payload:flight.icao::string                            as flight_icao,

        -- Codeshare (operating carrier reference, when present)
        raw_payload:flight.codeshared.airline_name::string         as codeshare_airline_name,
        raw_payload:flight.codeshared.airline_iata::string         as codeshare_airline_iata,
        raw_payload:flight.codeshared.airline_icao::string         as codeshare_airline_icao,
        raw_payload:flight.codeshared.flight_number::string        as codeshare_flight_number,
        (raw_payload:flight.codeshared is not null)                 as is_codeshare,

        -- Aircraft (sparse on free tier)
        raw_payload:aircraft.registration::string                  as aircraft_registration,
        raw_payload:aircraft.icao24::string                        as aircraft_icao24,
        raw_payload:aircraft.iata::string                          as aircraft_type_iata,
        raw_payload:aircraft.icao::string                          as aircraft_type_icao

    from source

)

select * from cleaned