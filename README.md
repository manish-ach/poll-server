# oraclefck

Auto-grab a free-tier **VM.Standard.A1.Flex** (Ampere ARM) instance on Oracle Cloud
when capacity in your home region is chronically *"Out of capacity"*.

A GitHub Actions cron fires every ~5 minutes and tries to launch the instance.
The moment OCI has a free slot, it grabs it, opens a GitHub issue and (optionally)
pings a Discord webhook with the public IP. No server, no cost — it runs on GitHub's
free runners and OCI launch attempts are free API calls.

**What it creates:** an instance named **`mnsh1`** — **2 OCPU / 12 GB RAM**, a
**200 GB boot volume**, running **Ubuntu 24.04 (ARM / aarch64)**. That is half of the
free CPU/RAM allowance (4 OCPU / 24 GB) and all of the free 200 GB block-storage
allowance. You can scale CPU/RAM up to 4/24 later from the console.

Tuned for **single-AD regions like Mumbai (`ap-mumbai-1`)**: one launch attempt per
run (Oracle auto-picks the fault domain) so OCI doesn't rate-limit us, and the cron
simply tries again five minutes later.

---

## Setup (≈10 min, one time)

### 1. Put this folder in a GitHub repo
Create a **private** repo (the secrets below control your tenancy) and push these files.
Scheduled workflows only run from the **default branch**, so push to `main`.

```bash
git init && git add . && git commit -m "oci a1 grabber"
gh repo create oraclefck --private --source . --push   # or create on github.com and push
```

### 2. Get an OCI API key
OCI console → top-right profile → **My profile** → **API keys** → **Add API key** →
**Generate API key pair** → **Download private key** → **Add**.
Do **not** set a passphrase on the key.

A "Configuration file preview" pops up. From it you need:
- `user`        → secret `OCI_CLI_USER`
- `fingerprint` → secret `OCI_CLI_FINGERPRINT`
- `tenancy`     → secret `OCI_CLI_TENANCY`
- `region`      → secret `OCI_CLI_REGION` (e.g. `ap-mumbai-1`)

The downloaded `.pem` file's **full contents** → secret `OCI_CLI_KEY_CONTENT`.

> ⚠️ **Paste the key contents into the GitHub secret only.** Never save the `.pem`
> inside this repo folder — that would push your private key to GitHub. The
> included `.gitignore` blocks common key filenames as a safety net, but don't
> rely on it: keep the key out of the folder entirely.

### 3. Find your subnet
Console → **Networking → Virtual Cloud Networks**. If you have none, click
**Start VCN Wizard → VCN with Internet Connectivity**. Open the VCN → the
**public subnet** → copy its **OCID** → secret `OCI_SUBNET_ID`.

### 4. Your SSH public key
Use an existing one or make one: `ssh-keygen -t ed25519 -f ~/.ssh/oci`.
Copy the contents of the `.pub` file → secret `SSH_PUBLIC_KEY`.

### 5. Add the secrets to GitHub
Repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret                | Value                                            |
|-----------------------|--------------------------------------------------|
| `OCI_CLI_USER`        | user OCID                                         |
| `OCI_CLI_TENANCY`     | tenancy OCID                                      |
| `OCI_CLI_FINGERPRINT` | key fingerprint                                   |
| `OCI_CLI_KEY_CONTENT` | full contents of the downloaded private `.pem`    |
| `OCI_CLI_REGION`      | `ap-mumbai-1`                                      |
| `OCI_SUBNET_ID`       | public subnet OCID                                |
| `SSH_PUBLIC_KEY`      | contents of your `.pub` key                       |
| `OCI_COMPARTMENT_ID`  | *(optional)* compartment OCID — defaults to tenancy/root |
| `OCI_IMAGE_ID`        | *(optional)* pin an exact image OCID; otherwise auto-resolved (see below) |
| `DISCORD_WEBHOOK`     | *(optional)* Discord webhook URL — pings the channel on success  |

### 5b. (Optional) Discord ping on success
In Discord: **Server Settings → Integrations → Webhooks → New Webhook**, pick the
channel, **Copy Webhook URL**. Add it as secret `DISCORD_WEBHOOK`. When the instance
lands you'll get a message in that channel with the IP. If you skip this secret, the
step is silently skipped and you still get the GitHub issue/email.

### 6. Test it, then let it run
Repo → **Actions** → enable workflows if prompted → **Grab OCI A1 free instance** →
**Run workflow** (the `workflow_dispatch` button). Check the log:
- `Out of capacity ... trying next` → auth works, just waiting for a slot. 
- A red non-capacity error → fix that secret/value (the message says what's wrong).

After a successful manual run, the 5-minute cron takes over automatically. When it
lands the instance you'll get a **new GitHub issue** (GitHub emails you). The public IP
goes to your Discord webhook (if set) and is always visible in the OCI console under
**Compute → Instances → mnsh1**.

---

## After you get it
- The script is idempotent: once `mnsh1` exists, every later run is a no-op, so
  **no duplicates** are created. Still, go to **Actions → this workflow → ⋯ → Disable
  workflow** to stop the cron.
- SSH in: `ssh -i ~/.ssh/oci ubuntu@<public-ip>` (user is `opc` for Oracle Linux images).
- The instance launches as **2 OCPU / 12 GB / 200 GB boot** (`mnsh1`). Want the full
  CPU/RAM allowance? Edit the instance later to **4 OCPU / 24 GB**, or set repo
  Variables `OCI_OCPUS` / `OCI_MEMORY_GB` before it launches. Free A1 limit is
  4 OCPU + 24 GB total across all your A1 VMs. Free block storage is **200 GB total**
  (boot volumes included), and the 200 GB boot volume already uses all of it — don't
  attach extra volumes or a second A1 VM's boot disk would be billable.

## Which image you get
By default the script grabs the newest **Canonical Ubuntu 24.04 Minimal aarch64 (ARM)**
image — it filters the A1 image list (which is already ARM-only) by the display-name
regex in `OCI_IMAGE_NAME_FILTER` (default `Minimal`). To get the *standard* (non-Minimal)
build instead, set that Variable to empty. To use a different release, set `OCI_OS_VERSION`
(e.g. `22.04`). SSH user for Ubuntu images is `ubuntu`.

**Want to pin one exact image?** Set the `OCI_IMAGE_ID` secret to a specific OCID — this
overrides the lookup entirely. Get the OCID with the CLI:
```bash
oci compute image list --compartment-id <tenancy-ocid> \
  --operating-system "Canonical Ubuntu" --operating-system-version "24.04" \
  --shape VM.Standard.A1.Flex --sort-by TIMECREATED --sort-order DESC \
  | jq -r '.data[] | select(."display-name" | test("Minimal")) | "\(.["display-name"])  \(.id)"'
```
or open the image on the OCI console's **Compute → Images** (or the instance-create image
picker) and copy its OCID.

## Tuning (optional repo Variables)
Settings → Secrets and variables → Actions → **Variables**:
`OCI_OCPUS` (2), `OCI_MEMORY_GB` (12), `OCI_DISPLAY_NAME` (mnsh1),
`OCI_BOOT_VOLUME_GB` (200), `OCI_OS` (Canonical Ubuntu), `OCI_OS_VERSION` (24.04),
`OCI_IMAGE_NAME_FILTER` (Minimal).

## Notes & gotchas
- GitHub **disables scheduled workflows after 60 days** with no repo commits — push
  something occasionally, or re-enable from the Actions tab.
- Cron runs can be **delayed during peak load**; that's fine for catching capacity.
- **Security:** anyone with these secrets controls your tenancy. Keep the repo private.
  For least privilege, create a dedicated IAM user + group + a policy that only allows
  `manage instance-family` / `use` on networking in your compartment, and use that
  user's API key here.
- Free-tier only ever places in your **home region** — there's no point switching
  regions; the small-shape + retry approach is the lever.
