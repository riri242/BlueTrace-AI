import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from app.schemas.drift import DriftRequest
from app.services.backward_drift_service import estimate_backward_drift
from app.services.coastline_validation import check_coastline
from app.services.marine_service import MarineService

logger = logging.getLogger(__name__)
ZONE = ZoneInfo("America/Los_Angeles")
LIMITATIONS = (
    "Experimental fixed-location current-only displacement, not a validated debris "
    "source estimate. Currents are sampled at the observation location, not along "
    "the path. Wind, waves, coastline collisions and uncertainty are not modeled. "
    "The result is anchored to the latest available hourly reading."
)


async def calculate_drift(request: DriftRequest, marine_service=None) -> dict:
    observed = datetime.combine(request.date, request.time)
    local = observed.replace(tzinfo=ZONE)
    if local.replace(fold=1).utcoffset() != local.replace(fold=0).utcoffset():
        return {
            "observation_date": request.date.isoformat(),
            "observation_time": request.time.isoformat(timespec="minutes"),
            "hours_requested": request.hours,
            "limitations": LIMITATIONS,
            "status": "unavailable",
            "message": "Ambiguous or nonexistent daylight-saving local time; choose another observation time."
        }
    now = datetime.now(ZONE).replace(tzinfo=None)
    base = {
        "observation_date": request.date.isoformat(),
        "observation_time": request.time.isoformat(timespec="minutes"),
        "hours_requested": request.hours,
        "limitations": LIMITATIONS,
    }

    def unavailable(message):
        return {**base, "status": "unavailable", "message": message}

    if observed > now:
        return unavailable("Observation date/time is in the future for California coast.")

    service = marine_service if marine_service is not None else MarineService()
    try:
        history = await service.get_marine_history(
            latitude=request.latitude,
            longitude=request.longitude,
            date=request.date.isoformat(),
            time=request.time.isoformat(timespec="minutes"),
            hours=request.hours,
        )
        result = estimate_backward_drift(history)
    except (RuntimeError, ValueError, TypeError, KeyError, OverflowError) as exc:
        logger.info("Drift estimation unavailable: %s", exc)
        return unavailable("Marine current history is unavailable or insufficient for this observation window.")

    anchor = datetime.fromisoformat(result["anchor_time"])
    offset_hours = (observed - anchor).total_seconds() / 3600
    if offset_hours < 0 or offset_hours > 1.5:
        return unavailable("No current reading sufficiently close to the observation time.")

    coastline_status = check_coastline(result["path"])
    return {
        **base,
        "status": "experimental",
        "coastline_status": coastline_status,
        "hours_traced": result["hours_traced"],
        "anchor_time": result["anchor_time"],
        "observation_offset_minutes": round(offset_hours * 60, 2),
        "path": result["path"],
        "message": ("Potential land crossing detected; do not interpret this path as a marine trajectory." if coastline_status == "potential_land_crossing" else "Experimental current-only backward trace; not a source attribution."),
    }
