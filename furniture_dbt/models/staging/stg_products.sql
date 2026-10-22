with source as (
    select * from {{ source('raw_furniture', 'products') }}
)
select
    product_id,
    category_id,
    product_name,
    case 
        when price < 0 then 0.0
        else price 
    end as price,
    is_active
from source
where price >= 0