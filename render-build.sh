#!/bin/bash
# set -e
# pip install --upgrade pip
# pip install -r requirements.txt
# apt-get update && apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2
# npx playwright install --with-deps
# playwright install --with-deps

#!/usr/bin/env bash
# Install system dependencies
apt-get update && apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libasound2 libxrandr2 libxkbcommon-x11-0

npm install 
npm install @playwright/test 

# Install Playwright browsers
npx playwright install --with-deps
