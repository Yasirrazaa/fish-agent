#!/bin/bash

# Install system dependencies
install_system_deps() {
    echo "Installing system dependencies..."
    sudo apt-get update
    sudo apt-get install -y \
        python3-pip \
        python3-venv \
        portaudio19-dev \
        ffmpeg \
        nvidia-cuda-toolkit
}

# Install Python dependencies
setup_python() {
    echo "Setting up Python environment..."
    
    # Create virtual environment
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Update pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
}

# Check CUDA setup
check_cuda() {
    echo "Checking CUDA setup..."
    if ! command -v nvidia-smi &> /dev/null; then
        echo "Error: nvidia-smi not found. Please install NVIDIA drivers."
        exit 1
    fi
    
    echo "GPU Information:"
    nvidia-smi
    
    echo -e "\nCUDA Test:"
    python3 -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('CUDA version:', torch.version.cuda if torch.cuda.is_available() else 'N/A')"
}

# Download models
download_models() {
    echo "Downloading models..."
    mkdir -p checkpoints
    
    # Install huggingface-cli if not installed
    pip install --upgrade huggingface-hub
    
    # Download models
    huggingface-cli download fishaudio/fish-agent-v0.1-3b --local-dir checkpoints/fish-agent-v0.1-3b
    huggingface-cli download fishaudio/fish-speech-1.4 --local-dir checkpoints/fish-speech-1.4
}

# Main setup
echo "Fish Agent API - Ubuntu Setup"
echo "==========================="

# Check Python version
python_version=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$python_version" -ge 12 ]; then
    echo "Error: Python version must be below 3.12 for compile mode"
    echo "Current version: Python 3.$python_version"
    exit 1
fi

# Run setup steps
echo "Starting setup..."
install_system_deps
setup_python
check_cuda
download_models

echo -e "\nSetup completed! You can now run the tests:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo "2. Run the test script:"
echo "   python test_local.py"
echo -e "\nFor voice cloning tests:"
echo "1. Record test audio:"
echo "   python record_test_audio.py"
echo "2. Run tests again to include voice cloning"

# Make setup_and_test.sh executable
chmod +x setup_and_test.sh
