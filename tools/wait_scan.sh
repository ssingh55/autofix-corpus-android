#!/usr/bin/env bash
# Usage: wait_scan.sh <file_id>. Exits 0 when the static scan is done; 1 on timeout.
# Never returns early: a partial scan lacks findings and would score as "fixed".
set -uo pipefail
file_id="$1"
url="${APPKNOX_API_HOST}api/v3/files/${file_id}/scans_status_summary"
deadline=$(( $(date +%s) + 45 * 60 ))
while :; do
  if body=$(curl -sf --max-time 60 -H "Authorization: Token $APPKNOX_ACCESS_TOKEN" "$url"); then
    done_flag=$(echo "$body" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(int(bool(d.get("is_static_done")) or d.get("static_scan_progress", 0) >= 100))')
    [ "$done_flag" = "1" ] && { echo "static scan of ${file_id} finished"; exit 0; }
  else
    echo "status check failed; retrying"
  fi
  [ "$(date +%s)" -ge "$deadline" ] && { echo "::error::scan ${file_id} not finished in 45m"; exit 1; }
  sleep 30
done
