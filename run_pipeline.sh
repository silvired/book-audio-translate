#!/bin/bash

# Pipeline script for PDF to Audio conversion
# This script handles Python version detection and dependency installation

echo "=== PDF to Audio Pipeline ==="
echo "Detecting Python version..."

# Function to provide installation instructions
install_instructions() {
    echo ""
    echo "=== Installation Instructions ==="
    echo "To install Python 3.10+ on macOS:"
    echo "1. Install Homebrew (if not already installed):"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo ""
    echo "2. Install Python 3.10:"
    echo "   brew install python@3.10"
    echo ""
    echo "3. Add to PATH (add to ~/.zshrc or ~/.bash_profile):"
    echo "   export PATH=\"/opt/homebrew/bin:\$PATH\""
    echo ""
    echo "4. Restart your terminal and try again"
    echo ""
}

# Function to check if a Python version is available
check_python() {
    local version=$1
    if command -v "$version" &> /dev/null; then
        echo "Found $version: $(command -v $version)"
        return 0
    else
        # Try common installation paths
        local common_paths=(
            "/opt/homebrew/bin/$version"
            "/usr/local/bin/$version"
            "/usr/bin/$version"
            "/opt/anaconda3/bin/$version"
        )
        for path in "${common_paths[@]}"; do
            if [ -f "$path" ]; then
                echo "Found $version: $path"
                PYTHON_FULL_PATH="$path"
                return 0
            fi
        done
        return 1
    fi
}

# Try different Python versions in order of preference (TTS supports 3.9-3.11)
PYTHON_CMD=""
PYTHON_FULL_PATH=""

if check_python "python3.11"; then
    PYTHON_CMD="python3.11"
    [ -n "$PYTHON_FULL_PATH" ] && PYTHON_CMD="$PYTHON_FULL_PATH"
elif check_python "python3.10"; then
    PYTHON_CMD="python3.10"
    [ -n "$PYTHON_FULL_PATH" ] && PYTHON_CMD="$PYTHON_FULL_PATH"
elif check_python "python3.9"; then
    echo "Warning: Python 3.9 detected. TTS may have compatibility issues."
    echo "Consider upgrading to Python 3.10+ for better compatibility."
    read -p "Continue with Python 3.9? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        PYTHON_CMD="python3.9"
        [ -n "$PYTHON_FULL_PATH" ] && PYTHON_CMD="$PYTHON_FULL_PATH"
    else
        echo "Please install Python 3.10+ and try again."
        install_instructions
        exit 1
    fi
elif check_python "python3"; then
    echo "Warning: Python 3 detected. Checking version..."
    PYTHON_VERSION=$($(command -v python3) --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
    if [[ "$PYTHON_VERSION" < "3.10" ]]; then
        echo "Error: Python $PYTHON_VERSION detected. TTS requires Python 3.10+"
        install_instructions
        exit 1
    else
        PYTHON_CMD="python3"
    fi
elif check_python "python"; then
    echo "Warning: Python detected. Checking version..."
    PYTHON_VERSION=$($(command -v python) --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
    if [[ "$PYTHON_VERSION" < "3.10" ]]; then
        echo "Error: Python $PYTHON_VERSION detected. TTS requires Python 3.10+"
        install_instructions
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    echo "Error: No Python version found!"
    echo "Please install Python 3.10+ for TTS compatibility"
    install_instructions
    exit 1
fi

echo "Using Python: $PYTHON_CMD"
echo "Python version: $($PYTHON_CMD --version)"

# Check if we're in the correct directory
if [ ! -f "run_pipeline_v2.py" ]; then
    echo "Error: run_pipeline_v2.py not found!"
    echo "Please run this script from the project root directory"
    exit 1
fi

echo ""
echo "=== Installing Dependencies ==="

# Install TTS
echo "Installing TTS..."
$PYTHON_CMD -m pip install TTS

# Install pydub
echo "Installing pydub..."
$PYTHON_CMD -m pip install pydub

# Install other required packages
echo "Installing additional dependencies..."
$PYTHON_CMD -m pip install PyPDF2 pymupdf

echo ""
echo "=== Running Pipeline ==="

# Update the pipeline script to use the detected Python version
echo "Updating pipeline to use $PYTHON_CMD..."

# Create a temporary version of the pipeline with the correct Python version
sed "s/python3\.10/$PYTHON_CMD/g" run_pipeline_v2.py > run_pipeline_temp.py

# Run the pipeline
$PYTHON_CMD run_pipeline_temp.py

# Clean up temporary file
rm run_pipeline_temp.py

echo ""
echo "=== Pipeline Complete ===" 