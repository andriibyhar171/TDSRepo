{{ config(materialized='table') }}

with stg_orders as (
    select * from {{ ref('stg_orders') }}
),
stg_products as (
    select * from {{ ref('stg_products') }}
),
stg_customers as (
    select * from {{ ref('stg_customers') }}
)
select
    o.order_id,
    o.customer_id,
    o.product_id,
    o.quantity,
    p.price as unit_price,
    round(cast(o.quantity * p.price as numeric), 2) as total_amount,
    o.status,
    o.created_at
from stg_orders o
inner join stg_customers c on o.customer_id = c.customer_id
inner join stg_products p on o.product_id = p.product_id