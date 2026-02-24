import pandas as pd
import pytest
from scripts.process_and_load import validate_sales_file


def test_validation_removes_duplicates(tmp_path):
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"

    df = pd.DataFrame({
        "order_id": ["1", "1"],
        "product": ["Laptop", "Laptop"],
        "category": ["Electronics", "Electronics"],
        "sale_amount": [100, 100],
        "sale_date": ["2024-01-01", "2024-01-01"],
        "region": ["North", "North"]
    })

    df.to_csv(input_file, index=False)

    validate_sales_file(str(input_file), str(output_file))

    validated_df = pd.read_csv(output_file)

    assert len(validated_df) == 1
    
    
def test_validation_fails_on_empty(tmp_path):
    input_file = tmp_path / "empty.csv"
    output_file = tmp_path / "out.csv"

    pd.DataFrame().to_csv(input_file, index=False)

    with pytest.raises(ValueError):
        validate_sales_file(str(input_file), str(output_file))
        
        
    
        
def test_validation_fails_on_missing_column(tmp_path):
    input_file = tmp_path / "bad.csv"
    output_file = tmp_path / "out.csv"

    df = pd.DataFrame({
        "order_id": ["1"],
        "product": ["Laptop"],
        # missing category
        "sale_amount": [100],
        "sale_date": ["2024-01-01"],
        "region": ["North"]
    })

    df.to_csv(input_file, index=False)

    with pytest.raises(ValueError):
        validate_sales_file(str(input_file), str(output_file))


def test_validation_allows_extra_columns(tmp_path):
    input_file = tmp_path / "extra.csv"
    output_file = tmp_path / "out.csv"

    df = pd.DataFrame({
        "order_id": ["1"],
        "product": ["Laptop"],
        "category": ["Electronics"],
        "sale_amount": [100],
        "sale_date": ["2024-01-01"],
        "region": ["North"],
        "unexpected_column": ["oops"]
    })

    df.to_csv(input_file, index=False)

    validate_sales_file(str(input_file), str(output_file))

    validated_df = pd.read_csv(output_file)
    assert len(validated_df) == 1
    

def test_validation_removes_negative_sales(tmp_path):
    input_file = tmp_path / "neg.csv"
    output_file = tmp_path / "out.csv"

    df = pd.DataFrame({
        "order_id": ["1"],
        "product": ["Laptop"],
        "category": ["Electronics"],
        "sale_amount": [-100],
        "sale_date": ["2024-01-01"],
        "region": ["North"]
    })

    df.to_csv(input_file, index=False)

    validate_sales_file(str(input_file), str(output_file))

    validated_df = pd.read_csv(output_file)
    assert len(validated_df) == 0
    
    
def test_validation_drops_invalid_dates(tmp_path):
    input_file = tmp_path / "bad_date.csv"
    output_file = tmp_path / "out.csv"

    df = pd.DataFrame({
        "order_id": ["1"],
        "product": ["Laptop"],
        "category": ["Electronics"],
        "sale_amount": [100],
        "sale_date": ["not-a-date"],
        "region": ["North"]
    })

    df.to_csv(input_file, index=False)

    validate_sales_file(str(input_file), str(output_file))

    validated_df = pd.read_csv(output_file)
    assert len(validated_df) == 0
    
def test_validation_drops_invalid_sale_amount(tmp_path):
    input_file = tmp_path / "bad_amount.csv"
    output_file = tmp_path / "out.csv"

    df = pd.DataFrame({
        "order_id": ["1"],
        "product": ["Laptop"],
        "category": ["Electronics"],
        "sale_amount": ["invalid"],
        "sale_date": ["2024-01-01"],
        "region": ["North"]
    })

    df.to_csv(input_file, index=False)

    validate_sales_file(str(input_file), str(output_file))

    validated_df = pd.read_csv(output_file)
    assert len(validated_df) == 0
    
    
def test_validation_drops_null_order_id(tmp_path):
    input_file = tmp_path / "null.csv"
    output_file = tmp_path / "out.csv"

    df = pd.DataFrame({
        "order_id": [None],
        "product": ["Laptop"],
        "category": ["Electronics"],
        "sale_amount": [100],
        "sale_date": ["2024-01-01"],
        "region": ["North"]
    })

    df.to_csv(input_file, index=False)

    validate_sales_file(str(input_file), str(output_file))

    validated_df = pd.read_csv(output_file)
    assert len(validated_df) == 0
    
def test_validation_is_idempotent(tmp_path):
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"

    df = pd.DataFrame({
        "order_id": ["1"],
        "product": ["Laptop"],
        "category": ["Electronics"],
        "sale_amount": [100],
        "sale_date": ["2024-01-01"],
        "region": ["North"]
    })

    df.to_csv(input_file, index=False)

    validate_sales_file(str(input_file), str(output_file))
    first_pass = pd.read_csv(output_file)

    validate_sales_file(str(output_file), str(output_file))
    second_pass = pd.read_csv(output_file)

    assert first_pass.equals(second_pass)