@echo off
REM Start the FastAPI backend (API on http://localhost:8000)
cd /d "%~dp0"
echo Starting backend...

REM Prefer project venv if it exists (avoids broken "py" or missing PATH)
if exist "%~dp0.venv\Scripts\python.exe" (
  "%~dp0.venv\Scripts\python.exe" "%~dp0backend\app\main.py"
  goto :done
)
if exist "%~dp0venv\Scripts\python.exe" (
  "%~dp0venv\Scripts\python.exe" "%~dp0backend\app\main.py"
  goto :done
)

REM Then try python (venv activated, conda, or PATH)
where python >nul 2>&1
if %errorlevel% equ 0 (
  python "%~dp0backend\app\main.py"
  goto :done
)

REM Last: py launcher (often points to missing Python after reinstall)
where py >nul 2>&1
if %errorlevel% equ 0 (
  py "%~dp0backend\app\main.py"
  goto :done
)

REM Fallback: look for Python in common Windows install locations
for %%P in (
  "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
  "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
  "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
  "%ProgramFiles%\Python312\python.exe"
  "%ProgramFiles%\Python313\python.exe"
  "%ProgramFiles%\Python311\python.exe"
  "%USERPROFILE%\anaconda3\python.exe"
  "%USERPROFILE%\miniconda3\python.exe"
) do if exist %%P (
  echo Using: %%P
  %%P "%~dp0backend\app\main.py"
  goto :done
)

echo.
echo Python was not found. Do one of the following:
echo   1. Create a venv here:  python -m venv .venv   then  .venv\Scripts\activate   then  pip install -e .
echo   2. If you see "Unable to create process" above, "py" points to a removed Python. Use a venv or reinstall Python.
echo   3. Install Python 3.11+ from python.org and tick "Add Python to PATH".
echo.
pause
exit /b 1
:done
pause
