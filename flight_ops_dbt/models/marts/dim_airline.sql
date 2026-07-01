with source as (

    select * from {{ ref('stg_airlines') }}

),

final as (

    select
        md5(coalesce(airline_iata, airline_icao))    as airline_key,
        airline_iata,
        airline_icao,
        airline_name,
        current_timestamp()                            as dbt_updated_at

    from source

)

select * from final