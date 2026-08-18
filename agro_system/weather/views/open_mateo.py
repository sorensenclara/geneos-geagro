import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

from django.http import JsonResponse

from weather.models.station_external import ExternalStation
from weather.models.open_meteo_hourly import OpenMeteoHourly


def _angular_diff_series(series: pd.Series) -> pd.Series:
    """Angular difference between consecutive wind direction values (0–180°)."""
    raw = series.diff().abs() % 360
    return raw.apply(lambda x: min(x, 360.0 - x) if pd.notna(x) else None)

# source_field de la API → (campo en OpenMeteoHourly, decimales)
SOURCE_TO_MODEL = {
    "temperature_2m":             ("temperature",    2),
    "relative_humidity_2m":       ("humidity",       2),
    "wind_speed_10m":             ("wind_speed",     2),
    "wind_direction_10m":         ("wind_direction", 1),
    "wind_gusts_10m":             ("wind_gusts",     2),
    "precipitation":              ("precipitation",  2),
    "cape":                       ("cape",           1),
    "et0_fao_evapotranspiration": ("eto_mm",         2),
}


def _fetch_station(openmeteo, station):
    """Fetch y guarda datos horarios para una estación externa. Retorna (created, updated)."""
    mappings = list(station.variable_mappings.select_related("variable").all())
    if not mappings:
        return 0, 0

    variables = [m.source_field for m in mappings]
    params = {
        "latitude":  station.latitude,
        "longitude": station.longitude,
        "hourly":    variables,
        "timezone":  "auto",
    }
    responses = openmeteo.weather_api(station.url, params=params)
    response  = responses[0]
    hourly    = response.Hourly()

    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        ).tz_convert(response.Timezone().decode())
    }
    for i, source_field in enumerate(variables):
        hourly_data[source_field] = hourly.Variables(i).ValuesAsNumpy()

    hourly_dataframe = pd.DataFrame(data=hourly_data)

    # Derived variables — computed from consecutive rows
    if "temperature_2m" in variables:
        hourly_dataframe["delta_t_1h"] = hourly_dataframe["temperature_2m"].diff().round(2)
    if "wind_direction_10m" in variables:
        hourly_dataframe["wind_dir_change_1h"] = _angular_diff_series(
            hourly_dataframe["wind_direction_10m"]
        ).round(1)

    with pd.option_context("display.max_rows", None, "display.max_columns", None, "display.width", 200):
        print(f"\n--- {station.name} ---")
        print(hourly_dataframe.to_string(index=False))

    DERIVED_FIELDS = {"delta_t_1h", "wind_dir_change_1h"}

    created = updated = 0
    for _, row in hourly_dataframe.iterrows():
        fixed = {}
        extra = {}
        for source_field in variables:
            value = float(row[source_field])
            if source_field in SOURCE_TO_MODEL:
                model_field, decimals = SOURCE_TO_MODEL[source_field]
                fixed[model_field] = round(value, decimals)
            else:
                extra[source_field] = round(value, 2)

        for field in DERIVED_FIELDS:
            if field in hourly_dataframe.columns:
                raw = row.get(field)
                fixed[field] = None if pd.isna(raw) else float(raw)

        _, is_new = OpenMeteoHourly.objects.update_or_create(
            station=station,
            datetime=row["date"].to_pydatetime(),
            defaults={**fixed, "extra_data": extra},
        )
        if is_new:
            created += 1
        else:
            updated += 1

    return created, updated


def weather_open_meteo(request):
    stations = ExternalStation.objects.filter(variable_mappings__isnull=False).distinct()
    if not stations.exists():
        return JsonResponse(
            {"error": "No hay estaciones externas con variables configuradas. "
                      "Configurá los mapeos en Admin → Estación externa."},
            status=400,
        )

    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    results = {}
    for station in stations:
        created, updated = _fetch_station(openmeteo, station)
        results[station.name] = {"created": created, "updated": updated}

    return JsonResponse({"status": "ok", "stations": results})
