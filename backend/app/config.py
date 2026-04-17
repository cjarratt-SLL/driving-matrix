import os
from dotenv import load_dotenv

load_dotenv()


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


class Settings:
    app_name: str = os.getenv("APP_NAME", "Driving Matrix API")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    planning_total_minutes_weight: float = _float_env("PLANNING_TOTAL_MINUTES_WEIGHT", -0.05)
    planning_total_miles_weight: float = _float_env("PLANNING_TOTAL_MILES_WEIGHT", -1.0)
    planning_on_time_reliability_weight: float = _float_env("PLANNING_ON_TIME_RELIABILITY_WEIGHT", 50.0)
    planning_riders_served_weight: float = _float_env("PLANNING_RIDERS_SERVED_WEIGHT", 10.0)
    planning_load_balance_weight: float = _float_env("PLANNING_LOAD_BALANCE_WEIGHT", 5.0)


settings = Settings()
