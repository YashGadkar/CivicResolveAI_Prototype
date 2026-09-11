import re
from functools import lru_cache

import httpx

from ..config import get_settings
from ..schemas import LocationVerificationResponse

settings = get_settings()

INVALID_LOCATION_RE = re.compile(r"^(?:test|testing|asdf+|qwerty|unknown|none|na|n/a|abc|xyz|12345?)$", re.IGNORECASE)


@lru_cache(maxsize=512)
def verify_location(location: str) -> LocationVerificationResponse:
    clean = re.sub(r"\s+", " ", location).strip(" ,.;")
    if len(clean) < 2 or INVALID_LOCATION_RE.fullmatch(clean) or not any(ch.isalpha() for ch in clean):
        return LocationVerificationResponse(
            input=location,
            valid=False,
            message="That location does not look like a real locality or address. Please enter a city, locality, ward, street, or landmark.",
        )

    params: dict[str, str | int] = {
        "q": clean,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 3,
    }
    if settings.geocoder_country_code_list:
        params["countrycodes"] = ",".join(settings.geocoder_country_code_list)

    try:
        with httpx.Client(timeout=settings.geocoder_timeout_seconds, follow_redirects=True) as client:
            response = client.get(
                f"{settings.geocoder_base_url.rstrip('/')}/search",
                params=params,
                headers={"User-Agent": settings.geocoder_user_agent, "Accept-Language": "en"},
            )
            response.raise_for_status()
            results = response.json()
    except (httpx.HTTPError, ValueError):
        return LocationVerificationResponse(
            input=location,
            valid=False,
            message="Location verification is temporarily unavailable. Please try again in a moment.",
        )

    if not isinstance(results, list) or not results:
        return LocationVerificationResponse(
            input=location,
            valid=False,
            message="We could not verify that location. Add the city/district or use a more specific locality, ward, street, or landmark.",
        )

    best = results[0]
    try:
        lat = float(best.get("lat"))
        lon = float(best.get("lon"))
    except (TypeError, ValueError):
        lat = lon = None
    canonical = str(best.get("display_name") or clean)[:255]
    return LocationVerificationResponse(
        input=location,
        valid=True,
        canonical_name=canonical,
        latitude=lat,
        longitude=lon,
        message="Location verified.",
    )
