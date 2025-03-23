#!/bin/bash

echo "Setting up RunPod deployment..."

# Make cleanup script executable
chmod +x cleanup.sh

# Run cleanup
./cleanup.sh

echo "Project structure is now clean and ready for deployment."
echo 
echo "Directory structure:"
echo "==================="
tree -L 3 ../ --gitignore

echo
echo "Next steps:"
echo "1. Build Docker image:"
echo "   docker build -f Dockerfile.runpod -t your-registry/fish-speech:latest ."
echo
echo "2. Push to registry:"
echo "   docker push your-registry/fish-speech:latest"
echo
echo "3. Deploy to RunPod following runpod/README.md"
