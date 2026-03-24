# KLS Timber Floor Joist Backend

Backend API built with FastAPI for timber floor joist calculations.

## What is included

- FastAPI application with `/health` and `/calculate/floor-joist`.
- Typed request and response schemas with Pydantic.
- Action pattern schemas for permanent, imposed, snow, and wind actions aligned with EN 1991 parts.
- Project action catalogs and a combination generator for ULS/SLS action sets.
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

## Run locally

Install dependencies:

```bash
pip install -e .[dev]
```

Start the API:

```bash
uvicorn app.main:app --reload
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

## Static design preview

If you cannot install Node.js, open `frontend/preview.html` directly in your browser. It is a standalone HTML/CSS mockup of the calculator UI intended for design review without any frontend tooling.
