#!/bin/bash

# Load environment variables if .env file exists
if [ -f .env ]; then
  echo "Loading environment from .env file"
  export $(grep -v '^#' .env | xargs)
fi

echo "Updating knowledge base from Obsidian repository..."
python backend/app/services/webhook_handler.py "$@"

# Check if the update was successful
if [ $? -eq 0 ]; then
  echo "✅ Knowledge base updated successfully!"
else
  echo "❌ Failed to update knowledge base"
  exit 1
fi
