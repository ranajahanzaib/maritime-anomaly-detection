import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CanonicalAISPoint(BaseModel):
    mmsi: int
    imo: Optional[int] = None
    vessel_name: Optional[str] = None
    vessel_type: str = "Other"  # Cargo, Tanker, Fishing, Passenger, Tug, Other
    flag: Optional[str] = None
    timestamp: datetime.datetime
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    sog: float = Field(0.0, ge=0.0)  # Speed over ground in knots
    cog: float = Field(0.0, ge=0.0, le=360.0)  # Course over ground in degrees
    heading: Optional[float] = Field(None, ge=0.0, le=360.0)
    navigational_status: Optional[str] = "Under way using engine"
    length: Optional[float] = None
    width: Optional[float] = None
    draught: Optional[float] = None
    source_dataset: str = "GENERIC"
    original_record_id: Optional[str] = None
    is_interpolated: bool = False
    is_valid: bool = True
    rejection_reason: Optional[str] = None


def normalize_vessel_type(type_code_or_str: Optional[str | int]) -> str:
    if type_code_or_str is None:
        return "Other"
    
    val_str = str(type_code_or_str).strip().lower()
    
    # Try numeric AIS type code mapping
    try:
        code = int(val_str)
        if 70 <= code <= 79:
            return "Cargo"
        elif 80 <= code <= 89:
            return "Tanker"
        elif code == 30 or code == 31 or code == 32:
            return "Fishing"
        elif 60 <= code <= 69:
            return "Passenger"
        elif code == 52 or code == 31 or code == 32 or "tug" in val_str:
            return "Tug"
        elif 50 <= code <= 59:
            return "Special Craft"
        elif 20 <= code <= 29:
            return "Wing in Ground"
        else:
            return "Other"
    except ValueError:
        pass
    
    if "cargo" in val_str or "container" in val_str or "bulk" in val_str:
        return "Cargo"
    elif "tanker" in val_str or "crude" in val_str or "chemical" in val_str:
        return "Tanker"
    elif "fish" in val_str or "trawler" in val_str:
        return "Fishing"
    elif "passenger" in val_str or "ferry" in val_str or "cruise" in val_str:
        return "Passenger"
    elif "tug" in val_str or "tow" in val_str:
        return "Tug"
    elif "pleasure" in val_str or "yacht" in val_str or "sailing" in val_str:
        return "Pleasure Craft"
    elif "pilot" in val_str or "military" in val_str or "law" in val_str:
        return "Special Craft"
    return "Other"
