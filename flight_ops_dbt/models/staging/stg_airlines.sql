with marketing_airlines as (

    select
        airline_iata    as airline_iata,
        airline_icao    as airline_icao,
        airline_name    as airline_name
    from {{ ref('stg_flights') }}
    where airline_iata is not null
       or airline_icao is not null

),

operating_airlines as (

    -- Codeshare operating carriers are a second source of airline entities
    select
        codeshare_airline_iata  as airline_iata,
        codeshare_airline_icao  as airline_icao,
        codeshare_airline_name  as airline_name
    from {{ ref('stg_flights') }}
    where is_codeshare = true
      and codeshare_airline_iata is not null

),

all_airlines as (

    select * from marketing_airlines
    union
    select * from operating_airlines

),

deduplicated as (

    select
        airline_iata,
        airline_icao,
        airline_name,
        row_number() over (
            partition by coalesce(airline_iata, airline_icao)
            order by airline_name nulls last
        ) as row_num
    from all_airlines

)

select
    airline_iata,
    airline_icao,
    airline_name
from deduplicated
where row_num = 1