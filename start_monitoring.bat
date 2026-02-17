@echo off
setlocal EnableDelayedExpansion

echo ==================================================
echo Starting Galileosky Monitoring Stack
echo ==================================================

echo.
echo Checking Docker connectivity...
docker pull hello-world >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Docker Hub seems unreachable. Trying to use mirror (mirror.gcr.io)...
    
    echo Pulling images from mirror...
    docker pull mirror.gcr.io/grafana/loki:2.9.2
    docker tag mirror.gcr.io/grafana/loki:2.9.2 grafana/loki:2.9.2
    
    docker pull mirror.gcr.io/grafana/promtail:2.9.2
    docker tag mirror.gcr.io/grafana/promtail:2.9.2 grafana/promtail:2.9.2
    
    docker pull mirror.gcr.io/grafana/grafana:10.4.1
    docker tag mirror.gcr.io/grafana/grafana:10.4.1 grafana/grafana:10.4.1
    
    echo Images pulled from mirror.
) else (
    echo Docker Hub is reachable.
)

cd monitoring

echo.
echo Building and starting containers...
docker compose up -d --build
if %errorlevel% neq 0 (
    echo "docker compose" command failed, trying "docker-compose"...
    docker-compose up -d --build
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Docker Compose failed to start services.
        echo Please ensure Docker Desktop is running and you have internet access.
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
