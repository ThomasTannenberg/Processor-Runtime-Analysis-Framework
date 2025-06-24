@echo off
ECHO Cleaning up old stats files...
del /q python_stats.yaml 2>nul
del /q ruby_stats.yaml 2>nul
del /q java_stats.yaml 2>nul
del /q rust_stats.yaml 2>nul

ECHO.

REM Start Ruby script
echo Starting Ruby workers...
start "Ruby" cmd /k "ruby ruby_multitask.rb"

REM Start Java application
echo Starting Java workers...
start "Java" cmd /k "java -jar java-benchmark-runner.jar"

REM Start Rust application
echo Starting Rust workers...
start "Rust" rust_multitask.exe

REM Start Python script, which also acts as the dashboard
echo Starting Python workers and dashboard...
start "Python Dashboard" cmd /k "python python_multitask.py"

echo All four scripts have been started.
pause