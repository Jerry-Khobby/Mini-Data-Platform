def test_monitoring_inserts_metrics(engine):
    from scripts.monitoring import record_pipeline_run

    # Insert a monitoring record
    record_pipeline_run(
        engine=engine,
        total_rows=10,
        valid_rows=10,
        invalid_rows=0,
        invalid_ratio=0.0,
        load_duration=0.1,
        status="SUCCESS",
    )

    # Verify that the record exists
    rows = engine.execute("SELECT COUNT(*) FROM etl_monitoring").scalar()
    assert rows > 0