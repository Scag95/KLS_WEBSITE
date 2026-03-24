# KLS Timber Floor Joist Backend

Backend API built with FastAPI for timber floor joist calculations.

## What is included

- FastAPI application with `/health` and `/calculate/floor-joist`.
- Combined floor-joist calculation endpoint at `/calculate/floor-joist/combinations`.
- Typed request and response schemas with Pydantic.
- Action pattern schemas for permanent, imposed, snow, and wind actions aligned with EN 1991 parts.
- Project action catalogs and a combination generator for ULS/SLS action sets.
- Finite-element input/output schemas for future beam discretization and diagrams.
- Early FEM core for 1D beam mesh generation, local stiffness, and global assembly.
- Reusable calculation engine separated from the HTTP layer.
- Pytest coverage for the domain engine and API contract.
- React frontend scaffold under `frontend/` for interactive input and result display.

## Current design assumptions

This first version models a simply supported timber joist under uniformly distributed load. It reports:

- line load
- maximum bending moment
- maximum shear
- rectangular section properties
- bending stress
- shear stress
- instantaneous deflection
- pass/fail checks for bending, shear, and deflection
- warnings for some common review conditions

The `design_standard` field is included for traceability, but no specific timber design code has been encoded yet.

The combined floor-joist endpoint now separates:

- `ULS` combinations for bending and shear checks
- `SLS` combinations for deflection checks

When the `spain_timber_buildings` profile is selected, the backend applies Spanish timber annex defaults for serviceability interpretation:

- service class 1 as the default for intermediate floors between habitable spaces
- active deflection criteria based on the selected finish sensitivity
- floor comfort deflection limit `L/350`
- final deflection limit `L/300`

This version does not yet derive timber design resistances from characteristic strengths, `kmod`, `kdef`, and `gamma_M`; ULS resistance still uses the allowable stresses provided in the input.

## Run locally

Desde la raíz del repositorio, crea un entorno virtual (recomendado) e instala dependencias:

```bash
python -m venv .venv
```

En Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`  
En macOS/Linux: `source .venv/bin/activate`

```bash
pip install -e .[dev]
```

Arranca la API (usa el módulo de Python para que funcione aunque `uvicorn` no esté en el PATH):

```bash
python -m uvicorn app.main:app --reload
```

Run tests:

```bash
pytest
```

## Frontend

The React frontend lives in `frontend/` and is configured to call the backend at `http://127.0.0.1:8000`.

Install frontend dependencies:

```bash
cd frontend
npm install
```

Start the frontend:

```bash
npm run dev
```

En **otra terminal**, desde la raíz del repositorio (con el mismo entorno virtual activado si usas uno), arranca la API:

```bash
python -m uvicorn app.main:app --reload
```

Desde `frontend/` también puedes usar `npm run dev:api` (equivale a subir al directorio padre y ejecutar el comando anterior).

Si PowerShell dice que `uvicorn` no se reconoce, no uses el ejecutable suelto: usa siempre **`python -m uvicorn`** después de `pip install -e .[dev]`.

Si en la consola de Vite aparece `ECONNREFUSED 127.0.0.1:8000` o en la app «Error HTTP 500» con cuerpo vacío, el backend no está en marcha. En desarrollo, Vite reenvía `/calculate` y `/analyze` al puerto 8000.

## Static design preview

If you cannot install Node.js, open `frontend/preview.html` directly in your browser. It is a standalone HTML/CSS mockup of the calculator UI intended for design review without any frontend tooling.
