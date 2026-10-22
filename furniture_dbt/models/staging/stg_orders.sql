with source as (
    select * from {{ source('raw_furniture', 'orders') }}
)
select
    order_id,
    customer_id,
    product_id,
    quantity,
    status,
    cast(order_date as timestamp) as created_at
from source