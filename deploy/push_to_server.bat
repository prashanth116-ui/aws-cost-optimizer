@echo off
:: Push AWS Cost Optimizer to DigitalOcean server
:: Usage: push_to_server.bat YOUR_DROPLET_IP

if "%1"=="" (
    echo Usage: push_to_server.bat YOUR_DROPLET_IP
    echo Example: push_to_server.bat 167.99.123.45
    exit /b 1
)

set SERVER=%1
set REPO_DIR=C:\Users\vkudu\claude-projects\aws-cost-optimizer

echo === Pushing AWS Cost Optimizer to Server: %SERVER% ===

:: Push credentials if exists
if exist "%REPO_DIR%\config\credentials.yaml" (
    echo.
    echo Step 1: Uploading credentials...
    scp "%REPO_DIR%\config\credentials.yaml" root@%SERVER%:~/aws-cost-optimizer/config/
) else (
    echo.
    echo Note: No credentials.yaml found, skipping...
)

:: Update code on server and restart
echo.
echo Step 2: Updating code and restarting dashboard...
ssh root@%SERVER% "cd ~/aws-cost-optimizer && git pull && sudo systemctl restart cost-optimizer"

echo.
echo === Done! Dashboard running at http://%SERVER%:8501 ===
echo.
echo View logs: ssh root@%SERVER% "sudo journalctl -u cost-optimizer -f"
pause
