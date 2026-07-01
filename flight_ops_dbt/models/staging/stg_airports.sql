with departure_airports as (

    select
        departure_airport_iata  as airport_iata,
        departure_airport_icao  as airport_icao,
        departure_airport_name  as airport_name,
        departure_timezone      as timezone
    from {{ ref('stg_flights') }}
    where departure_airport_iata is not null

),

arrival_airports as (

    select
        arrival_airport_iata    as airport_iata,
        arrival_airport_icao    as airport_icao,
        arrival_airport_name    as airport_name,
        arrival_timezone        as timezone
    from {{ ref('stg_flights') }}
    where arrival_airport_iata is not null

),

all_airports as (

    select * from departure_airports
    union
    select * from arrival_airports

),

-- One row per unique airport IATA code
deduplicated as (

    select
        airport_iata,
        airport_icao,
        airport_name,
        timezone,
        row_number() over (
            partition by airport_iata
            order by airport_name nulls last
        ) as row_num
    from all_airports

)

select
    airport_iata,
    airport_icao,
    airport_name,
    timezone
from deduplicated
where row_num = 1