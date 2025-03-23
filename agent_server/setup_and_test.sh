#!/bin/bash

# Function to check CUDA
check_cuda() {
    echo "Checking CUDA..."
    python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
}

# Function to check GPU memory
check_gpu() {
    echo -e "\nChecking GPU memory..."
    if command -v nvidia-smi &> /dev/null; then
        nvidia-smi
    else
        echo "nvidia-smi not found. Skip GPU check."
    fi
}

# Function to setup virtual environment
setup_venv() {
    echo -e "\nSetting up virtual environment..."
    if [ ! -d "venv" ]; then
        python -m venv venv
        echo "Virtual environment created."
    else
        echo "Virtual environment already exists."
    fi

    # Activate virtual environment
    source venv/bin/activate || source venv/Scripts/activate
    
    # Update pip
    python -m pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
}

# Function to download models
download_models() {
    echo -e "\nDownloading models..."
    mkdir -p checkpoints
    
    # Download Fish Agent model if not exists
    if [ ! -d "checkpoints/fish-agent-v0.1-3b" ]; then
        echo "Downloading Fish Agent model..."
        huggingface-cli download fishaudio/fish-agent-v0.1-3b --local-dir checkpoints/fish-agent-v0.1-3b
    else
        echo "Fish Agent model already exists."
    fi
    
    # Download Fish Speech model if not exists
    if [ ! -d "checkpoints/fish-speech-1.4" ]; then
        echo "Downloading Fish Speech model..."
        huggingface-cli download fishaudio/fish-speech-1.4 --local-dir checkpoints/fish-speech-1.4
    else
        echo "Fish Speech model already exists."
    fi
}

# Function to record test audio
record_audio() {
    echo -e "\nDo you want to record test audio for voice cloning? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        python record_test_audio.py
    fi
}

# Function to run tests
run_tests() {
    echo -e "\nRunning tests..."
    python test_local.py
}

# Main execution
echo "Fish Agent API Local Test Setup"
echo "=============================="

# Check if running with Python < 3.12
PYTHON_VERSION=$(python -c 'import sys; print(sys.version_info.minor)')
if [ "$PYTHON_VERSION" -ge 12 ]; then
    echo "Error: Python version must be below 3.12 for compile mode"
    exit 1
fi

# Execute setup steps
check_cuda
check_gpu
setup_venv
download_models
record_audio
run_tests

echo -e "\nSetup and testing completed!"
