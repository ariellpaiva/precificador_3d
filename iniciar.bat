@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    echo Preparando ambiente pela primeira vez...
    python -m venv .venv || (echo Python nao encontrado. Instale em python.org marcando "Add to PATH". & pause & exit /b)
)
.venv\Scripts\python -m pip install -q --disable-pip-version-check -r requirements.txt || (echo Falha ao instalar dependencias. & pause & exit /b)
.venv\Scripts\python server.py %*
pause
