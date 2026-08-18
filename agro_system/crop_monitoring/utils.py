def project_days(current_gdd, target_gdd, projected_daily_gdd):
    """
    Anticipación REAL: días estimados para alcanzar un GDD objetivo usando el
    promedio diario PROYECTADO del pronóstico Open-Meteo, no un histórico fijo.

        days = (target_gdd - current_gdd) / projected_daily_gdd

    Devuelve None si ya se superó el objetivo o si el ritmo proyectado es <= 0.
    """
    remaining = target_gdd - current_gdd
    if remaining <= 0 or projected_daily_gdd <= 0:
        return None
    return round(remaining / projected_daily_gdd, 1)
