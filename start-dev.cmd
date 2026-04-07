@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] No se encontro ".venv\Scripts\python.exe".
  echo Crea el entorno virtual e instala dependencias primero.
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo [ERROR] No se encontro "frontend\node_modules".
  echo Instala las dependencias del frontend primero con:
  echo   cd frontend ^&^& npm.cmd install
  exit /b 1
)

echo Iniciando backend en http://127.0.0.1:8000 ...
start "KLS Backend" cmd /k "cd /d ""%~dp0"" && .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

echo Iniciando frontend en http://127.0.0.1:5173 ...
start "KLS Frontend" cmd /k "cd /d ""%~dp0frontend"" && npm.cmd run dev -- --host 127.0.0.1 --port 5173"

echo.
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:5173
echo Se abrieron dos ventanas nuevas de cmd.

endlocal
