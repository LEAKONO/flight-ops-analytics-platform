with source as (

    select
        aircraft_icao24,
        aircraft_registration,
        aircraft_type_iata,
        aircraft_type_icao
    from {{ ref('stg_flights') }}
    where aircraft_icao24 is not null

),

deduplicated as (

    select
        aircraft_icao24,
        aircraft_registration,
        aircraft_type_iata,
        aircraft_type_icao,
        row_number() over (
            partition by aircraft_icao24
            order by aircraft_registration nulls last
        ) as row_num
    from source

)

select
    aircraft_icao24,
    aircraft_registration,
    aircraft_type_iata,
    aircraft_type_icao
from deduplicated
where row_num = 1