@echo off
REM OpenClass Nexus AI Installation Script

echo Installing OpenClass Nexus AI...

REM Check Python version
python --version || (echo Python 3.8+ required && exit /b 1)

REM Create virtual environment
python -m venv openclass-env
call openclass-env\Scripts\activate.bat

REM Install dependencies
pip install -r requirements.txt

REM Setup configuration
copy config\templates\default_config.yaml config\app_config.yaml

echo Installation completed successfully!
echo Activate environment: openclass-env\Scripts\activate.bat
echo Run setup: python scripts\setup_phase2_aws.py
