@echo off
setlocal

cd /d "%~dp0"

echo Iniciando o sistema Igreja CRM...
docker compose up -d

if errorlevel 1 (
    echo.
    echo Nao foi possivel iniciar o sistema.
    echo Verifique se o Docker Desktop esta aberto.
    pause
    exit /b 1
)

echo.
echo Sistema iniciado com sucesso!
echo Acesse: http://localhost:8000
echo.
pause
