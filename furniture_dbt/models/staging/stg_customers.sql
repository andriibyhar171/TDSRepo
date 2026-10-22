with source as (
    select * from {{ source('raw_furniture', 'customers') }}
),
deduped as (
    select
        customer_id,
        full_name,
        coalesce(email, 'unknown@example.com') as email,
        city,
        cast(registration_date as date) as registration_date,
        row_number() over (partition by customer_id order by registration_date desc) as rn
    from source
)
select
    customer_id,
    full_name,
    email,
    city,
    registration_date
from deduped
where rn = 1