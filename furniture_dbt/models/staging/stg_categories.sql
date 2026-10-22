with source as (
    select * from {{ source('raw_furniture', 'categories') }}
)
select
    category_id,
    category_name
from source