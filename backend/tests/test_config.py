import importlib

from app import config


def _reload_config():
    return importlib.reload(config)


def test_planning_weight_env_valid_values(monkeypatch):
    monkeypatch.setenv("PLANNING_TOTAL_MINUTES_WEIGHT", "-0.25")
    monkeypatch.setenv("PLANNING_TOTAL_MILES_WEIGHT", "-2.5")
    monkeypatch.setenv("PLANNING_ON_TIME_RELIABILITY_WEIGHT", "75.0")
    monkeypatch.setenv("PLANNING_RIDERS_SERVED_WEIGHT", "15.5")
    monkeypatch.setenv("PLANNING_LOAD_BALANCE_WEIGHT", "8.0")
    monkeypatch.setenv("PLANNING_CAPACITY_UTILIZATION_WEIGHT", "9.5")
    monkeypatch.setenv("PLANNING_EMPTY_SEAT_PENALTY_WEIGHT", "-3.25")

    config_module = _reload_config()

    assert config_module.settings.planning_total_minutes_weight == -0.25
    assert config_module.settings.planning_total_miles_weight == -2.5
    assert config_module.settings.planning_on_time_reliability_weight == 75.0
    assert config_module.settings.planning_riders_served_weight == 15.5
    assert config_module.settings.planning_load_balance_weight == 8.0
    assert config_module.settings.planning_capacity_utilization_weight == 9.5
    assert config_module.settings.planning_empty_seat_penalty_weight == -3.25


def test_planning_weight_env_invalid_values_fallback(monkeypatch):
    monkeypatch.setenv("PLANNING_TOTAL_MINUTES_WEIGHT", "invalid")
    monkeypatch.setenv("PLANNING_TOTAL_MILES_WEIGHT", "oops")
    monkeypatch.setenv("PLANNING_ON_TIME_RELIABILITY_WEIGHT", "x")
    monkeypatch.setenv("PLANNING_RIDERS_SERVED_WEIGHT", "??")
    monkeypatch.setenv("PLANNING_LOAD_BALANCE_WEIGHT", "NaN?")
    monkeypatch.setenv("PLANNING_CAPACITY_UTILIZATION_WEIGHT", "invalid")
    monkeypatch.setenv("PLANNING_EMPTY_SEAT_PENALTY_WEIGHT", "bad")

    config_module = _reload_config()

    assert config_module.settings.planning_total_minutes_weight == -0.05
    assert config_module.settings.planning_total_miles_weight == -1.0
    assert config_module.settings.planning_on_time_reliability_weight == 50.0
    assert config_module.settings.planning_riders_served_weight == 10.0
    assert config_module.settings.planning_load_balance_weight == 5.0
    assert config_module.settings.planning_capacity_utilization_weight == 6.0
    assert config_module.settings.planning_empty_seat_penalty_weight == -2.0


def test_planning_weight_env_empty_values_fallback(monkeypatch):
    # Explicitly set env vars to empty strings; _float_env should treat these as missing
    monkeypatch.setenv("PLANNING_TOTAL_MINUTES_WEIGHT", "")
    monkeypatch.setenv("PLANNING_TOTAL_MILES_WEIGHT", "")
    monkeypatch.setenv("PLANNING_ON_TIME_RELIABILITY_WEIGHT", "")
    monkeypatch.setenv("PLANNING_RIDERS_SERVED_WEIGHT", "")
    monkeypatch.setenv("PLANNING_LOAD_BALANCE_WEIGHT", "")
    monkeypatch.setenv("PLANNING_CAPACITY_UTILIZATION_WEIGHT", "")
    monkeypatch.setenv("PLANNING_EMPTY_SEAT_PENALTY_WEIGHT", "")

    config_module = _reload_config()

    # Empty strings should fall back to the same defaults used when env vars are missing/invalid
    assert config_module.settings.planning_total_minutes_weight == -0.05
    assert config_module.settings.planning_total_miles_weight == -1.0
    assert config_module.settings.planning_on_time_reliability_weight == 50.0
    assert config_module.settings.planning_riders_served_weight == 10.0
    assert config_module.settings.planning_load_balance_weight == 5.0
    assert config_module.settings.planning_capacity_utilization_weight == 6.0
    assert config_module.settings.planning_empty_seat_penalty_weight == -2.0


def test_planning_weight_env_empty_values_fallback(monkeypatch):
    monkeypatch.setenv("PLANNING_TOTAL_MINUTES_WEIGHT", "")
    monkeypatch.setenv("PLANNING_TOTAL_MILES_WEIGHT", "   ")
    monkeypatch.setenv("PLANNING_ON_TIME_RELIABILITY_WEIGHT", "")
    monkeypatch.setenv("PLANNING_RIDERS_SERVED_WEIGHT", " ")
    monkeypatch.setenv("PLANNING_LOAD_BALANCE_WEIGHT", "")
    monkeypatch.setenv("PLANNING_CAPACITY_UTILIZATION_WEIGHT", " ")
    monkeypatch.setenv("PLANNING_EMPTY_SEAT_PENALTY_WEIGHT", "")

    config_module = _reload_config()

    assert config_module.settings.planning_total_minutes_weight == -0.05
    assert config_module.settings.planning_total_miles_weight == -1.0
    assert config_module.settings.planning_on_time_reliability_weight == 50.0
    assert config_module.settings.planning_riders_served_weight == 10.0
    assert config_module.settings.planning_load_balance_weight == 5.0
    assert config_module.settings.planning_capacity_utilization_weight == 6.0
    assert config_module.settings.planning_empty_seat_penalty_weight == -2.0


def test_planning_weight_env_non_finite_values_fallback(monkeypatch):
    monkeypatch.setenv("PLANNING_TOTAL_MINUTES_WEIGHT", "nan")
    monkeypatch.setenv("PLANNING_TOTAL_MILES_WEIGHT", "inf")
    monkeypatch.setenv("PLANNING_ON_TIME_RELIABILITY_WEIGHT", "-inf")
    monkeypatch.setenv("PLANNING_CAPACITY_UTILIZATION_WEIGHT", "nan")
    monkeypatch.setenv("PLANNING_EMPTY_SEAT_PENALTY_WEIGHT", "inf")

    config_module = _reload_config()

    assert config_module.settings.planning_total_minutes_weight == -0.05
    assert config_module.settings.planning_total_miles_weight == -1.0
    assert config_module.settings.planning_on_time_reliability_weight == 50.0
    assert config_module.settings.planning_capacity_utilization_weight == 6.0
    assert config_module.settings.planning_empty_seat_penalty_weight == -2.0


def test_planning_weight_env_missing_values_use_defaults(monkeypatch):
    monkeypatch.delenv("PLANNING_TOTAL_MINUTES_WEIGHT", raising=False)
    monkeypatch.delenv("PLANNING_TOTAL_MILES_WEIGHT", raising=False)
    monkeypatch.delenv("PLANNING_ON_TIME_RELIABILITY_WEIGHT", raising=False)
    monkeypatch.delenv("PLANNING_RIDERS_SERVED_WEIGHT", raising=False)
    monkeypatch.delenv("PLANNING_LOAD_BALANCE_WEIGHT", raising=False)
    monkeypatch.delenv("PLANNING_CAPACITY_UTILIZATION_WEIGHT", raising=False)
    monkeypatch.delenv("PLANNING_EMPTY_SEAT_PENALTY_WEIGHT", raising=False)

    config_module = _reload_config()

    assert config_module.settings.planning_total_minutes_weight == -0.05
    assert config_module.settings.planning_total_miles_weight == -1.0
    assert config_module.settings.planning_on_time_reliability_weight == 50.0
    assert config_module.settings.planning_riders_served_weight == 10.0
    assert config_module.settings.planning_load_balance_weight == 5.0
    assert config_module.settings.planning_capacity_utilization_weight == 6.0
    assert config_module.settings.planning_empty_seat_penalty_weight == -2.0


def test_planning_weight_env_invalid_values_log_warning(monkeypatch, caplog):
    caplog.set_level("WARNING")
    monkeypatch.setenv("PLANNING_TOTAL_MINUTES_WEIGHT", "invalid")

    _reload_config()

    assert "Invalid float env PLANNING_TOTAL_MINUTES_WEIGHT='invalid' (parse failure); using default -0.05" in caplog.text
