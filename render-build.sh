#!/bin/bash

# Update pip and install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install system dependencies for Playwright
apt-get update && apt-get install -y \
  libnss3 \
  libatk1.0-0 \
  libatk-bridge2.0-0 \
  libcups2 \
  libasound2 \
  libxrandr2 \
  libxkbcommon-x11-0 \
  fonts-liberation \
  libappindicator3-1 \
  libx11-xcb1

# Install Playwright's Node.js dependencies
npm install @playwright/test

# Install Playwright browsers using npx
npx playwright install --with-deps
