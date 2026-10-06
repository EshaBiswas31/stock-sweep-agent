@echo off
REM push.bat -- commits any changes and pushes to GitHub, which auto-redeploys on Vercel.
REM Save this file inside your project folder (E:\mini_stock_project\mini_project)
REM and double-click it any time after you edit the code.

cd /d %~dp0

echo.
echo Checking for changes...
git add .

set /p msg="Describe your change (or press Enter for a default message): "
if "%msg%"=="" set msg=Update project

git commit -m "%msg%"
if errorlevel 1 (
    echo.
    echo Nothing new to commit, or commit failed. Skipping push.
    pause
    exit /b
)

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo Done. Vercel will auto-redeploy in a minute or two.
pause
