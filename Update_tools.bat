@echo off
if not exist "%~dp0\keitaiFSextractor" (
    exit/b
)

cd "%~dp0\keitaiFSextractor"

echo Updating tools...
python download_tools.py

copy /y tools\extract_fat.ini tools\TSK-FAT-AutoRecover

pause