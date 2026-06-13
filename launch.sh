#!/usr/bin/env bash
#
# Attempts to launch a free-tier VM.Standard.A1.Flex instance on Oracle Cloud.
# Designed to be run repeatedly (e.g. from a GitHub Actions cron) until OCI has
# spare A1 capacity. Safe to re-run: if the instance already exists it does
# nothing, so it never creates duplicates.
#
# Auth is taken from OCI_CLI_* environment variables (set as GitHub secrets).
set -euo pipefail

# ----- config (env vars, with sensible defaults) ---------------------------
COMPARTMENT_ID="${OCI_COMPARTMENT_ID:-$OCI_CLI_TENANCY}"   # default: root compartment
SUBNET_ID="${OCI_SUBNET_ID:?set OCI_SUBNET_ID}"
SHAPE="${OCI_SHAPE:-VM.Standard.A1.Flex}"
OCPUS="${OCI_OCPUS:-1}"                                    # small slice = easier to place
MEM_GB="${OCI_MEMORY_GB:-6}"
DISPLAY_NAME="${OCI_DISPLAY_NAME:-free-a1}"
BOOT_GB="${OCI_BOOT_VOLUME_GB:-100}"
OS_NAME="${OCI_OS:-Canonical Ubuntu}"
OS_VERSION="${OCI_OS_VERSION:-24.04}"

# SSH public key -> file (used by --ssh-authorized-keys-file)
SSH_KEY_FILE="$(mktemp)"
printf '%s\n' "${SSH_PUBLIC_KEY:?set SSH_PUBLIC_KEY}" > "$SSH_KEY_FILE"

emit() { [[ -n "${GITHUB_OUTPUT:-}" ]] && echo "$1" >> "$GITHUB_OUTPUT" || true; }
summary() { [[ -n "${GITHUB_STEP_SUMMARY:-}" ]] && echo "$1" >> "$GITHUB_STEP_SUMMARY" || true; }

# ----- guard: already have a (non-terminated) instance with this name? ------
echo "Checking for an existing '$DISPLAY_NAME' instance..."
existing="$(oci compute instance list --compartment-id "$COMPARTMENT_ID" --all 2>/dev/null \
  | jq --arg n "$DISPLAY_NAME" \
      '[.data[] | select(."display-name"==$n and ."lifecycle-state"!="TERMINATED")] | length')"
if [[ "${existing:-0}" -gt 0 ]]; then
  echo "✅ An instance named '$DISPLAY_NAME' already exists — nothing to do."
  emit "created=false"
  exit 0
fi

# ----- resolve image -------------------------------------------------------
if [[ -n "${OCI_IMAGE_ID:-}" ]]; then
  IMAGE_ID="$OCI_IMAGE_ID"
else
  # The --shape filter already restricts results to aarch64 images. The optional
  # OCI_IMAGE_NAME_FILTER (a regex on the display name, e.g. "Minimal") picks the
  # right variant — A1.Flex returns both standard and Minimal Ubuntu builds.
  echo "Looking up latest $OS_NAME $OS_VERSION image for $SHAPE (filter='${OCI_IMAGE_NAME_FILTER:-none}')..."
  IMAGE_ID="$(oci compute image list \
    --compartment-id "$COMPARTMENT_ID" \
    --operating-system "$OS_NAME" \
    --operating-system-version "$OS_VERSION" \
    --shape "$SHAPE" \
    --sort-by TIMECREATED --sort-order DESC \
    | jq -r --arg f "${OCI_IMAGE_NAME_FILTER:-}" \
        '[(.data // [])[] | select($f=="" or (."display-name" | test($f)))][0].id // empty')"
fi
[[ -n "$IMAGE_ID" && "$IMAGE_ID" != "null" ]] || { echo "❌ Could not resolve an image OCID."; exit 1; }
echo "Image: $IMAGE_ID"

# ----- one launch attempt --------------------------------------------------
attempt() {
  local ad="$1" fd="$2"
  local args=(
    compute instance launch
    --availability-domain "$ad"
    --compartment-id "$COMPARTMENT_ID"
    --shape "$SHAPE"
    --shape-config "{\"ocpus\": $OCPUS, \"memoryInGBs\": $MEM_GB}"
    --image-id "$IMAGE_ID"
    --subnet-id "$SUBNET_ID"
    --assign-public-ip true
    --display-name "$DISPLAY_NAME"
    --boot-volume-size-in-gbs "$BOOT_GB"
    --ssh-authorized-keys-file "$SSH_KEY_FILE"
    --wait-for-state RUNNING
  )
  [[ -n "$fd" ]] && args+=( --fault-domain "$fd" )
  oci "${args[@]}" 2>&1
}

# ----- loop over availability domains (ONE auto-fault-domain attempt each) --
# We deliberately do NOT iterate fault domains. OCI rate-limits launch_instance
# (HTTP 429 "Too many requests") if you fire several launches back-to-back, so
# hammering FD-1/2/3 in one run just gets you throttled. One attempt per run +
# the 5-minute cron is what reliably catches a free slot. In single-AD Mumbai
# this is a single launch call per run.
mapfile -t ADS < <(oci iam availability-domain list --compartment-id "$OCI_CLI_TENANCY" | jq -r '.data[].name')
echo "Availability domains: ${ADS[*]}"

for ad in "${ADS[@]}"; do
  echo "── Attempt: AD=$ad FD=<auto> shape=$SHAPE ${OCPUS}ocpu/${MEM_GB}GB"
  set +e
  out="$(attempt "$ad" "")"
  rc=$?
  set -e

  if [[ $rc -eq 0 ]]; then
    iid="$(echo "$out" | jq -r '.data.id' 2>/dev/null || true)"
    ip="$(oci compute instance list-vnics --instance-id "$iid" --query 'data[0]."public-ip"' --raw-output 2>/dev/null || true)"
    # This repo is PUBLIC → Actions logs and the run summary are world-readable.
    # Keep the IP/OCID OUT of the log and summary; ship them only via step outputs,
    # which the (private) Discord step consumes. Outputs are not printed to the log.
    echo "🎉 SUCCESS — A1 instance is RUNNING (IP/OCID sent to Discord; also in the OCI console)."
    emit "created=true"
    emit "instance_id=$iid"
    emit "public_ip=$ip"
    summary "## 🎉 Got your A1 instance!"
    summary "It's **RUNNING** in AD-1. The public IP was sent to your Discord webhook and is in the OCI console."
    summary "_(IP and OCID are intentionally omitted here — this repo's Actions logs are public.)_"
    exit 0
  fi

  echo "$out"
  if echo "$out" | grep -qiE "out of (host )?capacity"; then
    echo "⏳ Out of capacity in $ad — will retry on the next cron run."
    continue
  fi
  if echo "$out" | grep -qiE "TooManyRequests|too many requests|\"status\":[[:space:]]*429"; then
    echo "🐢 Rate-limited by OCI (429) — backing off; the next cron run will retry."
    emit "created=false"
    exit 0
  fi
  # Anything else (bad auth, quota LimitExceeded, bad OCID) is a real error to fix.
  echo "❌ Non-capacity error — fix this before the next run (see message above)."
  exit 1
done

echo "😴 No capacity anywhere this round. The cron will try again shortly."
emit "created=false"
exit 0
