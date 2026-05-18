@echo off
setlocal enabledelayedexpansion
chcp 1251 >nul
title snbld resvap - Build (Nuitka)
cd /d "%~dp0"

echo.
echo ===========================================
echo    BUILD SNBLD RESVAP (NUITKA)
echo ===========================================
echo Folder: %CD%
echo Date: %DATE% %TIME%
echo.

echo [1/8] Python check...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo    OK: %%i

echo.
echo [2/8] Nuitka check...
python -c "import nuitka" 2>nul
if errorlevel 1 (
    echo    Installing Nuitka...
    pip install nuitka -q
)
python -c "import nuitka" 2>nul
if errorlevel 1 (
    echo ERROR: Nuitka not installed!
    pause
    exit /b 1
)
echo    OK: Nuitka installed

echo.
echo [3/8] Inno Setup check...

set ISCC_PATH=
for %%p in ("C:\Program Files (x86)\Inno Setup 6" "C:\Program Files\Inno Setup 6" "%LOCALAPPDATA%\Programs\Inno Setup 6") do (
    if exist "%%~p\ISCC.exe" set ISCC_PATH=%%~p\ISCC.exe
)

if defined ISCC_PATH (
    echo    OK: Inno Setup found
) else (
    echo ERROR: Inno Setup 6 not found!
    echo    Download from: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

echo.
echo [4/8] Main files check...

if exist "qml\" (
    echo    OK: qml
) else (
    echo ERROR: qml folder not found!
    pause
    exit /b 1
)

for %%f in (icons 123.ico onn.mp3 off.mp3) do (
    if exist "%%f" (
        echo    OK: %%f
    ) else (
        echo ERROR: %%f not found!
        pause
        exit /b 1
    )
)

echo.
echo [5/8] Running build_nuitka.py...
echo.

python build_nuitka.py

if errorlevel 1 (
    echo.
    echo ERROR: build_nuitka.py failed!
    pause
    exit /b 1
)

echo.
echo    OK: Nuitka build completed

echo.
echo [6/7] Checking upload dependencies...

python -c "import paramiko" 2>nul
if errorlevel 1 (
    echo    Installing paramiko, dotenv, boto3...
    pip install paramiko boto3 python-dotenv -q
)
python -c "import paramiko,boto3; from dotenv import load_dotenv" 2>nul
if errorlevel 1 (
    echo ERROR: Upload dependencies not installed!
    pause
    exit /b 1
)
echo    OK: Dependencies installed

echo.
echo [7/7] Check upload config...

:: Check Beget config
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('BEGET_OK' if os.environ.get('BEGET_SSH_HOST') else 'BEGET_MISSING')" > "%TEMP%\check_beget.txt"
set /p BEGET_CHECK=<"%TEMP%\check_beget.txt"
del "%TEMP%\check_beget.txt"

:: Check Selectel config
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('SEL_OK' if os.environ.get('SELECTEL_ACCESS_KEY') else 'SEL_MISSING')" > "%TEMP%\check_sel.txt"
set /p SEL_CHECK=<"%TEMP%\check_sel.txt"
del "%TEMP%\check_sel.txt"

:: Upload to Beget if configured (uses enabledelayedexpansion for !BEGET_CHECK!)
if not "!BEGET_CHECK!"=="BEGET_OK" (
    echo SKIP: Beget config not found
) else (
    echo [7/7] Uploading installer to Beget...
    for /f "delims=" %%i in ('python -c "from pathlib import Path; f=list(Path('dist_installers').glob('snbldsetup*.exe'))[0]; print(f.name)"') do set "INSTALLER_NAME=%%i"
    if defined INSTALLER_NAME (
        python -c "import socket; socket.setdefaulttimeout(30); import os,sys,paramiko; from pathlib import Path; from dotenv import load_dotenv; load_dotenv(); f=list(Path('dist_installers').glob('snbldsetup*.exe'))[0]; s=paramiko.SSHClient(); s.set_missing_host_key_policy(paramiko.AutoAddPolicy()); s.connect(os.environ['BEGET_SSH_HOST'], username=os.environ['BEGET_SSH_USER'], password=os.environ['BEGET_SSH_PASSWORD'], timeout=30); sf=s.open_sftp(); remote_path='/home/s/snbld/snbld.beget.tech/public_html/downloads/'+f.name; print(f'Uploading {f.name} -> {remote_path}'); sf.put(str(f), remote_path); sf.close(); s.close(); print('OK')"
        if errorlevel 1 (
            echo WARNING: Upload failed!
        ) else (
            echo    OK: Uploaded
        )
    ) else (
        echo WARNING: Installer not found in dist_installers!
    )
)

echo.
echo ✅ version.json upload SKIPPED. Use deploy_update.bat when you are ready to roll out update to all users.

echo.
echo ===========================================
echo BUILD COMPLETE
echo ===========================================

dir /b dist_installers\

pause
exit /b 0