import os
import math
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
_WARNED_INVALID_FLOAT_ENVS: set[str] = set()


def _warn_default_once(name: str, raw: str, default: float, reason: str) -> None:
    if name in _WARNED_INVALID_FLOAT_ENVS:
        return
    _WARNED_INVALID_FLOAT_ENVS.add(name)
    logger.warning(
        "Invalid float env %s=%r (%s); using default %s",
        name,
        raw,
        reason,
        default,
    )


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip()
    if normalized == "":
        _warn_default_once(name, raw, default, "blank value")
        return default
    try:
        value = float(normalized)
    except ValueError:
        _warn_default_once(name, raw, default, "parse failure")
        return default
    if not math.isfinite(value):
        _warn_default_once(name, raw, default, "non-finite value")
        return default
    return value


class Settings:
    app_name: str = os.getenv("APP_NAME", "Driving Matrix API")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    planning_total_minutes_weight: float = _float_env("PLANNING_TOTAL_MINUTES_WEIGHT", -0.05)
    planning_total_miles_weight: float = _float_env("PLANNING_TOTAL_MILES_WEIGHT", -1.0)
    planning_on_time_reliability_weight: float = _float_env("PLANNING_ON_TIME_RELIABILITY_WEIGHT", 50.0)
    planning_riders_served_weight: float = _float_env("PLANNING_RIDERS_SERVED_WEIGHT", 10.0)
    planning_load_balance_weight: float = _float_env("PLANNING_LOAD_BALANCE_WEIGHT", 5.0)
    planning_capacity_utilization_weight: float = _float_env("PLANNING_CAPACITY_UTILIZATION_WEIGHT", 6.0)
    planning_empty_seat_penalty_weight: float = _float_env("PLANNING_EMPTY_SEAT_PENALTY_WEIGHT", -2.0)


settings = Settings()
