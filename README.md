# GeAgro — Sistema de alertas vitivinícolas

SaaS de alertas inteligentes para viñedos. Ingesta datos climáticos (estación propia + Open-Meteo), acumula GDD, deriva el estado fenológico (escala BBCH) y dispara alertas accionables por cultivo y campaña.

---

## Puesta en marcha (primera vez)

### 1. Variables de entorno

Crear el archivo `.env` dentro de la carpeta de settings (`agro_system/agro_system/`).
Copiar el contenido de `env_template` y completar los datos sin espacios alrededor del `=`.

Para generar una `SECRET_KEY`:

    python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

### 2. Dependencias

    pip install -r requirements.txt

### 3. Base de datos

    # Aplica todas las migraciones (incluye grupos, provincias y ciudades de Argentina)
    python manage.py migrate

### 4. Traducciones

    # Extrae strings marcados con _('...') y genera/actualiza el archivo .po
    python manage.py makemessages -l es

    # Compila el .po a .mo para que Django lo use (correr después de editar el .po)
    python manage.py compilemessages

---

## Comandos de management

### Orden de ejecución inicial recomendado

```
create_producer_group
seed_viticulture_operations
seed_indicators
seed_test_data        ← mínimo para tener datos funcionales
seed_demo_data        ← opcional, datos de demo completos
run_daily_cycle       ← ciclo diario (cron)
```

---

### `create_producer_group`

> Crea el grupo de permisos para usuarios de tipo Productor.

    python manage.py create_producer_group

Crea el grupo `Productor` y le asigna permisos a las apps de productor, insumos, operaciones, ventas y alertas. **Correrlo una sola vez** al iniciar el proyecto. Si el grupo ya existe, actualiza sus permisos.

---

### `seed_viticulture_operations`

> Carga todos los datos maestros del sistema vitivinícola.

    python manage.py seed_viticulture_operations

    # Ver qué crearía sin escribir en la base de datos
    python manage.py seed_viticulture_operations --dry-run

Crea o actualiza:
- **Estadios fenológicos BBCH** (escala Lorenz 1994, calibrada Mendoza) con rangos de GDD base 10 °C
- **Variedades y actividades**: Malbec, Cabernet Sauvignon, Merlot, Bonarda, Syrah, Chardonnay, Chenin, Semillón, Tannat, Tempranillo, Pinot Noir, Viognier — con GDD de cosecha por variedad
- **Etapas operativas**: Poda, Brotación, Desarrollo foliar, Floración y Cuaje, Envero, Maduración, Cosecha
- **Tipos de servicio y servicios**: fitosanitarios, emergencia climática, gestión hídrica, monitoreo, labores culturales, mantenimiento y cosecha

Idempotente: `update_or_create` en todo — safe para correr varias veces.

---

### `seed_indicators`

> Configura todos los indicadores del motor de alertas con sus variables, bandas, recomendaciones y acciones.

    python manage.py seed_indicators

Crea y configura:
- **Indicadores**: helada, granizo, estrés hídrico, golpe de calor, zonda, lobesia botrana, oídio, botrytis, mildiu primario, mildiu secundario, ventana de aplicación, ventana de cosecha
- **Estado por zona**: vincula cada indicador al perfil de alerta de Mendoza y Tandil (`on` / `vigilance` / `off`)
- **Variables e IndicatorBand BBCH**: umbrales por etapa fenológica para helada, oídio y mildiu
- **Recomendaciones**: texto que aparece en el detalle de la alerta (helada, zonda, mildiu primario)
- **Acciones**: plantillas de orden de trabajo que se generan automáticamente al disparar la alerta (helada, zonda, mildiu primario)

Idempotente: borra y recrea recomendaciones, acciones y bandas. Los indicadores se actualizan con `update_or_create`.

---

### `seed_test_data`

> Crea un conjunto mínimo de datos de prueba ligados al productor id=2 (Florencia Productor).

    python manage.py seed_test_data

Genera:
- Parámetros base: géneros, moneda ARS, unidades de medida, estados de cultivo y OT
- Estructura de campo: finca, lotes, áreas (Mendoza y Tandil)
- Dos cultivos activos (Malbec y Cabernet Sauvignon) con su campaña
- Biofix (brotación) y GDD acumulado inicial simulado (~BBCH 65 — floración)
- AlertProfile y AlertProfileIndicator para Mendoza y Tandil

Útil para tener un entorno funcional rápido. **Prerequisito** para `seed_demo_data` y `seed_climate_demo`.

---

### `seed_demo_data`

> Genera datos completos de demostración: dos campañas, tres cultivos, plan técnico, órdenes de trabajo con insumos y contratistas, y alertas para toda la temporada.

    python manage.py seed_demo_data

Requiere `seed_viticulture_operations` y `seed_test_data` previos. Crea:

**Campañas**
- `Campaña 2025/2026` — anterior, `active=False`, cosechada (sep-2025 → abr-2026)
- `Campaña 2026/2027` — actual, `active=True`, en poda/dormancia

**Cultivos** (3 por campaña, en la Finca San Carlos, Luján de Cuyo)
- Malbec — Lote Norte (10 ha)
- Cabernet Sauvignon — Lote Sur (7.5 ha)
- Bonarda — Lote Este (4.5 ha, lote nuevo)

**Insumos fitosanitarios**
Azufre mojable 80% WP, Mancozeb, Fosetil-Al, Ciproconazol, Boscalid + Piraclostrobin, Clorpirifós, Acetamiprid, Citowett, Fosfato monoamónico

**Plan técnico** `PT-MBL-MZA-10HA` — 14 etapas (poda → cosecha) con dosis de insumo por hectárea

**Órdenes de trabajo**
- Campaña anterior (27 OTs): todas en estado `Finalizada`, algunas `TPW` con contratista, varias con insumos aplicados
- Campaña actual (26 OTs): estado `En curso`, `Pendiente` y `Contingente` según la etapa

**DailySummary**: datos climáticos sintéticos para 15 eventos clave de cada campaña (heladas, zonda, golpe de calor, lluvia)

**Alertas campaña anterior (13)**: confirmadas (`is_forecast=False`): heladas oct-2025, zonda, oídio, lobesia, golpe de calor ene-2026, botrytis feb-2026

**Alertas campaña actual (13)**: pronóstico (`is_forecast=True`) distribuidas por toda la temporada sep-2026 → ene-2027 — persisten en la base de datos y no las elimina el ciclo diario mientras estén fuera de la ventana de 7 días

---

### `seed_climate_demo`

> Inyecta datos climáticos sintéticos con condiciones de helada para testear el motor de alertas sin depender de Open-Meteo real.

    python manage.py seed_climate_demo

Requiere `seed_test_data` previo. Genera:
- `ExternalStation` sintética ligada al lote de prueba (Malbec Lote Norte)
- 15 días de clima normal en `OpenMeteoHourly` (acumula ~105 GDD → BBCH 11-15)
- Hoy y mañana con helada a la madrugada (T = −3 °C, HR = 85%, viento 2 km/h)
- `DailySummary` consolidado y `GDDAccumulator` recalculado desde los datos horarios
- Evaluación automática de alertas: dispara `FrostEvaluator` (nivel `alert` por helada radiativa severa)

Útil para verificar que el motor detecta y emite alertas correctamente en un entorno aislado.

---

### `run_daily_cycle`

> Ciclo diario completo del motor agro: ingesta climática, recalcula GDD, evalúa indicadores, emite alertas y notificaciones.

    python manage.py run_daily_cycle

    # Procesar una fecha específica (útil para backfill o debug)
    python manage.py run_daily_cycle --date 2026-08-10

    # Modo fin de día: consolida con datos reales de la estación propia
    python manage.py run_daily_cycle --eod

    # Backfill: reprocesa desde una fecha hasta hoy
    python manage.py run_daily_cycle --from-date 2026-07-01

**Flujo interno:**
1. Consolida `DailySummary` desde Open-Meteo (y desde estación propia si `--eod`)
2. Recalcula `GDDAccumulator` para todos los cultivos con biofix
3. Evalúa indicadores activos del perfil de zona y del cultivo
4. Emite `Alert` con el nivel devuelto por el evaluador (warning / alert / critical)
5. Genera órdenes de trabajo contingentes para alertas de pronóstico
6. Crea `Notification` para los usuarios responsables
7. Aborta alertas de pronóstico que ya no se predicen o cuya fecha pasó sin confirmarse

La estación propia tiene prioridad sobre Open-Meteo cuando tiene datos para esa fecha.

Idempotente: se puede correr N veces por día sin efectos secundarios.

**Cron recomendado:**

    # 08:00 h — ciclo de mañana (GDD estimado con pronóstico Open-Meteo)
    0 8 * * *  /ruta/venv/bin/python /ruta/manage.py run_daily_cycle

    # 23:45 h — ciclo fin de día (GDD definitivo con datos reales de estación)
    45 23 * * *  /ruta/venv/bin/python /ruta/manage.py run_daily_cycle --eod

---

## Usuarios y permisos

El modelo de usuario extiende el User de Django para autenticación por email. Hay tres tipos:

| Tipo | Descripción | Grupo requerido |
|---|---|---|
| Administrador general | Acceso total al admin | `is_staff = True` |
| Organización | Puede crear y administrar productores de su org | `Organización` |
| Productor | Acceso a su propio campo, cultivos y alertas | `Productor` |

Los usuarios Productor se crean desde `UserProducer`, no desde el modelo base. El grupo se asigna automáticamente según el tipo.

---

## Settings

El proyecto usa tres archivos de configuración:

| Archivo | Uso |
|---|---|
| `settings/base.py` | Configuración común a todos los entornos |
| `settings/dev.py` | Extiende base — desarrollo local |
| `settings/prod.py` | Extiende base — producción |

Para cambiar de entorno, editar `manage.py`:

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agro_system.settings.dev')
    # o
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agro_system.settings.prod')
