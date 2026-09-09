#!/bin/bash
# Restore Ada runtime (~/.hermes) from the backup tarball in this directory,
# then launch Ada Chat.
#
# Expects an ada-backup-*.tar.zst (or .tar.gz/.tar) in the same directory.
# Get one from https://github.com/gsantana212/ada-containers-backup (releases).
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BALL="$(ls "$DIR"/ada-backup-*.tar.zst "$DIR"/ada-backup-*.tar.gz "$DIR"/ada-backup-*.tar 2>/dev/null | head -1 || true)"
if [ -z "$BALL" ]; then
  echo "ERROR: no ada-backup-*.tar.* found in $DIR"
  echo "Download the latest backup tarball from ada-containers-backup and place it here, then re-run."
  exit 1
fi
echo "Restoring from: $BALL"
mkdir -p "$HOME/.hermes"
case "$BALL" in
  *.tar.zst) tar --zstd -xf "$BALL" -C "$HOME/.hermes" ;;
  *.tar.gz)  tar -xzf "$BALL" -C "$HOME/.hermes" ;;
  *.tar)     tar -xf "$BALL" -C "$HOME/.hermes" ;;
esac
echo "~/.hermes rehydrated."
python3 "$DIR/ada-chat.py"
