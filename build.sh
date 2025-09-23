#!/bin/bash
# Build script for Render deployment
cd frontend && npm install --production=false && NODE_ENV=production npm run build