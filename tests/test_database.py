from database.mlat_db import MLATDatabase


def test_database_stores_receivers_and_positions(tmp_path):
    db_path = tmp_path / "mlat.db"
    db = MLATDatabase(str(db_path))
    db.connect()

    db.store_receiver(
        receiver_id="RECV_NYC_001",
        latitude=40.7128,
        longitude=-74.0060,
        altitude=10.0,
        status="online",
        last_seen=1_700_000_000.0,
        capabilities=["mode-s", "mlat"],
    )

    receivers = db.get_receivers()
    assert len(receivers) == 1
    assert receivers[0].receiver_id == "RECV_NYC_001"

    position_id = db.store_position(
        aircraft_id="A1B2C3",
        timestamp=1_700_000_100.0,
        latitude=40.75,
        longitude=-73.85,
        altitude=9000.0,
        uncertainty=120.5,
        num_receivers=4,
        receiver_ids=["RECV_NYC_001", "RECV_BOS_001", "RECV_PHL_001", "RECV_DC_001"],
        residual=12.3,
    )

    track = db.get_aircraft_track("A1B2C3")
    assert track.num_positions == 1
    assert track.positions[0].id == position_id

    same_position_id = db.store_position(
        aircraft_id="A1B2C3",
        timestamp=1_700_000_100.0,
        latitude=40.76,
        longitude=-73.84,
        altitude=9050.0,
        uncertainty=110.0,
        num_receivers=5,
        receiver_ids=["RECV_NYC_001", "RECV_BOS_001", "RECV_PHL_001", "RECV_DC_001", "RECV_BUF_001"],
        residual=10.0,
    )

    updated_track = db.get_aircraft_track("A1B2C3")
    assert same_position_id == position_id
    assert updated_track.num_positions == 1
    assert updated_track.positions[0].latitude == 40.76
    assert updated_track.positions[0].num_receivers == 5

    positions_after = db.get_positions_after_id(position_id - 1, limit=10)
    assert len(positions_after) == 1
    assert positions_after[0].id == position_id

    db.close()
