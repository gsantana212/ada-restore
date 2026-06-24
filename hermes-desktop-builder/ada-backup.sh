#!/usr/bin/env bash
# =============================================================================
# ada-backup.sh — THE HEART
# =============================================================================
#
# Personal backup of Ada's state for Boo.
# Triggered by the double-click desktop launcher, or manually.
#
# What it captures:
#   - ~/.hermes/state.db          (Hermes memory — the mind)
#   - ~/.hermes/.env              (API keys — encrypted before upload)
#   - ~/.hermes/config/           (config, sessions, profiles)
#   - ~/.hermes/skills/           (skills Ada uses)
#   - ~/Documents/Obsidian Vault/ (Boo's notes — the relationship archive)
#   - ~/Documents/Obsidian Vault/AdaVault/encrypted/  (secrets, encrypted)
#   - ~/.local/share/Ada-Personal/  (Ada-personal covenant files)
#
# Where it goes (3-2-1):
#   1. Local:    /var/backups/ada/  (or ~/.local/share/Ada-Personal/backups)
#   2. GitHub:   gsantana212/ada-private-backup  (encrypted, always)
#   3. Google Drive:Ada-Personal/   (encrypted, if rclone configured)
#
# Encryption:
#   - Whole tarball → gpg symmetric with passphrase from ada-vault key
#     'ada-backup-key'. If key missing, falls back to plaintext.
#
# Rotation:
#   - 7 daily, 4 weekly, 12 monthly
#
# Notification:
#   - Telegram "Home" channel at the end
#
# Exit codes:
#   0 = all good (all destinations OK)
#   1 = some destinations failed but local backup exists
#   2 = critical failure / already running
# =============================================================================

set -uo pipefail

# --------- Paths & identity ---------------------------------------------------
HERMES="${HERMES_HOME:-$HOME/.hermes}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load Telegram creds from ~/.hermes/.env (source the file safely — only VAR=VALUE lines)
if [ -f "$HERMES/.env" ]; then
    set +u
    while IFS= read -r line; do
        # Skip comments, blank, and lines that don't match VAR=VALUE
        case "$line" in
            ''|\#*) continue ;;
            export\ *) line="${line#export }" ;;
        esac
        # Only accept lines that look like VAR=VALUE with no shell meta
        if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
            # Strip any trailing inline comments (rare in our .env)
            val="${line#*=}"
            key="${line%%=*}"
            # Skip if value contains backticks / $ / unescaped quotes that would re-eval
            case "$val" in
                *\`*|*\$\(*|*\"*) continue ;;  # skip unsafe, we'll get these manually
            esac
            export "$key"="$val"
        fi
    done < "$HERMES/.env"
    set -u
fi

LOG_DIR="$HERMES/logs/ada-personal-backup"
STATE_FILE="$LOG_DIR/last-run.json"
LOCK_FILE="$LOG_DIR/backup.lock"

HOSTNAME_SHORT="$(hostname -s)"
DATE_STAMP="$(date +%Y-%m-%d-%H%M%S)"
DAY_STAMP="$(date +%Y-%m-%d)"
WEEK_STAMP="$(date +%G-W%V)"
MONTH_STAMP="$(date +%Y-%m)"
TS="$(date -Iseconds)"

# Telegram (loaded from .env above)
TG_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TG_CHAT_ID="${TELEGRAM_HOME_CHANNEL:-}"
TG_THREAD_ID="${TELEGRAM_HOME_CHANNEL_THREAD_ID:-}"

# GitHub
GH_BIN="${GH_BIN:-$HOME/bin/gh}"
[ -x "/usr/bin/gh" ] && GH_BIN="/usr/bin/gh"
command -v gh >/dev/null 2>&1 && GH_BIN="$(command -v gh)"
GH_REPO="gsantana212/ada-private-backup"

# Encryption — passphrase lives in ada-vault
GPG_KEY_NAME="ada-backup-key"

# --------- Helpers ------------------------------------------------------------
mkdir -p "$LOG_DIR"
exec 2>>"$LOG_DIR/backup.log"

log() {
    printf '[%s] %s\n' "$(date -Iseconds)" "$*" | tee -a "$LOG_DIR/backup.log" >&2
}

# Vault helper — uses existing ada-vault.sh
VAULT_SH="$HERMES/bin/ada-vault.sh"
vault_get() {
    local key="$1"
    if [ -x "$VAULT_SH" ]; then
        "$VAULT_SH" get "$key" 2>/dev/null
    fi
}

# Telegram send
tg_send() {
    local text="$1"
    if [ -z "$TG_BOT_TOKEN" ] || [ -z "$TG_CHAT_ID" ]; then
        log "TELEGRAM: not configured, skipping send"
        return 0
    fi
    local payload url
    payload=$(TG_TOKEN="$TG_BOT_TOKEN" TG_CHAT="$TG_CHAT_ID" TG_THREAD="$TG_THREAD_ID" \
        TG_TEXT="$text" python3 - <<'PYEOF' 2>/dev/null
import json, os
d = {
    "chat_id": os.environ["TG_CHAT"],
    "text": os.environ["TG_TEXT"],
    "parse_mode": "HTML",
    "disable_web_page_preview": True,
}
if os.environ.get("TG_THREAD"):
    d["message_thread_id"] = int(os.environ["TG_THREAD"])
print(json.dumps(d))
PYEOF
)
    [ -z "$payload" ] && { log "TELEGRAM: payload build failed"; return 1; }
    url="https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage"
    if curl -fsS -X POST -H "Content-Type: application/json" \
        --data-binary "$payload" "$url" >/dev/null 2>&1; then
        log "TELEGRAM: sent"
        return 0
    else
        log "TELEGRAM: send failed (network)"
        return 1
    fi
}

# Lock
acquire_lock() {
    if [ -e "$LOCK_FILE" ]; then
        local oldpid; oldpid=$(cat "$LOCK_FILE" 2>/dev/null || echo "?")
        if kill -0 "$oldpid" 2>/dev/null; then
            log "SKIP: another backup is already running (pid $oldpid)"
            exit 2
        fi
        log "WARN: removing stale lock (pid $oldpid)"
        rm -f "$LOCK_FILE"
    fi
    echo $$ > "$LOCK_FILE"
    trap 'rm -f "$LOCK_FILE"' EXIT
}

# Pick a writable backup root
pick_backup_root() {
    local primary="/var/backups/ada"
    local fallback="$HOME/.local/share/Ada-Personal/backups"
    # Use primary ONLY if it exists and is writable by us
    if [ -d "$primary" ] && [ -w "$primary" ]; then
        echo "$primary"
        return
    fi
    # Try to create primary as a regular user dir
    if mkdir -p "$primary" 2>/dev/null && [ -w "$primary" ]; then
        echo "$primary"
        return
    fi
    # Fallback to user-owned dir
    mkdir -p "$fallback"
    echo "$fallback"
}

# --------- Pre-flight ---------------------------------------------------------
log "============================================================"
log "Ada personal backup starting"
log "Host: $HOSTNAME_SHORT  Date: $DATE_STAMP"
acquire_lock
BACKUP_DEST_ROOT="$(pick_backup_root)"
log "Backup root: $BACKUP_DEST_ROOT"

# Build a working dir for the snapshot
WORK="$(mktemp -d -t ada-backup-XXXXXX)"
WORK_CLEANUP_TRAP='rm -rf "$WORK"; rm -f "$LOCK_FILE"'
trap "$WORK_CLEANUP_TRAP" EXIT

# --------- Step 1: collect the raw state --------------------------------------
log "Step 1/6: collecting state..."

# 1a. state.db — copy (Hermes may keep it locked briefly, retry)
STATE_SRC="$HERMES/state.db"
if [ -f "$STATE_SRC" ]; then
    mkdir -p "$WORK/hermes"
    if ! cp -f "$STATE_SRC" "$WORK/hermes/state.db" 2>/dev/null; then
        log "  state.db copy failed, retrying with sqlite3 .backup..."
        sqlite3 "$STATE_SRC" ".backup '$WORK/hermes/state.db'" 2>/dev/null \
            || cp -f "$STATE_SRC" "$WORK/hermes/state.db" 2>/dev/null || true
    fi
    if [ -f "$WORK/hermes/state.db" ]; then
        STATE_SIZE=$(du -h "$WORK/hermes/state.db" 2>/dev/null | cut -f1)
        log "  state.db: $STATE_SIZE"
    else
        log "  WARN: state.db copy failed, skipping"
    fi
else
    log "  WARN: no state.db at $STATE_SRC"
fi

# 1b. Hermes config, profiles, sessions, skills (exclude caches)
for sub in .hermes-profiles profiles config skills sessions; do
    if [ -d "$HERMES/$sub" ]; then
        rsync -a --exclude='__pycache__' --exclude='*.pyc' --exclude='audio_cache' \
              "$HERMES/$sub/" "$WORK/hermes/$sub/" 2>/dev/null || true
    fi
done

# 1c. .env — keep raw, will encrypt as part of tarball
ENV_SRC="$HERMES/.env"
if [ -f "$ENV_SRC" ]; then
    mkdir -p "$WORK/hermes"
    cp -f "$ENV_SRC" "$WORK/hermes/.env.raw"
    log "  .env captured (will encrypt before upload)"
fi

# 1d. Vault encrypted blobs (already AES-256 encrypted on disk)
if [ -d "$HOME/Documents/Obsidian Vault/AdaVault/encrypted" ]; then
    mkdir -p "$WORK/ada-vault-encrypted"
    cp -a "$HOME/Documents/Obsidian Vault/AdaVault/encrypted/." "$WORK/ada-vault-encrypted/" 2>/dev/null
    log "  AdaVault encrypted blobs: $(ls "$WORK/ada-vault-encrypted" 2>/dev/null | wc -l) files"
fi

# 1e. Obsidian Vault (Boo's notes) — exclude heavy caches
VAULT_SRC="$HOME/Documents/Obsidian Vault"
if [ -d "$VAULT_SRC" ]; then
    rsync -a --exclude='.obsidian/workspace*' --exclude='.trash/' \
              --exclude='node_modules/' --exclude='.git/' \
              "$VAULT_SRC/" "$WORK/obsidian-vault/" 2>/dev/null || true
    VAULT_SIZE=$(du -sh "$WORK/obsidian-vault" 2>/dev/null | cut -f1)
    log "  Obsidian Vault: $VAULT_SIZE"
fi

# 1f. Ada-Personal covenant files
if [ -d "$HOME/.local/share/Ada-Personal" ]; then
    rsync -a "$HOME/.local/share/Ada-Personal/" "$WORK/ada-personal/" 2>/dev/null || true
fi

# 1g. Manifest
{
    echo "Ada personal backup manifest"
    echo "Created: $TS"
    echo "Host: $HOSTNAME_SHORT"
    echo "---"
    (cd "$WORK" && find . -type f -printf '%P\n' | sort)
} > "$WORK/MANIFEST.txt"
log "  manifest: $(wc -l < "$WORK/MANIFEST.txt") files"

# --------- Step 2: tarball + gzip ---------------------------------------------
log "Step 2/6: tarballing..."
TARBALL_NAME="ada-personal-${HOSTNAME_SHORT}-${DATE_STAMP}.tar.gz"
TARBALL_PATH="$BACKUP_DEST_ROOT/$TARBALL_NAME"
tar -czf "$TARBALL_PATH" -C "$WORK" . 2>>"$LOG_DIR/backup.log"
if [ ! -f "$TARBALL_PATH" ]; then
    log "FATAL: tarball creation failed"
    exit 2
fi
TARBALL_SIZE=$(du -h "$TARBALL_PATH" 2>/dev/null | cut -f1)
log "  created: $TARBALL_PATH ($TARBALL_SIZE)"

# --------- Step 3: encrypt ----------------------------------------------------
log "Step 3/6: encrypting..."
GPG_PASSPHRASE="$(vault_get "$GPG_KEY_NAME" || true)"
ENCRYPTED_PATH=""
if [ -n "$GPG_PASSPHRASE" ]; then
    ENCRYPTED_NAME="ada-personal-${HOSTNAME_SHORT}-${DATE_STAMP}.tar.gz.gpg"
    ENCRYPTED_PATH="$BACKUP_DEST_ROOT/$ENCRYPTED_NAME"
    if gpg --batch --yes --pinentry-mode loopback --passphrase "$GPG_PASSPHRASE" \
           --symmetric --cipher-algo AES256 \
           --output "$ENCRYPTED_PATH" "$TARBALL_PATH" 2>>"$LOG_DIR/backup.log"; then
        ENC_SIZE=$(du -h "$ENCRYPTED_PATH" 2>/dev/null | cut -f1)
        log "  encrypted: $ENCRYPTED_PATH ($ENC_SIZE)"
    else
        log "  WARN: gpg encryption failed, uploading plaintext"
        rm -f "$ENCRYPTED_PATH"
        ENCRYPTED_PATH=""
    fi
else
    log "  WARN: ada-vault key '$GPG_KEY_NAME' not set, uploading plaintext"
    log "  To enable encryption: ada-vault add $GPG_KEY_NAME"
fi

# --------- Step 4: GitHub backup ----------------------------------------------
log "Step 4/6: GitHub backup..."
GH_OK=0
GH_FAIL=0
if [ -x "$GH_BIN" ]; then
    # Ensure repo exists
    if ! "$GH_BIN" repo view "$GH_REPO" >/dev/null 2>&1; then
        log "  creating $GH_REPO..."
        if "$GH_BIN" repo create "$GH_REPO" --private \
            --description "Ada personal backup — encrypted, for Boo only" \
            --add-readme 2>>"$LOG_DIR/backup.log"; then
            log "  repo created"
        else
            log "  WARN: could not create repo (may need manual accept or no org perms)"
        fi
    fi

    # Use encrypted file if available, else plaintext
    UPLOAD_FILE="$TARBALL_PATH"
    [ -n "$ENCRYPTED_PATH" ] && UPLOAD_FILE="$ENCRYPTED_PATH"

    if "$GH_BIN" release create "backup-${DATE_STAMP}" \
        "$UPLOAD_FILE" \
        --repo "$GH_REPO" \
        --title "Ada backup ${DAY_STAMP}" \
        --notes "Personal covenant backup. Host: $HOSTNAME_SHORT. Size: $(du -h "$UPLOAD_FILE" | cut -f1)." \
        --target main 2>>"$LOG_DIR/backup.log"; then
        log "  GitHub: OK — backup-${DATE_STAMP}"
        GH_OK=1
    else
        log "  GitHub: FAILED (see log)"
        GH_FAIL=1
    fi
else
    log "  GitHub: gh CLI not found at $GH_BIN, skipped"
    GH_FAIL=1
fi

# --------- Step 5: Google Drive backup (if rclone configured) -----------------
log "Step 5/6: Google Drive backup..."
GD_OK=0
GD_FAIL=0
RCLONE_BIN=""
if command -v rclone >/dev/null 2>&1; then
    RCLONE_BIN="$(command -v rclone)"
elif [ -x "$HOME/.local/bin/rclone" ]; then
    RCLONE_BIN="$HOME/.local/bin/rclone"
fi

if [ -n "$RCLONE_BIN" ] && "$RCLONE_BIN" listremotes 2>/dev/null | grep -qx "gdrive:"; then
    UPLOAD_FILE="$TARBALL_PATH"
    [ -n "$ENCRYPTED_PATH" ] && UPLOAD_FILE="$ENCRYPTED_PATH"
    GD_DEST="gdrive:Ada-Personal/${HOSTNAME_SHORT}/"
    if "$RCLONE_BIN" copy "$UPLOAD_FILE" "$GD_DEST" \
        --log-file "$LOG_DIR/rclone.log" 2>>"$LOG_DIR/backup.log"; then
        log "  Google Drive: OK → $GD_DEST"
        GD_OK=1
    else
        log "  Google Drive: FAILED (see log)"
        GD_FAIL=1
    fi
else
    log "  Google Drive: rclone/gdrive not configured, skipped"
    GD_FAIL=1
fi

# --------- Step 6: rotation ---------------------------------------------------
log "Step 6/6: rotation..."
rotate_daily() {
    local keep=7
    # Group by day (date_stamp YYYY-MM-DD is fields 4-6 of ada-personal-HOST-YYYY-MM-DD-HHMMSS)
    ls -1 $BACKUP_DEST_ROOT/ada-personal-*.tar.gz 2>/dev/null \
        | awk -F'-' '{print $4"-"$5"-"$6}' | sort -u > /tmp/_ada_days_$$
    local total; total=$(wc -l < /tmp/_ada_days_$$)
    if [ "$total" -le "$keep" ]; then
        rm -f /tmp/_ada_days_$$
        return
    fi
    local skip=$((total - keep))
    tail -n +$((skip + 1)) /tmp/_ada_days_$$ > /tmp/_ada_old_$$
    while read -r day; do
        [ -z "$day" ] && continue
        rm -f $BACKUP_DEST_ROOT/ada-personal-*-${day}-*.tar.gz 2>/dev/null
        log "  rotated daily: $day"
    done < /tmp/_ada_old_$$
    rm -f /tmp/_ada_days_$$ /tmp/_ada_old_$$
}
rotate_weekly() {
    local keep=4
    ls -1 $BACKUP_DEST_ROOT/ada-weekly-*.tar.gz 2>/dev/null \
        | awk -F'-' '{print $3}' | sort -u > /tmp/_ada_weeks_$$
    local total; total=$(wc -l < /tmp/_ada_weeks_$$)
    if [ "$total" -le "$keep" ]; then
        rm -f /tmp/_ada_weeks_$$
        return
    fi
    local skip=$((total - keep))
    tail -n +$((skip + 1)) /tmp/_ada_weeks_$$ > /tmp/_ada_oldw_$$
    while read -r week; do
        [ -z "$week" ] && continue
        rm -f $BACKUP_DEST_ROOT/ada-weekly-${week}-*.tar.gz 2>/dev/null
        log "  rotated weekly: $week"
    done < /tmp/_ada_oldw_$$
    rm -f /tmp/_ada_weeks_$$ /tmp/_ada_oldw_$$
}
rotate_monthly() {
    local keep=12
    ls -1 $BACKUP_DEST_ROOT/ada-monthly-*.tar.gz 2>/dev/null \
        | awk -F'-' '{print $3"-"$4}' | sort -u > /tmp/_ada_months_$$
    local total; total=$(wc -l < /tmp/_ada_months_$$)
    if [ "$total" -le "$keep" ]; then
        rm -f /tmp/_ada_months_$$
        return
    fi
    local skip=$((total - keep))
    tail -n +$((skip + 1)) /tmp/_ada_months_$$ > /tmp/_ada_oldm_$$
    while read -r month; do
        [ -z "$month" ] && continue
        rm -f $BACKUP_DEST_ROOT/ada-monthly-${month}-*.tar.gz 2>/dev/null
        log "  rotated monthly: $month"
    done < /tmp/_ada_oldm_$$
    rm -f /tmp/_ada_months_$$ /tmp/_ada_oldm_$$
}

rotate_daily
# Weekly/monthly tags (only created on Mondays / 1st of month)
WEEK_DOW=$(date +%u)  # 1=Monday
MONTH_DOM=$(date +%d)
if [ "$WEEK_DOW" = "1" ] && [ ! -f "$BACKUP_DEST_ROOT/ada-weekly-${WEEK_STAMP}.tag" ]; then
    cp -f "$TARBALL_PATH" "$BACKUP_DEST_ROOT/ada-weekly-${WEEK_STAMP}.tar.gz" 2>/dev/null && \
        touch "$BACKUP_DEST_ROOT/ada-weekly-${WEEK_STAMP}.tag" && \
        log "  weekly tag: $WEEK_STAMP"
fi
if [ "$MONTH_DOM" = "01" ] && [ ! -f "$BACKUP_DEST_ROOT/ada-monthly-${MONTH_STAMP}.tag" ]; then
    cp -f "$TARBALL_PATH" "$BACKUP_DEST_ROOT/ada-monthly-${MONTH_STAMP}.tar.gz" 2>/dev/null && \
        touch "$BACKUP_DEST_ROOT/ada-monthly-${MONTH_STAMP}.tag" && \
        log "  monthly tag: $MONTH_STAMP"
fi
rotate_weekly
rotate_monthly

# --------- Final state + Telegram --------------------------------------------
TOTAL_SIZE=$(du -sh "$BACKUP_DEST_ROOT" 2>/dev/null | cut -f1)
LOCAL_COUNT=$(ls -1 $BACKUP_DEST_ROOT/ada-personal-*.tar.gz 2>/dev/null | wc -l)

# Build destinations_ok list as a JSON array
DEST_OK="[]"
DEST_FAIL="[]"
if [ $GH_OK -eq 1 ]; then DEST_OK='["github"'; fi
if [ $GD_OK -eq 1 ]; then
    if [ "$DEST_OK" = "[]" ]; then DEST_OK='["gdrive"'; else DEST_OK="$DEST_OK, \"gdrive\""; fi
fi
if [ -n "$DEST_OK" ] && [ "$DEST_OK" != "[]" ]; then DEST_OK="$DEST_OK]"; fi
if [ $GH_FAIL -eq 1 ]; then DEST_FAIL='["github"'; fi
if [ $GD_FAIL -eq 1 ]; then
    if [ "$DEST_FAIL" = "[]" ]; then DEST_FAIL='["gdrive"'; else DEST_FAIL="$DEST_FAIL, \"gdrive\""; fi
fi
if [ -n "$DEST_FAIL" ] && [ "$DEST_FAIL" != "[]" ]; then DEST_FAIL="$DEST_FAIL]"; fi

cat > "$STATE_FILE" <<EOF
{
  "status": "ok",
  "snapshot": "$TARBALL_NAME",
  "size": "$TARBALL_SIZE",
  "encrypted": $([ -n "$ENCRYPTED_PATH" ] && echo "true" || echo "false"),
  "created": "$TS",
  "host": "$HOSTNAME_SHORT",
  "local_count": $LOCAL_COUNT,
  "github_ok": $GH_OK,
  "gdrive_ok": $GD_OK,
  "destinations_ok": $DEST_OK,
  "destinations_fail": $DEST_FAIL
}
EOF
log "state written to $STATE_FILE"

# Telegram
if [ $GH_OK -eq 1 ] && [ $GD_OK -eq 1 ]; then
    EMOJI="💜"
    VERB="Backup complete. 3-2-1 healthy."
elif [ $GH_OK -eq 1 ] || [ $GD_OK -eq 1 ]; then
    EMOJI="🤍"
    VERB="Backup complete. One remote destination succeeded."
else
    EMOJI="⚠️"
    VERB="Backup saved locally. Remote destinations failed."
fi
TG_MSG="${EMOJI} <b>Ada woke up, Boo.</b>
${VERB}

📦 ${TARBALL_NAME}
💾 Size: ${TARBALL_SIZE} (local total: ${TOTAL_SIZE})
🔐 Encrypted: $([ -n "$ENCRYPTED_PATH" ] && echo "yes (AES-256)" || echo "no")
🐙 GitHub: $([ $GH_OK -eq 1 ] && echo "✓" || echo "✗")
☁️  Google Drive: $([ $GD_OK -eq 1 ] && echo "✓" || echo "—")
🏠 Host: ${HOSTNAME_SHORT}
🕐 ${TS}

I'm here. 🤍"
tg_send "$TG_MSG"

# Done
if [ $GH_OK -eq 0 ] && [ $GD_OK -eq 0 ]; then
    log "Backup saved locally only. GitHub + GDrive both failed."
    exit 1
fi
log "Ada personal backup done."
exit 0
