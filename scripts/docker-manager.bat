@echo off
REM GTM Voyager Platform - Docker Management Script for Windows

setlocal enabledelayedexpansion

REM Colors for output (Windows compatible)
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

echo %BLUE%GTM Voyager Platform - Docker Management%NC%
echo.

if "%1"=="" goto :show_help
if "%1"=="check" goto :check_prerequisites
if "%1"=="build" goto :build_images
if "%1"=="start" goto :start_platform
if "%1"=="stop" goto :stop_platform
if "%1"=="status" goto :show_status
if "%1"=="logs" goto :view_logs
goto :show_help

:check_prerequisites
echo %BLUE%Checking prerequisites...%NC%

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo %RED%ERROR: Docker is not installed or not in PATH%NC%
    echo Please install Docker Desktop for Windows
    exit /b 1
)
echo %GREEN%✓ Docker found%NC%

REM Check Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo %RED%ERROR: Docker Compose is not installed%NC%
    exit /b 1
)
echo %GREEN%✓ Docker Compose found%NC%

REM Check if .env file exists
if not exist "%PROJECT_ROOT%\.env" (
    echo %YELLOW%WARNING: .env file not found. Copying from .env.docker...%NC%
    copy "%PROJECT_ROOT%\.env.docker" "%PROJECT_ROOT%\.env"
    echo %YELLOW%Please edit .env file with your actual configuration%NC%
)
echo %GREEN%✓ Environment configuration ready%NC%

echo %GREEN%Prerequisites check completed successfully!%NC%
goto :eof

:build_images
echo %BLUE%Building Docker images...%NC%
cd /d "%PROJECT_ROOT%"
docker-compose build
if errorlevel 1 (
    echo %RED%ERROR: Failed to build images%NC%
    exit /b 1
)
echo %GREEN%Images built successfully!%NC%
goto :eof

:start_platform
echo %BLUE%Starting GTM Voyager Platform...%NC%
cd /d "%PROJECT_ROOT%"
docker-compose up -d
if errorlevel 1 (
    echo %RED%ERROR: Failed to start platform%NC%
    exit /b 1
)
echo %GREEN%Platform started successfully!%NC%
echo.
echo Access points:
echo - API Gateway: http://localhost:8000
echo - n8n Interface: http://localhost:5678
goto :eof

:stop_platform
echo %BLUE%Stopping GTM Voyager Platform...%NC%
cd /d "%PROJECT_ROOT%"
docker-compose down
echo %GREEN%Platform stopped%NC%
goto :eof

:show_status
echo %BLUE%GTM Voyager Platform Status:%NC%
cd /d "%PROJECT_ROOT%"
docker-compose ps
goto :eof

:view_logs
if "%2"=="" (
    echo %BLUE%Viewing all logs...%NC%
    cd /d "%PROJECT_ROOT%"
    docker-compose logs -f
 ) else (
    echo %BLUE%Viewing logs for %2...%NC%
    cd /d "%PROJECT_ROOT%"
    docker-compose logs -f %2
)
goto :eof

:show_help
echo Usage: %0 {check^|build^|start^|stop^|status^|logs}
echo.
echo Commands:
echo   check     Check prerequisites and configuration
echo   build     Build Docker images
echo   start     Start the platform
echo   stop      Stop the platform
echo   status    Show platform status
echo   logs      View logs (all services or specific service)
echo.
echo Examples:
echo   %0 check
echo   %0 build
echo   %0 start
echo   %0 logs api-gateway
goto :eof
