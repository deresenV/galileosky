@echo off
setlocal EnableDelayedExpansion

echo ==================================================
echo Starting Galileosky Monitoring Stack
echo ==================================================

cd monitoring

echo Building and starting containers...
docker compose up -d --build
if %errorlevel% neq 0 (
    echo "docker compose" command failed, trying "docker-compose"...
    docker-compose up -d --build
    if %errorlevel% neq 0 (
        echo Error: Docker Compose failed to start services.
        echo Please ensure Docker Desktop is running.
        pause
        exit /b 1
    )
)

echo.
echo ==================================================
echo Services are running!
echo ==================================================
echo.

echo [Local IP Addresses]
powershell -Command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike '*Loopback*' -and $_.InterfaceAlias -notlike '*vEthernet*' } | Select-Object -ExpandProperty IPAddress"

echo.
echo [Public IP Address]
powershell -Command "try { (Invoke-WebRequest -Uri 'https://api.ipify.org' -UseBasicParsing).Content } catch { echo 'Unavailable' }"

echo.
echo ==================================================
echo Access Information:
echo - Grafana Dashboard: http://localhost:3000
echo - Listener Port:     12347 (TCP)
echo ==================================================
echo.
echo Press any key to exit...
pause >nul
