#!/bin/bash
# Sync Media zu Handy (nur neue/geänderte Files)

PHONE_IP="192.168.1.50"  # <-- Deine Handy IP hier
PHONE_USER="u0_a123"     # <-- Termux User (meist u0_aXXX)
PHONE_PORT="8022"        # Termux SSH Port

LOCAL_DIR="$HOME/.openclaw/workspace/media-collection/sorted/"
PHONE_DIR="/storage/emulated/0/Media/"

echo "📱 Syncing to phone..."
echo "   IP: $PHONE_IP"
echo ""

rsync -avz --progress \
  --include='*/' \
  --include='*.jpg' --include='*.png' --include='*.gif' \
  --include='*.mp4' --include='*.webm' \
  --exclude='*' \
  -e "ssh -p $PHONE_PORT" \
  "$LOCAL_DIR" \
  "$PHONE_USER@$PHONE_IP:$PHONE_DIR"

echo ""
echo "✅ Sync done!"
