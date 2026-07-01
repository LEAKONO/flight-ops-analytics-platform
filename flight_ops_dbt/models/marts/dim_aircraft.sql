with source as (

    select * from {{ ref('stg_aircraft') }}

),

final as (

    select
        md5(aircraft_icao24)                          as aircraft_key,
        aircraft_icao24,
        aircraft_registration,
        aircraft_type_iata,
        aircraft_type_icao,
        current_timestamp()                            as dbt_updated_at

    from source

)

select * from final