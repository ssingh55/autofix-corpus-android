#!/usr/bin/env bash
# Force v1 (JAR) signing onto the `full` flavor's release APK.
#
# AGP silently drops v1 signing when minSdk >= 24, see
# issuetracker.google.com/issues/134858541. The `full` flavor has minSdk 24,
# so its raw AGP output has no v1 signature and scanner id 117 (Janus) would
# never fire. This re-signs the APK in place with the same auto-generated
# debug keystore AGP already used, adding the missing v1 signature block.
#
# Usage: force-v1.sh <path-to-apk>
set -euo pipefail

apk="$1"

apksigner=$(ls "$ANDROID_HOME"/build-tools/*/apksigner | sort -V | tail -1)

# AGP already signed this APK (v2) with the auto-generated debug keystore. Its
# location varies by runner image (e.g. ~/.android/ vs XDG ~/.config/.android/),
# so find it rather than hardcoding a path. Re-signing with the same keystore
# keeps the same signer identity and simply adds the v1 (JAR) signature block that
# enableV1Signing = true failed to produce because minSdk (24) is >= 24.
# `|| true` on the find|head pipeline: under set -o pipefail, find hitting an
# unreadable directory (nonzero exit) must not abort the script here — the
# empty-keystore check below is the intended, clear failure mode instead.
keystore=$(find "$HOME" -maxdepth 4 -name debug.keystore 2>/dev/null | head -1 || true)
if [ -z "$keystore" ]; then
  echo "debug.keystore not found under $HOME" >&2
  exit 1
fi

# --min-sdk-version overrides apksigner's own inference from the APK's manifest
# (minSdk 24), which otherwise silently overrides --v1-signing-enabled too.
"$apksigner" sign --ks "$keystore" --ks-pass pass:android \
  --key-pass pass:android --ks-key-alias androiddebugkey \
  --min-sdk-version 1 \
  --v1-signing-enabled true --v2-signing-enabled true \
  "$apk"

# --min-sdk-version 1: without it, verify also infers minSdk 24 from the manifest
# and skips checking the v1 (JAR) signature block entirely, always reporting false.
"$apksigner" verify --verbose --min-sdk-version 1 "$apk" | \
  grep -q "Verified using v1 scheme (JAR signing): true"
