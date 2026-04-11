# Plan de Implementación: Calculadora Kerto-Ripa (MVP)

## Alcance

- **Incluido**: Sección A (métodos de diseño) + Sección B (ejemplo de verificación)
- **Excluido (preparado)**: Vibración (§A.10), Sección C (top slab support), Sección D (refuerzos)
- **National Annex**: Valores fijos finlandeses. Preparado para extensión a España.
- **Materiales**: Propiedades fijas ETA-07/0029 (Kerto-S y Kerto-Q). No editables por el usuario.

---

## 1. Definición de Inputs del Usuario (Frontend)

### Paso 1 — Tipo de Sección

El usuario selecciona **una** de las siguientes tipologías:

| ID | Nombre | Descripción | Losa superior | Losa inferior |
|----|--------|-------------|:---:|:---:|
| `ribbed_top` | Ribbed slab (losa arriba) | Solo losa superior | ✅ | ❌ |
| `ribbed_bottom` | Ribbed slab invertida | Solo losa inferior (upside down) | ❌ | ✅ |
| `box` | Box slab | Losa superior + inferior | ✅ | ✅ |
| `open_box` | Open box slab | Box con losa inferior discontinua | ✅ | ✅ (parcial) |

> [!NOTE]
> La tipología determina qué campos de geometría se activan en el paso siguiente y qué ecuaciones se usan en el backend (A.5 vs A.6, etc.).

---

### Paso 2 — Geometría de la Sección Transversal

#### Grupo: Elemento completo

| Campo | Descripción | Unidad | Rango | Requerido |
|-------|-------------|--------|-------|:---------:|
| `element_width` | Ancho total del elemento Kerto-Ripa | mm | > 0 | ✅ |
| `n_ribs` | Número de nervios (ribs) | — | ≥ 2 | ✅ |

> De estos dos datos el backend calcula automáticamente el spacing `b_f` entre nervios y si hay nervios de borde.

#### Grupo: Nervio (Rib / Web) — Material: Kerto-S (fijo)

| Campo | Descripción | Unidad | Rango | Requerido |
|-------|-------------|--------|-------|:---------:|
| `h_w` | Altura del nervio | mm | > 0 | ✅ |
| `b_w` | Ancho del nervio | mm | > 0 | ✅ |

#### Grupo: Losa superior (Top slab) — Material: Kerto-Q (fijo)

| Campo | Descripción | Unidad | Rango | Visible si |
|-------|-------------|--------|-------|:----------:|
| `h_f1` | Espesor de la losa superior | mm | > 0 | `ribbed_top`, `box`, `open_box` |

#### Grupo: Losa inferior (Bottom slab) — Material: Kerto-Q (fijo)

| Campo | Descripción | Unidad | Rango | Visible si |
|-------|-------------|--------|-------|:----------:|
| `h_f2` | Espesor de la losa inferior | mm | > 0 | `ribbed_bottom`, `box`, `open_box` |
| `b_actual` | Ancho real de la losa inferior (por nervio) | mm | > 0 | solo `open_box` |

> [!IMPORTANT]
> Según el PDF, el **espesor de las losas debe ser el valor lijado** (sanded). El frontend mostrará una nota informativa: *"Introduce el espesor después del lijado (nominal − 1 mm por cara lijada)"*.

#### Validaciones en frontend (instantáneas):
- `b_f` (spacing calculado) ≤ 1250 mm (máximo permitido §A.3)
- El campo `b_actual` solo aparece para `open_box`
- Vista previa SVG de la sección transversal actualizada en tiempo real

---

### Paso 3 — Geometría del Elemento (Longitudinal)

| Campo | Descripción | Unidad | Rango | Requerido |
|-------|-------------|--------|-------|:---------:|
| `L_ef` | Luz de cálculo (span) | mm | > 0 | ✅ |
| `L_support` | Longitud de contacto del apoyo | mm | > 0 | ✅ |
| `support_type` | Tipo de apoyo | enum | `end` / `intermediate` | ✅ |
| `span_type` | Configuración de vanos | enum | `single` | ✅ |

> [!NOTE]
> Para el MVP solo soportamos **single span** (simplemente apoyado). La opción `continuous` se dejará preparada en el schema pero deshabilitada en el frontend.

---

### Paso 4 — Cargas y Condiciones de Servicio

#### Grupo: Cargas (reutilizando el sistema de combinaciones existente)

El usuario define acciones en el catálogo de acciones (igual que en el floor joist calculator actual):

| Campo | Descripción | Unidad | Rango |
|-------|-------------|--------|-------|
| Acciones permanentes | Peso propio, acabados, etc. | kN/m² | ≥ 0 |
| Acciones variables | Sobrecarga de uso, nieve, etc. | kN/m² | ≥ 0 |
| Factores ψ | psi0, psi1, psi2 por acción variable | — | 0–1 |

> Se reutiliza `ProjectActionCatalog` + `generate_combinations()` sin cambios.

#### Grupo: Condiciones de diseño

| Campo | Descripción | Opciones | Default |
|-------|-------------|----------|---------|
| `service_class` | Clase de servicio EC5 | SC1, SC2, SC3 | SC1 |
| `load_duration_class` | Clase de duración de carga | Permanente, Largo, Medio, Corto, Instantáneo | Medio |

> El backend resuelve automáticamente `k_mod` y `k_def` a partir de estos dos campos:

| `load_duration_class` | `k_mod` (LVL, SC1) | `k_mod` (LVL, SC2) |
|---|---|---|
| Permanente | 0.60 | 0.60 |
| Largo plazo | 0.70 | 0.70 |
| Medio plazo | 0.80 | 0.80 |
| Corto plazo | 0.90 | 0.90 |
| Instantáneo | 1.10 | 1.10 |

| Service class | `k_def` (LVL) |
|---|---|
| SC1 | 0.60 |
| SC2 | 0.80 |
| SC3 | *(no recomendado para LVL)* |

#### Grupo: Coeficientes de seguridad (fijos, mostrados como info)

| Parámetro | Valor | Nota |
|-----------|-------|------|
| `γ_M,LVL` | 1.2 | Finland NA. Preparado para extensión |
| `γ_M,conn` | 1.2 | Finland NA. Para Sections C/D futuras |

---

### Paso 5 — Resultados

No hay inputs del usuario. Se muestra el informe de verificaciones.

---

## 2. Propiedades de Material Fijas (ETA-07/0029)

Estos valores se definen como constantes en el backend. El usuario **no los modifica**.

### Kerto-S (Nervios / Webs)

| Propiedad | Símbolo | Valor | Unidad |
|-----------|---------|-------|--------|
| Módulo de elasticidad medio | `E_mean,S` | 13800 | MPa |
| Módulo de elasticidad 5° percentil | `E_05,S` | 11600 | MPa |
| Resistencia a flexión característica | `f_m,k,S` | 44.0 | MPa |
| Resistencia a compresión paralela | `f_c,0,k,S` | 35.0 | MPa |
| Resistencia a tracción paralela | `f_t,0,k,S` | 35.0 | MPa |
| Resistencia a cortante edgewise | `f_v,0,edge,k,S` | 4.1 | MPa |
| Resistencia a cortante flatwise | `f_v,0,flat,k,S` | 2.3 | MPa |
| Resistencia a compresión perpendicular | `f_c,90,k,S` | 6.0 | MPa |
| Resistencia a tracción perpendicular | `f_t,90,k,S` | 0.5 | MPa |
| Módulo de cortante | `G_mean,S` | 600 | MPa |
| Módulo de elasticidad perpendicular | `E_90,mean,S` | 430 | MPa |
| Densidad característica | `ρ_k,S` | 480 | kg/m³ |

### Kerto-Q (Losas / Flanges)

| Propiedad | Símbolo | Valor | Unidad |
|-----------|---------|-------|--------|
| Módulo de elasticidad medio | `E_mean,Q` | 10500 | MPa |
| Módulo de elasticidad 5° percentil | `E_05,Q` | 8800 | MPa |
| Resistencia a compresión paralela | `f_c,0,k,Q` | 26.0 | MPa |
| Resistencia a tracción paralela | `f_t,0,k,Q` | 26.0 | MPa |
| Resistencia a cortante flatwise (rolling shear) | `f_v,0,flat,k,Q` | 1.3 | MPa |
| Resistencia a flexión flatwise | `f_m,0,flat,k,Q` | 32.0 | MPa |
| Resistencia a compresión perpendicular flatwise | `f_c,90,flat,k,Q` | 2.8 | MPa |
| Módulo de elasticidad perpendicular | `E_90,mean,Q` | 2000 | MPa |
| Módulo de cortante | `G_mean,Q` | 600 | MPa |
| Densidad característica | `ρ_k,Q` | 480 | kg/m³ |

> [!WARNING]
> Estos valores son los que se usan en el ejemplo del PDF (Sección B). La tabla completa Table 1-2 del ETA-07/0029 puede contener valores adicionales. Los valores `f_c,0,k`, `f_t,0,k` de Kerto-Q (26 MPa) y `f_m,k` de Kerto-S (44 MPa) están confirmados por el ejemplo numérico del PDF.

---

## 3. Pipeline de Cálculo (Backend)

El backend recibe los inputs y ejecuta la siguiente cadena:

```
INPUTS
  ├── section_type, geometría, cargas, service_class, load_duration_class
  │
  ▼
PASO 1: Geometría Derivada
  ├── b_f (spacing entre nervios) → element_width, n_ribs, b_w
  ├── b_ef,SLS (ancho eficaz SLS) → Eq. A.2
  ├── b_ef,ULS (ancho eficaz ULS) → Eq. A.3
  ├── Verificar criterio pandeo placa → Eq. A.4
  │
  ▼
PASO 2: Propiedades de Sección Efectiva
  ├── A_i (áreas) → b_i × h_i para cada miembro
  ├── I_i (inercias) → b_i × h_i³ / 12
  ├── a_i (distancias al eje neutro) → Eq. A.7–A.10
  ├── EI_ef,ULS → Eq. A.5 o A.6
  ├── EI_ef,SLS → Eq. A.5 o A.6 (con b_ef,SLS)
  │
  ▼
PASO 3: Esfuerzos de Diseño (por nervio)
  ├── Carga lineal por nervio: q_line = q_total × b_spacing
  ├── M_d = q_line × L² / 8  (simplemente apoyado)
  ├── V_d = q_line × L / 2
  ├── (Para combinaciones: se itera sobre cada combinación ULS/SLS)
  │
  ▼
PASO 4: Resistencias Características (ULS)
  ├── R_M,c,k   (compresión en ala)         → Eq. A.11
  ├── R_M,t,k   (tracción en ala)           → Eq. A.12 + k_l (A.13)
  ├── R_M,m,k   (borde del alma)            → Eq. A.14 + k_h (A.15)
  ├── R_M,centric,k (centro del alma)       → Eq. A.19
  ├── R_M,k = min(R_M,c,k, R_M,t,k, R_M,m,k)
  │
  ├── R_V,top,k  (unión losa sup–alma)      → Eq. A.22 + A.25
  ├── R_V,web,k  (cortante en alma)         → Eq. A.23
  ├── R_V,bot,k  (unión losa inf–alma)      → Eq. A.24 + A.25
  ├── R_V,k = min(R_V,top,k, R_V,web,k, R_V,bot,k)
  │
  ├── R_c90,k    (compresión en apoyo)       → Eq. A.32 o A.33/A.34
  │
  ▼
PASO 5: Resistencias de Diseño
  ├── R_d = k_mod × R_k / γ_M
  │
  ▼
PASO 6: Verificaciones ULS
  ├── Check bending:     M_d ≤ R_M,d     → utilization = M_d / R_M,d
  ├── Check shear:       V_d ≤ R_V,d     → utilization = V_d / R_V,d
  ├── Check support:     V_d ≤ R_c90,d   → utilization = V_d / R_c90,d
  ├── (Check combined si hay axial → Eq. A.28–A.31, futuro)
  │
  ▼
PASO 7: Verificaciones SLS
  ├── Deflexión instantánea momento:  u_inst,M = 5qL⁴/(384×EI_ef,SLS)
  ├── Deflexión instantánea cortante: u_inst,V = qL²/(8×G×A_web)
  ├── u_inst = u_inst,M + u_inst,V
  ├── Check: u_inst ≤ L/300
  │
  ├── Deflexión final:
  │   u_fin = (1+k_def)×u_inst,g + (1+ψ₂×k_def)×u_inst,q
  ├── Check: u_fin ≤ L/200
  │
  ▼
PASO 8 (futuro): Vibración
  ├── f_1 (frecuencia natural)
  ├── u_1kN (deflexión bajo 1 kN)
  ├── (Placeholder: no implementado en MVP)
```

---

## 4. Estructura de Ficheros Backend

### Nuevos ficheros

#### [NEW] `app/domain/kertoripa/`

```
app/domain/kertoripa/
├── __init__.py
├── materials.py         ← Constantes ETA-07/0029 + lookup k_mod, k_def
├── geometry.py          ← b_ef, áreas, inercias, eje neutro, EI_ef
├── bending.py           ← R_M,k (4 modos de fallo)
├── shear.py             ← R_V,k (3 modos de fallo)
├── support.py           ← R_c,90,k (ribbed thin / thick slab)
├── serviceability.py    ← Deflexiones instantáneas y finales
├── vibration.py         ← PLACEHOLDER (solo interfaz, sin lógica)
└── calculator.py        ← Orquestador: recibe request → devuelve response
```

#### [NEW] `app/schemas/kertoripa.py`

```python
# Enums
class KertoRipaSectionType(StrEnum):
    RIBBED_TOP = "ribbed_top"
    RIBBED_BOTTOM = "ribbed_bottom"
    BOX = "box"
    OPEN_BOX = "open_box"

class RibPosition(StrEnum):
    EDGE = "edge"
    MIDDLE = "middle"

class ServiceClass(StrEnum):       # reutilizar del floor_joist si ya existe
    SC1 = "service_class_1"
    SC2 = "service_class_2"
    SC3 = "service_class_3"

class LoadDurationClass(StrEnum):
    PERMANENT = "permanent"
    LONG_TERM = "long_term"
    MEDIUM_TERM = "medium_term"
    SHORT_TERM = "short_term"
    INSTANTANEOUS = "instantaneous"

# Request
class KertoRipaCrossSectionInput(BaseModel):
    section_type: KertoRipaSectionType
    element_width_mm: float         # Ancho total del elemento
    n_ribs: int                     # Número de nervios, ≥ 2
    h_w_mm: float                   # Altura del nervio
    b_w_mm: float                   # Ancho del nervio
    h_f1_mm: float | None           # Espesor losa superior (None si no aplica)
    h_f2_mm: float | None           # Espesor losa inferior (None si no aplica)
    b_actual_mm: float | None       # Ancho real losa inferior (solo open_box)

class KertoRipaSpanInput(BaseModel):
    L_ef_mm: float                  # Luz de cálculo
    L_support_mm: float             # Longitud de apoyo
    support_position: str           # "end" | "intermediate"

class KertoRipaDesignBasis(BaseModel):
    service_class: ServiceClass
    load_duration_class: LoadDurationClass

class KertoRipaCalculationRequest(BaseModel):
    project_name: str | None
    cross_section: KertoRipaCrossSectionInput
    span: KertoRipaSpanInput
    design_basis: KertoRipaDesignBasis
    action_catalog: ProjectActionCatalog      # Reutilizado

# Response — misma filosofía que FloorJoistCombinationCalculationResponse
class KertoRipaGeometryResults(BaseModel):
    b_f_mm: float                   # Spacing calculado
    b_ef_SLS_mm: float              # Ancho eficaz SLS
    b_ef_ULS_mm: float              # Ancho eficaz ULS
    EI_ef_SLS_Nmm2: float           # Rigidez efectiva SLS
    EI_ef_ULS_Nmm2: float           # Rigidez efectiva ULS
    neutral_axis_a2_mm: float       # Posición eje neutro

class KertoRipaCheckResult(BaseModel):
    check: str                      # "bending", "shear", "support", etc.
    demand: float
    capacity: float
    utilization: float
    unit: str                       # "kNm", "kN", "mm", etc.
    passed: bool
    failure_mode: str | None        # "flange_compression", "web_edge", etc.

class KertoRipaCalculationResponse(BaseModel):
    summary: dict                   # passed, governing_check
    geometry: KertoRipaGeometryResults
    uls_checks: list[KertoRipaCheckResult]
    sls_checks: list[KertoRipaCheckResult]
    intermediate_values: dict       # a_i, I_i, A_i, R_M modes, R_V modes...
    warnings: list[WarningMessage]
```

#### [MODIFY] `app/api/routes.py`

```python
# Añadir endpoint:
@router.post("/calculate/kerto-ripa", ...)
def calculate_kerto_ripa_endpoint(payload: KertoRipaCalculationRequest):
    ...
```

---

## 5. Frontend — Flujo UX

### Estructura del wizard

```
┌─────────────────────────────────────────────────────────────┐
│                    KLS Timber Studio                        │
│                 Kerto-Ripa® Calculator                      │
├─────────────────────────────────────────────────────────────┤
│  [1. Sección]  [2. Geometría]  [3. Cargas]  [4. Resultados] │
├──────────────────────┬──────────────────────────────────────┤
│                      │                                      │
│   Formulario del     │   Vista previa SVG de la sección     │
│   paso activo        │   transversal (actualización live)   │
│                      │                                      │
│                      │   ┌─────────────────────────────┐    │
│                      │   │    ┌──────────────────┐      │    │
│                      │   │    │  h_f1 (Kerto-Q)  │      │    │
│                      │   │    └──┬────────────┬──┘      │    │
│                      │   │       │ h_w        │         │    │
│                      │   │       │ (Kerto-S)  │         │    │
│                      │   │       │ b_w        │         │    │
│                      │   │    ┌──┴────────────┴──┐      │    │
│                      │   │    │  h_f2 (Kerto-Q)  │      │    │
│                      │   │    └──────────────────┘      │    │
│                      │   └─────────────────────────────┘    │
│                      │                                      │
├──────────────────────┴──────────────────────────────────────┤
│              [← Anterior]    [Calcular →]                   │
└─────────────────────────────────────────────────────────────┘
```

### Tab 1 — Tipo de Sección
- 4 tarjetas visuales seleccionables (con icono SVG de cada tipología)
- Al seleccionar una, se marca visualmente y se pasa al próximo step

### Tab 2 — Geometría
- Split layout: formularios a la izquierda, preview SVG a la derecha
- La preview SVG muestra la sección transversal completa del elemento con:
  - Nervios coloreados (Kerto-S)
  - Losas coloreadas diferente (Kerto-Q)
  - Cotas con los valores actuales
  - Etiquetas de material
- Los campos aparecen/desaparecen según el `section_type` seleccionado
- Incluye campos del span (L_ef, L_support)

### Tab 3 — Cargas
- Reutiliza el componente de catálogo de acciones existente
- Añade selector de `service_class` y `load_duration_class`
- Muestra info-box con los valores derivados: k_mod, k_def, γ_M

### Tab 4 — Resultados
- Tarjetas de verificación con barra de utilización (patrón existente)
- Sección expandible "Valores intermedios" con:
  - b_ef (SLS/ULS), EI_ef (SLS/ULS), a_i, etc.
  - Cada modo de fallo de R_M,k y R_V,k con su valor
  - El modo gobernante resaltado
- Resumen de deflexiones SLS

---

## 6. Orden de Implementación

### Fase 1: Backend — Materiales y Geometría
1. `app/domain/kertoripa/materials.py` — Constantes + lookups
2. `app/schemas/kertoripa.py` — Modelos Pydantic
3. `app/domain/kertoripa/geometry.py` — b_ef, áreas, inercias, eje neutro, EI_ef

### Fase 2: Backend — Resistencias ULS
4. `app/domain/kertoripa/bending.py` — R_M,k (4 modos)
5. `app/domain/kertoripa/shear.py` — R_V,k (3 modos)
6. `app/domain/kertoripa/support.py` — R_c,90,k

### Fase 3: Backend — SLS + Orquestador
7. `app/domain/kertoripa/serviceability.py` — Deflexiones
8. `app/domain/kertoripa/vibration.py` — Placeholder
9. `app/domain/kertoripa/calculator.py` — Orquestador
10. `app/api/routes.py` — Endpoint

### Fase 4: Verificación Backend
11. Test con valores del ejemplo B del PDF:
    - h_w=225, b_w=45, h_f=25, spacing=585, L=5500, L_support=100
    - R_M,k = 103.2 kNm, R_V,k = 29.1 kN, R_c90,k = 37.2 kN
    - u_inst = 5.38 mm, u_fin = 6.95 mm

### Fase 5: Frontend
12. Nuevo componente/página Kerto-Ripa con wizard tabs
13. Preview SVG de sección transversal
14. Integración con API
15. Presentación de resultados

---

## 7. Verificación

### Test automatizado
- Script Python que reproduce el ejemplo B del PDF con valores conocidos
- Compara resultados numéricos con tolerancia de ±0.5%

### Verificación manual
- Levantar backend + frontend
- Introducir los datos del ejemplo B
- Verificar que los resultados coinciden con la Sección B del PDF
