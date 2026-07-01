-- Generates one row per calendar date for a 3-year window.
-- Dates outside this range won't join to fact_flight, but the window
-- is wide enough to cover all realistic flight dates from this pipeline.

with date_spine as (

    select
        dateadd(day, seq4(), '2024-01-01'::date) as calendar_date
    from table(generator(rowcount => 1096))  -- 3 years of dates (2024-2026)

)

select
    -- Surrogate key: integer in YYYYMMDD format (fast to join, human-readable)
    to_number(to_varchar(calendar_date, 'YYYYMMDD'))    as date_key,

    calendar_date                                         as full_date,
    year(calendar_date)                                   as year,
    quarter(calendar_date)                                as quarter,
    month(calendar_date)                                  as month_number,
    monthname(calendar_date)                              as month_name,
    weekofyear(calendar_date)                             as week_of_year,
    dayofmonth(calendar_date)                             as day_of_month,
    dayofweek(calendar_date)                              as day_of_week_number,
    dayname(calendar_date)                                as day_of_week_name,
    case
        when dayofweek(calendar_date) in (0, 6) then true
        else false
    end                                                   as is_weekend,
    case
        when month(calendar_date) in (12, 1, 2) then 'Winter'
        when month(calendar_date) in (3, 4, 5)  then 'Spring'
        when month(calendar_date) in (6, 7, 8)  then 'Summer'
        else 'Autumn'
    end                                                   as season

from date_spine
order by calendar_date