# KLS Timber Floor Joist

Aplicacion con backend en FastAPI y frontend en React/Vite para calculo de vigas de madera.

## Levantar el proyecto localmente

### 1. Crear y preparar el entorno Python

Desde la raiz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

### 2. Instalar dependencias del frontend

Desde `frontend/`:

```powershell
cd frontend
npm.cmd install
```

Nota para Windows PowerShell: se usa `npm.cmd` para evitar problemas con la politica de ejecucion de scripts.

### 3. Arrancar el backend

En una terminal situada en la raiz del proyecto:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/health
```

### 4. Arrancar el frontend

En otra terminal, desde `frontend/`:

```powershell
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Frontend:

```text
http://127.0.0.1:5173
```

## Flujo recomendado

1. Arranca primero el backend.
2. Arranca despues el frontend.
3. Abre `http://127.0.0.1:5173` en el navegador.

## Problemas comunes

- Si el frontend muestra errores de conexion, revisa que el backend siga corriendo en `127.0.0.1:8000`.
- Si `uvicorn` no se reconoce, usa `python -m uvicorn` o `.\.venv\Scripts\python.exe -m uvicorn`.
- Si `npm` falla en PowerShell por politicas de ejecucion, usa `npm.cmd` en lugar de `npm`.
