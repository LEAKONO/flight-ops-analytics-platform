with source as (

    select * from {{ ref('stg_airports') }}

),

final as (

    select
        -- Surrogate key: hash of natural key (airport_iata)
        md5(coalesce(airport_iata, airport_icao))   as airport_key,
        airport_iata,
        airport_icao,
        airport_name,
        -- Flag invalid timezone formats from source (e.g. "+8" is not a valid IANA zone)
        case
            when timezone like '+%'
              or timezone like '-%'
              or timezone is null
            then null
            else timezone
        end                                           as timezone,
        -- Metadata
        current_timestamp()                           as dbt_updated_at

    from source

)

select * from final