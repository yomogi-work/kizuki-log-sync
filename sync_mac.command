#!/bin/bash
cd "$(dirname "$0")"

echo "========================================="
echo " Kizuki Log: GitHub Sync (Mac)"
echo "========================================="

echo "[1/3] Fetching latest changes from GitHub..."
git pull origin main --rebase
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Failed to pull changes. Please check your internet connection or resolve merge conflicts."
    read -p "Press [Enter] key to exit..."
    exit 1
fi

echo ""
echo "[2/3] Adding local changes..."
git add .
git commit -m "Auto-sync from Mac: $(date '+%Y-%m-%d %H:%M:%S')"

echo ""
echo "[3/3] Uploading changes to GitHub..."
git push origin main
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Failed to push changes."
    read -p "Press [Enter] key to exit..."
    exit 1
fi

echo ""
echo "========================================="
echo " Sync Completed Successfully!"
echo "========================================="
sleep 3
