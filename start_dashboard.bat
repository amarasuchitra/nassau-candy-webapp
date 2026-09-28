@echo off
REM Start the Nassau Candy web app locally (Windows): http://localhost:8000
REM Keep this window open while you use the app. Close it to stop.
setlocal
cd /d "%~dp0"
title Nassau Candy web app

if exist ".venv-installed" goto run

echo.
echo  First run: setting up the app. This takes a minute or two...
echo.
set "PY=python"
where python >nul 2>nul || set "PY=py"
%PY% -m venv .venv
if errorlevel 1 goto nopython
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo ok> .venv-installed

:run
REM use port 8000, or the next free one if something else is already using it
set "PORT=8000"
for /f "usebackq" %%p in (`".venv\Scripts\python.exe" -m backend.free_port 8000`) do set "PORT=%%p"
echo.
echo  Dashboard:  http://127.0.0.1:%PORT%
echo  API docs:   http://127.0.0.1:%PORT%/docs
echo  Keep this window open. Close it, or press Ctrl+C, to stop.
echo.
start "" cmd /c "timeout /t 4 /nobreak >nul & start http://127.0.0.1:%PORT%"
".venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port %PORT%
goto end

:nopython
echo.
echo  Python was not found. Install Python 3.11 or newer from https://www.python.org/downloads/
echo  and tick "Add python.exe to PATH" during setup. Then run this file again.
echo  Meanwhile you can open web\index.html directly - same dashboard, without the API.
goto end

:failed
echo.
echo  Installing the requirements failed. Check your internet connection and run this file again.
if exist ".venv" rmdir /s /q ".venv"

:end
echo.
pause
