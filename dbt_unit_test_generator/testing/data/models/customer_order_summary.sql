with customers as (
    select * from {{ source('crm', 'customers') }}
),

orders as (
    select * from {{ source('sales', 'orders') }}
),

final as (
    select 
        c.customer_id,
        c.first_name,
        c.last_name,
        c.email,
        count(o.order_id) as total_orders,
        sum(o.order_amount) as total_spent,
        max(o.order_date) as last_order_date
    from customers c
    left join orders o 
        on c.customer_id = o.customer_id
    group by 
        c.customer_id,
        c.first_name,
        c.last_name,
        c.email
)

select * from final