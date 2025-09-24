#!/bin/bash
# Startup script for AI Visibility backend
# This script initializes the database and then starts the application

echo "Starting AI Visibility backend..."

# Run database initialization
echo "Initializing database..."
python init_database.py

# Check if database initialization was successful
if [ $? -eq 0 ]; then
    echo "Database initialization successful!"
else
    echo "Warning: Database initialization had issues, but continuing..."
fi

# Start the main application
echo "Starting Uvicorn server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000