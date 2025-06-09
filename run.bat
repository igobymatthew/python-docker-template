@echo off
REM Usage: run.bat script.py [args...]

docker image inspect py310-base >nul 2>&1
IF ERRORLEVEL 1 (
    echo Building Docker image py310-base...
    docker build -t py310-base .
)

docker run --rm ^
 -v "%cd%:/app" ^
 -w /app ^
 py310-base ^
 python ./src/%*
