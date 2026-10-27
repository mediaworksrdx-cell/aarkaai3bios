@echo off
:: Self-elevate to Administrator if not already elevated
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting Administrator privileges to update DNS and Hosts file...
    powershell -Command "Start-Process cmd.exe -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

title Aarka AI - Azure DNS Connector
color 0A
echo =======================================================
echo          CONNECTING AARKA AI TO AZURE VM
echo =======================================================
echo.

set HOSTS_FILE=%SystemRoot%\System32\drivers\etc\hosts

:: Remove any outdated mappings for these domains
powershell -Command "$file = '%HOSTS_FILE%'; if (Test-Path $file) { (Get-Content $file) | Where-Object { $_ -notmatch 'aarka-ai|synthetixanalytics|fingeniq' } | Set-Content $file }"

:: Map domains directly to Azure IP
echo 138.91.105.85 aarka-ai.com www.aarka-ai.com >> "%HOSTS_FILE%"
echo 138.91.105.85 synthetixanalytics.com www.synthetixanalytics.com >> "%HOSTS_FILE%"
echo 138.91.105.85 fingeniq.com www.fingeniq.com >> "%HOSTS_FILE%"

echo [OK] Windows Hosts file mapped to Azure (138.91.105.85).

:: Set DNS to Google DNS & Cloudflare DNS on active network adapters
powershell -Command "Get-NetAdapter | Where-Object Status -eq 'Up' | ForEach-Object { Set-DnsClientServerAddress -InterfaceIndex $_.InterfaceIndex -ServerAddresses ('8.8.8.8','1.1.1.1') -ErrorAction SilentlyContinue }"
echo [OK] High-speed DNS configured (8.8.8.8 / 1.1.1.1).

:: Flush DNS
ipconfig /flushdns >nul
echo [OK] Windows DNS Cache flushed.

echo.
echo =======================================================
echo    SUCCESS: aarka-ai.com is now connected to Azure!
echo =======================================================
echo.
echo Opening https://aarka-ai.com in your default browser...
start https://aarka-ai.com

timeout /t 4 >nul
exit
