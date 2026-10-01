"""
FAO-56 Penman-Monteith daily ETo.

Assumptions for the internal weather station (Ecowitt/Ambient protocol):
  - wind_speed stored in mph (field windspeedmph) → converted to m/s here
  - solar_radiation stored in W/m² (instantaneous reading from pyranometer)
    averaged over ALL readings of the day (including night values of 0)
    → Rs [MJ/m²/day] = Avg(W/m²) × 0.0864
  - Wind sensor assumed at 2 m height (adjust _WIND_HEIGHT_M if different)
  - Elevation not stored; defaults to 0 m (sea level). Add a field to WeatherStation
    and pass it here to improve accuracy for Mendoza (~750 m).
"""

import math

_WIND_HEIGHT_M = 2.0   # assumed anemometer height
_MPH_TO_MS     = 0.44704
_WM2_TO_MJ_DAY = 0.0864   # W/m² average over 24 h → MJ/m²/day


def _es(T: float) -> float:
    """Saturation vapour pressure at temperature T (°C) — FAO eq. 11."""
    return 0.6108 * math.exp(17.27 * T / (T + 237.3))


def _u2(uz: float, z: float = _WIND_HEIGHT_M) -> float:
    """Wind speed corrected to 2 m height — FAO eq. 47."""
    if z == 2.0:
        return uz
    return uz * (4.87 / math.log(67.8 * z - 5.42))


def penman_monteith_eto(
    tmin: float,
    tmax: float,
    hr_mean: float,
    wind_mph_avg: float,
    solar_wm2_avg: float,
    latitude: float,
    day_of_year: int,
    elevation_m: float = 0.0,
) -> float | None:
    """
    FAO-56 Penman-Monteith ETo (mm/day).

    Parameters
    ----------
    tmin, tmax      : daily min/max temperature (°C)
    hr_mean         : mean relative humidity (%)
    wind_mph_avg    : mean wind speed in mph (stored as windspeedmph)
    solar_wm2_avg   : mean solar radiation in W/m², averaged over all
                      daily readings including night zeros
    latitude        : decimal degrees (negative = southern hemisphere)
    day_of_year     : 1–366
    elevation_m     : metres above sea level (default 0)

    Returns ETo (mm/day) rounded to 1 decimal, or None if inputs are
    insufficient.
    """
    if any(v is None for v in [tmin, tmax, hr_mean, wind_mph_avg, solar_wm2_avg]):
        return None
    if hr_mean <= 0 or hr_mean > 100 or wind_mph_avg < 0:
        return None

    # Unit conversions
    u2_ms = _u2(_MPH_TO_MS * wind_mph_avg)
    Rs    = solar_wm2_avg * _WM2_TO_MJ_DAY

    tmean   = (tmin + tmax) / 2.0
    lat_rad = math.radians(latitude)

    # Atmospheric pressure P (kPa) — FAO eq. 7
    P = 101.3 * ((293.0 - 0.0065 * elevation_m) / 293.0) ** 5.26

    # Psychrometric constant γ (kPa/°C) — FAO eq. 8
    gamma = 0.000665 * P

    # Vapour pressure terms
    es_mean = (_es(tmin) + _es(tmax)) / 2.0      # saturation — FAO eq. 12
    ea      = (hr_mean / 100.0) * es_mean         # actual     — FAO eq. 17
    vpd     = max(es_mean - ea, 0.0)              # deficit (always ≥ 0)

    # Slope of saturation VP curve Δ (kPa/°C) — FAO eq. 13
    delta = 4098.0 * _es(tmean) / (tmean + 237.3) ** 2

    # Extraterrestrial radiation Ra (MJ/m²/day) — FAO eqs. 21–27
    dr       = 1.0 + 0.033 * math.cos(2 * math.pi / 365 * day_of_year)
    sol_dec  = 0.409 * math.sin(2 * math.pi / 365 * day_of_year - 1.39)
    cos_lat  = math.cos(lat_rad)
    sin_lat  = math.sin(lat_rad)
    cos_dec  = math.cos(sol_dec)
    sin_dec  = math.sin(sol_dec)
    tan_dec  = math.tan(sol_dec)
    # sunset hour angle (clamp to avoid acos domain error near poles)
    omega_s  = math.acos(max(-1.0, min(1.0, -math.tan(lat_rad) * tan_dec)))
    Ra = (24.0 * 60.0 / math.pi) * 0.0820 * dr * (
        omega_s * sin_lat * sin_dec + cos_lat * cos_dec * math.sin(omega_s)
    )

    # Clear-sky solar radiation Rso — FAO eq. 37
    Rso = max((0.75 + 2e-5 * elevation_m) * Ra, 0.001)

    # Net shortwave radiation Rns — FAO eq. 38  (α = 0.23 reference grass)
    Rns = 0.77 * Rs

    # Net longwave radiation Rnl — FAO eq. 39
    sigma   = 4.903e-9                              # MJ/(K⁴·m²·day)
    Tk4_avg = ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2.0
    rs_rso  = min(Rs / Rso, 1.0)
    Rnl = sigma * Tk4_avg * (0.34 - 0.14 * math.sqrt(max(ea, 0))) * (1.35 * rs_rso - 0.35)

    # Net radiation Rn (G = 0 for daily)
    Rn = Rns - Rnl

    # ETo — FAO eq. 6
    numerator   = 0.408 * delta * Rn + gamma * (900.0 / (tmean + 273.0)) * u2_ms * vpd
    denominator = delta + gamma * (1.0 + 0.34 * u2_ms)

    if denominator <= 0:
        return None

    eto = numerator / denominator
    return max(round(eto, 1), 0.0)
