{{ config(materialized='table') }}

with stg_customers as (
    select * from {{ ref('stg_customers') }}
)
select
    customer_id,
    full_name,
    email,
    city,
    registration_date
from stg_customers