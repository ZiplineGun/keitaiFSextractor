@echo off
cd "%~dp0"
if not exist keitaiFSextractor\virtual_env\Scripts\activate (
    echo A Python virtual environment has not been created. Please run Install_tools.bat first.
    exit/b 1
)

call keitaiFSextractor\virtual_env\Scripts\activate

if "%~1"=="" (
    echo There are no arguments.
    echo Usage: Extract.bat input_file [input_file ...]
    pause
    exit /b 1
)

cls
python keitaiFSextractor\main.py %*
pause