import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from faker import Faker
from sqlalchemy import create_engine, text

# Ініціалізація генератора
fake = Faker('uk_UA')
Faker.seed(42)
random.seed(42)

os.makedirs('data_lake', exist_ok=True)

# 1. ТАБЛИЦІ ВИМІРІВ (DIMENSIONS)
def generate_categories():
    print("Генерація категорій меблів...")
    categories = [
        'М’які меблі (дивани, крісла)',
        'Спальня (ліжка, матраци)',
        'Корпусні меблі (шафи, комоди)',
        'Столи та стільці',
        'Кухонні гарнітури',
        'Офісні та кабінетні меблі',
        'Меблі для передпокою'
    ]
    data = []
    for i, cat in enumerate(categories, start=1):
        data.append({
            'category_id': i,
            'category_name': cat
        })
    return pd.DataFrame(data)


def generate_products(n, category_ids):
    print(f"Генерація {n} товарів (меблів)...")
    furniture_types = [
        'Диван кутовий', 'Крісло розкладне', 'Ліжко двоспальне', 
        'Ортопедичний матрац', 'Шафа-купе', 'Комод', 
        'Обідній стіл', 'Стілець ергономічний', 'Офісне крісло', 'Тумба під ТВ'
    ]
    materials = ['Дуб', 'Сосна', 'Бук', 'Екошкіра', 'Велюр', 'МДФ', 'Метал']
    
    data = []
    for i in range(1, n + 1):
        p_name = f"{random.choice(furniture_types)} «{fake.first_name()}» ({random.choice(materials)})"
        data.append({
            'product_id': i,
            'category_id': random.choice(category_ids),
            'product_name': p_name,
            'price': round(random.uniform(1500.0, 45000.0), 2),
            'is_active': random.choice([True, True, True, False])
        })
    return pd.DataFrame(data)


def generate_customers(n):
    print(f"Генерація {n} покупців (з імітацією 'брудних' даних)...")
    data = []
    for i in range(1, n + 1):
        # 10% пропущених email для перевірки очищення в ЛР №2
        email = fake.email() if random.random() > 0.1 else None
        data.append({
            'customer_id': i,
            'full_name': fake.name(),
            'email': email,
            'city': fake.city(),
            'registration_date': fake.date_between(start_date='-2y', end_date='today')
        })
    df = pd.DataFrame(data)

    # 5% дублікатів записів
    duplicates = df.sample(frac=0.05, random_state=42)
    df = pd.concat([df, duplicates], ignore_index=True)
    return df



# 2. ТАБЛИЦІ ФАКТІВ
def generate_orders(n, customer_ids, product_ids):
    print(f"Генерація {n} замовлень...")
    data = []
    for i in range(1, n + 1):
        order_date = fake.date_time_between(start_date='-1y', end_date='now')
        data.append({
            'order_id': i,
            'customer_id': random.choice(customer_ids),
            'product_id': random.choice(product_ids),
            'quantity': random.randint(1, 4),
            'order_date': order_date,
            'status': random.choices(['completed', 'pending', 'cancelled'], weights=[80, 15, 5])[0]
        })
    return pd.DataFrame(data)


def generate_reviews(n, customer_ids, product_ids):
    print(f"Генерація {n} відгуків...")
    data = []
    for i in range(1, n + 1):
        # 20% коментарів є пустими (NULL) за вимогою завдання
        comment = None if random.random() <= 0.2 else fake.sentence(nb_words=12)
        data.append({
            'review_id': i,
            'customer_id': random.choice(customer_ids),
            'product_id': random.choice(product_ids),
            'rating': random.randint(1, 5),
            'review_date': fake.date_time_between(start_date='-1y', end_date='now'),
            'comment': comment
        })
    return pd.DataFrame(data)


# 3. ОСНОВНИЙ ЦИКЛ ГЕНЕРАЦІЇ ТА ЗАВАНТАЖЕННЯ (INGESTION)
DB_URL = "postgresql://admin:adminpassword@localhost:5432/furniture_dwh"

def load_data_to_dwh():
    print("--- 1. Створення датасетів ---")
    df_categories = generate_categories()
    df_products = generate_products(60, df_categories['category_id'].tolist())
    df_customers = generate_customers(500)

    # Для зв'язків беремо лише валідні унікальні ID
    valid_customer_ids = df_customers['customer_id'].dropna().unique().tolist()
    product_ids = df_products['product_id'].tolist()

    df_orders = generate_orders(4000, valid_customer_ids, product_ids)
    df_reviews = generate_reviews(1200, valid_customer_ids, product_ids)

    print("\n--- 2. Збереження у Data Lake (Parquet) ---")
    df_categories.to_parquet('data_lake/raw_categories.parquet', index=False)
    df_products.to_parquet('data_lake/raw_products.parquet', index=False)
    df_customers.to_parquet('data_lake/raw_customers.parquet', index=False)
    df_orders.to_parquet('data_lake/raw_orders.parquet', index=False)
    df_reviews.to_parquet('data_lake/raw_reviews.parquet', index=False)
    print("Файли успішно записані у папку data_lake/.")

    print("\n--- 3. Завантаження у PostgreSQL (шар raw) ---")
    engine = create_engine(DB_URL)

    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
        conn.commit()

    df_categories.to_sql('categories', engine, schema='raw', if_exists='replace', index=False)
    print("-> raw.categories завантажено")
    df_products.to_sql('products', engine, schema='raw', if_exists='replace', index=False)
    print("-> raw.products завантажено")
    df_customers.to_sql('customers', engine, schema='raw', if_exists='replace', index=False)
    print("-> raw.customers завантажено")
    df_orders.to_sql('orders', engine, schema='raw', if_exists='replace', index=False)
    print("-> raw.orders завантажено")
    df_reviews.to_sql('reviews', engine, schema='raw', if_exists='replace', index=False)
    print("-> raw.reviews завантажено")

    print("\nДані успішно завантажено в DWH у схему 'raw'!")

if __name__ == "__main__":
    load_data_to_dwh()