#!/bin/bash
# Build script for Render deployment
export NODE_ENV=production
cd frontend && npm install && NODE_ENV=production npm run build