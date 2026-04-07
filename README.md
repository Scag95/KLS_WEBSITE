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
http://127.0.0.1:8000/docs
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

En desarrollo, `http://127.0.0.1:8000` es solo la API. La interfaz web actual se sirve desde Vite en `http://127.0.0.1:5173`.

## Arrancar ambos desde VS Code

En VS Code puedes lanzar backend y frontend en terminales integradas separadas con la tarea:

```text
Terminal > Run Task > KLS Dev
```

Tambien puedes abrir la paleta de comandos y ejecutar `Tasks: Run Task`, luego elegir `KLS Dev`.
Antes de usarla, asegurate de haber creado `.venv` e instalado las dependencias de `frontend/`.

## Arrancar ambos con F5 en VS Code

Tambien puedes iniciar todo desde el depurador de VS Code con la configuracion:

```text
Run and Debug > KLS Full Stack
```

O pulsando `F5` despues de seleccionar `KLS Full Stack` en el panel de depuracion.
Esto abre backend y frontend en terminales integradas de VS Code y lanza el navegador en `http://127.0.0.1:5173`.

## Arrancar ambos con un solo comando en CMD

Si prefieres ventanas externas de `cmd`, desde la raiz del proyecto puedes ejecutar:

```cmd
start-dev.cmd
```

En PowerShell usa:

```powershell
.\start-dev.cmd
```

## Problemas comunes

- Si el frontend muestra errores de conexion, revisa que el backend siga corriendo en `127.0.0.1:8000`.
- Si `uvicorn` no se reconoce, usa `python -m uvicorn` o `.\.venv\Scripts\python.exe -m uvicorn`.
- Si `npm` falla en PowerShell por politicas de ejecucion, usa `npm.cmd` en lugar de `npm`.
