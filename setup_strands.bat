@echo off
REM Setup script for Strands SDK version (Windows)
REM Creates virtual environment and installs dependencies

echo.
echo ============================================================
echo   Setting up AWS Marketplace Listing Creator (Strands SDK)
echo ============================================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    echo Please install Python 3.8+ and add it to PATH
    pause
    exit /b 1
)
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
if exist venv (
    echo Virtual environment already exists
    set /p recreate="Remove and recreate? (y/n): "
    if /i "%recreate%"=="y" (
        rmdir /s /q venv
        python -m venv venv
        echo Virtual environment recreated
    ) else (
        echo Using existing virtual environment
    )
) else (
    python -m venv venv
    echo Virtual environment created
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1
echo pip upgraded
echo.

REM Install dependencies
echo Installing dependencies...
echo This may take a few minutes...
pip install -r requirements_strands.txt
echo Dependencies installed
echo.

REM Check AWS credentials
echo Checking AWS credentials...
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo AWS credentials not configured
    echo Run: aws configure
) else (
    echo AWS credentials configured
)
echo.

REM Run tests
echo Running tests...
python test_strands_migration.py
if errorlevel 1 (
    echo.
    echo ============================================================
    echo   Setup complete but tests failed
    echo ============================================================
    echo.
    echo Common issues:
    echo.
    echo 1. AWS credentials not configured:
    echo    aws configure
    echo.
    echo 2. Bedrock models not enabled:
    echo    Go to: https://console.aws.amazon.com/bedrock/
    echo    Enable: Claude 3.7 Sonnet
    echo.
    echo 3. Missing dependencies:
    echo    pip install -r requirements_strands.txt
    echo.
    echo Run tests again:
    echo    python test_strands_migration.py
    echo.
) else (
    echo.
    echo ============================================================
    echo   Setup complete! Everything is working.
    echo ============================================================
    echo.
    echo Next steps:
    echo.
    echo 1. Activate the virtual environment (if not already active):
    echo    venv\Scripts\activate.bat
    echo.
    echo 2. Run the Streamlit app:
    echo    streamlit run streamlit_strands_app.py
    echo.
    echo 3. Or use Python directly:
    echo    python -c "from agent.strands_marketplace_agent import StrandsMarketplaceAgent; agent = StrandsMarketplaceAgent(); print(agent.process_message('Create a listing'))"
    echo.
    echo 4. Deploy to AgentCore (optional):
    echo    pip install bedrock-agentcore-cli
    echo    agentcore configure --config agentcore_config.yaml
    echo    agentcore launch
    echo.
    echo Documentation:
    echo    - Quick Start: QUICKSTART_STRANDS.md
    echo    - Full Guide: README_STRANDS.md
    echo    - Migration: MIGRATION_GUIDE.md
    echo.
)

pause
