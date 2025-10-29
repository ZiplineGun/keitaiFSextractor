@echo off
where python >nul 2>nul
if errorlevel 1 (
    echo python is not installed or not in PATH.
    exit /b 1
)

if not exist %~dp0\keitaiFSextractor\tools (
    echo The keitaiFSextractor folder that should be present is missing, so the process has terminated.
    exit/b 1
)

cd keitaiFSextractor
if not exist virtual_env (
    echo Creating a virtual environment for Python...
    python -m venv virtual_env
)
call virtual_env\Scripts\activate

echo Installing Python packages...
pip install Qiling==1.4.6 unicorn==2.0.1.post1 requests scsu

rem for dumpefs2
pip install reedsolo construct crcmod

rem for jefferson
pip install click==8.1.7 colorama==0.4.6 cstruct==6.1 lzallright==0.2.6

echo ===============================
echo Downloading the necessary tools...
python download_tools.py

copy /y tools\extract_fat.ini tools\TSK-FAT-AutoRecover

pause