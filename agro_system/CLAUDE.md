# Contexto del proyecto — Motor de alertas vitivinícolas (MVP, foco Mendoza)

> Pegá esto en Claude Code, o guardalo como `CLAUDE.md` en la raíz del repo para que lo lea automáticamente. Idioma del proyecto: español argentino (vos, no tú).

---

## Qué estamos construyendo

Un SaaS de **alertas inteligentes para viñedos** basado en datos meteorológicos. El sistema ingiere clima (estación + API), acumula grados-día (GDD), deriva el estado fenológico de la planta (escala BBCH) y dispara alertas accionables.

El diseño contempla **dos regiones con climas opuestos** (Tandil húmedo / Mendoza árido), pero **el MVP arranca por Mendoza**. No hay que construir las dos: hay que construir el motor + un perfil (Mendoza) y dejar la puerta abierta para el segundo.

---

## La regla de oro de la arquitectura

**El motor es único. La región lo parametriza vía un perfil. Los umbrales NO van hardcodeados en las reglas: cada regla los lee del perfil activo.**

```
PerfilRegion (config)  ───parametriza───►  Motor común (idéntico para todas las regiones)
  • alertas_activas                          • ingesta de datos
  • umbrales                                 • acumuladores GDD
  • fuentes_prioritarias                     • estado BBCH
  • gdd_corte_superior                       • evaluador de reglas
```

Agregar una región = crear un registro de `PerfilRegion`, no tocar el código del motor.

---

## Modelo de datos

El modelo Django ya está armado en `models.py` (incluido en el repo). Resumen de las entidades y las decisiones que cargan peso:

- **PerfilRegion** — config por zona: `alertas_activas` (on/vigilancia/off por alerta), `umbrales` (JSON por alerta), `fuentes_prioritarias`, `gdd_corte_superior`.
- **Variedad** — lo único fenológico que cambia entre variedades es `gdd_cosecha_min/max`. La tabla de etapas es compartida.
- **Vinedo** — tiene perfil, variedad y lat/lon (para Open-Meteo).
- **Campania** — contenedor administrativo (poda, tareas, costos). Su `fecha_inicio` **NO** es el cero del GDD.
- **Biofix** — el cero biológico de **cada** contador. Una fila por contador por campaña.
- **LecturaDiaria** — una fila por viñedo por día. Tiene el método `gdd(base, corte)`.
- **AcumuladorGDD** — estado **recalculable**, no append-only. `recalcular()` suma desde el biofix.
- **EtapaFenologica** — tabla compartida GDD → BBCH → etapa (ya viene con seed).

### Tres convenciones que son fáciles de arruinar (leer con atención)

1. **Dos contadores de GDD en paralelo, con bases distintas y ceros distintos.**
   - Fenología de la vid: **base 10 °C**, cero en **brotación**.
   - Lobesia botrana: **base 7 °C**, cero en el **primer vuelo / primera captura de trampa**.
   - No comparten cero ni base. Son dos filas de `Biofix` distintas. Nunca mezclar los ejes.

2. **El GDD se recalcula desde el biofix, no se incrementa.** `AcumuladorGDD.recalcular()` siempre re-suma las `LecturaDiaria` desde la fecha del biofix. Por eso el **reanclaje** (cuando el productor confirma la brotación tarde) no necesita lógica especial: `biofix.confirmar(fecha_real)` cambia la fecha y vuelve a recalcular. Es idempotente. **No** implementar un contador que sume de a poco.

3. **El cero del GDD es un evento biológico, no la fecha de inicio de campaña.** Si el cero fuera administrativo, dos viñedos vecinos con podas en fechas distintas darían GDD distinto en la misma floración → se pierde comparabilidad y predicción. Mientras no haya brotación confirmada, se usa una fecha fija fallback (~1 de septiembre, hemisferio sur) y `origen="fallback"`.

---

## Anticipación (la lógica que dispara las alertas a tiempo)

La anticipación **no se mide en días fijos**, se proyecta sobre GDD:

```
dias_estimados = (gdd_objetivo - gdd_actual) / gdd_diario_proyectado
```

El `gdd_diario_proyectado` sale del **pronóstico** de Open-Meteo (próximos 7–14 días), no de un promedio histórico. Eso es "anticipación real". Ya está como `proyectar_dias()` en `models.py`.

---

## Foco MVP: perfil Mendoza

Clima árido frío (BWk). La presión fúngica es baja; **lo que domina es el estrés hídrico, el calor y el granizo**. El riego es estructural (sin riego no hay viñedo).

### Perfil de configuración a cargar

```python
PERFIL_MENDOZA = {
    "nombre": "mendoza",
    "clima": "BWk_arido",
    "gdd_corte_superior": 30.0,            # método Winkler con techo (validar contra datos)
    "alertas_activas": {
        "estres_hidrico": "on",            # LA dominante
        "helada": "on",
        "granizo": "on",
        "golpe_calor": "on",
        "zonda": "on",
        "lobesia": "on",                   # plaga cuarentenaria, importante en Cuyo
        "oidio": "on",                     # único hongo relevante (no necesita agua libre)
        "ventana_aplicacion": "on",
        "gdd_cosecha": "on",
        "bbch_dinamico": "on",
        "mildiu_primario": "vigilancia",   # solo años lluviosos
        "mildiu_secundario": "off",
        "botrytis": "vigilancia",          # solo lluvia pre-cosecha
        "exceso_hidrico": "off",
        "frente_frio_sudestada": "off",    # reemplazado por Zonda en Cuyo
    },
    "umbrales": {
        "estres_hidrico": {"aviso": -20, "alerta": -35, "critico": -50},
        "golpe_calor": {"t_floracion": 32, "t_envero": 38},
        # completar el resto a medida que se implementan
    },
    "fuentes_prioritarias": ["open_meteo_eto", "estacion_humedad_suelo", "estacion"],
    "variedades": {
        "malbec":             {"gdd_cosecha": [1450, 1700]},
        "cabernet_sauvignon": {"gdd_cosecha": [1550, 1800]},
        "bonarda":            {"gdd_cosecha": [1600, 1900]},
    },
}
```

### Orden de construcción sugerido (de cimiento a alerta)

1. **Cliente de ingesta Open-Meteo** → normaliza la respuesta y crea/actualiza `LecturaDiaria` por viñedo (lat/lon). Variables clave para Mendoza: T máx/mín, HR, viento, ráfagas, radiación, **ETo (Penman-Monteith FAO)**, **humedad de suelo**, CAPE.
2. **Motor GDD + BBCH** → correr `AcumuladorGDD.recalcular()` para el contador `vid`, y derivar el estado con `EtapaFenologica.estado_actual()`. Esto es la base de la que cuelga todo.
3. **Alerta Estrés hídrico** (la dominante) → balance rolling 7 días.
4. **Alerta Helada** → usa T mín, HR, viento y **Tw (bulbo húmedo, fórmula de Stull)**; umbrales por BBCH. En Mendoza la helada es advectiva además de radiativa.
5. **Alerta Ventana de aplicación** → semáforo verde/amarillo/rojo con **Delta T = T − Tw** (óptimo 2–8 °C), viento, ráfagas, sin lluvia 6 h. Reusa el cálculo de Tw de Helada.
6. **Management command diario** → ciclo completo: ingesta → recalcular acumuladores → evaluar reglas activas del perfil → emitir alertas.

### Detalle agronómico para las alertas prioritarias

- **Estrés hídrico (balance rolling 7 días):** `Balance = (Lluvia + Riego) − (ETo × Kc)` sobre los últimos 7 días (ventana deslizante). Kc por etapa: 0.30 brotación / 0.70 pleno desarrollo / 0.45 pre-cosecha. Niveles: aviso −20 mm, alerta −35 mm, crítico −50 mm.
  **GAP a resolver para Mendoza:** el riego es estructural, así que el balance **necesita** un input de riego (`riego_mm`). Sin modelar el riego, el balance hídrico en Mendoza no significa nada. Hay que agregar ese campo/entrada antes de que esta alerta sea útil acá. Marcarlo como pendiente.
- **Golpe de calor / Sunburn:** umbral 32 °C en floración (BBCH 60–69), 38 °C en envero (BBCH 81+). Variables: T máx, radiación, HR, viento. En Mendoza es fuerte por T>35 °C frecuente + radiación de altura.
- **Zonda:** viento föhn cálido y seco (deseca brotes). Reemplaza a la sudestada de Buenos Aires. Crítico en brotación–desarrollo foliar (primavera).
- **Helada:** umbrales por BBCH; calcular Tw con T + HR (Stull) y usarlo como disparo conservador (dispara antes que T seca → más seguro).

---

## Stack

- Backend: **Django + Python** (es lo que ya está en `models.py`).
- Base de datos: **PostgreSQL** (+ PostGIS si se necesita geo más adelante).
- API meteorológica: **Open-Meteo**. OJO: el plan gratis es para uso **no comercial**; para un SaaS que cobra hay que usar el tier comercial con API key. Tenerlo en cuenta en costos.
- Frontend: por definir (probablemente React), fuera del alcance del MVP inicial.

---

## Estilo de trabajo esperado

- Respuestas directas, con código concreto y números. Sin floritura.
- Flaggear errores e inconsistencias en vez de confirmar suposiciones.
- Si algo no cierra agronómicamente o técnicamente, decirlo.
- Antes de implementar una alerta nueva, confirmar que lee sus umbrales del perfil, no hardcodeados.