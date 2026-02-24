import os
import pandas as pd
from scripts.generate_data import generate_sales


def test_generate_sales_creates_file(tmp_path):
    output_file = tmp_path / "sales.csv"

    generate_sales(
        num_rows=100,
        output_path=str(output_file),
        random_seed=42,
    )

    assert output_file.exists()

    df = pd.read_csv(output_file)
    assert len(df) == 100
    assert "order_id" in df.columns