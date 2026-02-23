import csv, random, os, logging
from faker import Faker

PRODUCT_LIST = ["Laptop", "Phone", "Tablet", "Monitor", "Keyboard", "Mouse"]
CATEGORY_LIST = ["Electronics", "Accessories", "Peripherals"]
REGION_LIST   = ["North", "South", "East", "West", "Central"]

logging.basicConfig(level=logging.INFO)
fake = Faker()

def generate_sales(
    num_rows: int = 1000,
    output_path: str = "data/sales.csv",
    start_date: str = "-1y",
    end_date: str = "now",
    min_sale: float = 10.0,
    max_sale: float = 2000.0,
    random_seed: int | None = None
) -> None:
    """Generate synthetic sales data CSV."""
    if random_seed is not None:
        random.seed(random_seed)
        fake.seed_instance(random_seed)

    if num_rows <= 0:
        raise ValueError("num_rows must be > 0")
    if min_sale > max_sale:
        raise ValueError("min_sale cannot be greater than max_sale")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "order_id", "product", "category", "sale_amount", "sale_date", "region"
        ])
        writer.writeheader()

        seen_ids = set()
        for _ in range(num_rows):
            order_id = fake.uuid4()
            while order_id in seen_ids:
                order_id = fake.uuid4()
            seen_ids.add(order_id)

            writer.writerow({
                "order_id": order_id,
                "product": random.choice(PRODUCT_LIST),
                "category": random.choice(CATEGORY_LIST),
                "sale_amount": round(random.uniform(min_sale, max_sale), 2),
                "sale_date": fake.date_time_between(start_date=start_date, end_date=end_date),
                "region": random.choice(REGION_LIST),
            })
    logging.info(f"Generated {num_rows} rows → {output_path}")

if __name__ == "__main__":
    generate_sales(random_seed=42)