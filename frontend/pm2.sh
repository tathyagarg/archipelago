#!/bin/bash

# Thank you Cyteon!

APP_NAME="archipelago"
DEFAULT_PORT=41965
PORT=${1:-$DEFAULT_PORT}

echo "Starting $APP_NAME on port $PORT"

npm run build

PORT=$PORT pm2 start build/index.js --name "$APP_NAME-frontend"
pm2 save

echo "Started $APP_NAME on port $PORT successfully"

