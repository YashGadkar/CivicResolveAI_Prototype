from fastapi import APIRouter, Depends

from .models import User
from .platform_routes import current_user
from .platform_schemas import CoordinateLocationRequest, ProviderCapabilitiesResponse
from .schemas import LocationVerificationResponse
from .services.location import reverse_location

router = APIRouter(prefix="/api/v1", tags=["Capabilities"])


@router.get("/capabilities", response_model=ProviderCapabilitiesResponse)
def capabilities(_user: User = Depends(current_user)) -> ProviderCapabilitiesResponse:
    return ProviderCapabilitiesResponse()


@router.post("/device-location/reverse", response_model=LocationVerificationResponse)
def device_location(
    payload: CoordinateLocationRequest,
    _user: User = Depends(current_user),
) -> LocationVerificationResponse:
    return reverse_location(payload.latitude, payload.longitude)
