#!/usr/bin/env python3
"""Build the friend-facing setup guide PDF for the mnsh1 Oracle Cloud grabber.

Usage: python3 make_guide.py <output.pdf>
Uses only reportlab's built-in fonts, so it runs anywhere reportlab is installed.
"""
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    CondPageBreak,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "mnsh1-setup-guide.pdf")

# ---------------------------------------------------------------- palette / geometry
NAVY = colors.HexColor("#1d3557")
RED = colors.HexColor("#c74634")
INK = colors.HexColor("#1f2933")
MUTED = colors.HexColor("#6b7280")
LINE = colors.HexColor("#d9dee5")
CODE_BG = colors.HexColor("#f3f4f6")
TIP_BG = colors.HexColor("#e9f1fb")
WARN_BG = colors.HexColor("#fdf1e7")
HEAD_BG = colors.HexColor("#eef2f7")
ZEBRA = colors.HexColor("#f8fafc")

PAGE_W, PAGE_H = A4
M = 18 * mm
AVAIL = PAGE_W - 2 * M

# ---------------------------------------------------------------- styles
body = ParagraphStyle("body", fontName="Helvetica", fontSize=10.5, leading=15,
                      textColor=INK, spaceAfter=6)
small = ParagraphStyle("small", parent=body, fontSize=9, leading=12.5, textColor=MUTED)
cell = ParagraphStyle("cell", parent=body, fontSize=9.3, leading=12.5, spaceAfter=0)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Helvetica-Bold")
li = ParagraphStyle("li", parent=cell, fontSize=10, leading=14, spaceAfter=2)
h1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=19, leading=24,
                    textColor=NAVY, spaceBefore=4, spaceAfter=8, keepWithNext=1)
h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=12.5, leading=16,
                    textColor=NAVY, spaceBefore=10, spaceAfter=4, keepWithNext=1)
title = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=26, leading=31,
                       textColor=NAVY, spaceAfter=6)
subtitle = ParagraphStyle("subtitle", fontName="Helvetica", fontSize=12.5, leading=18,
                          textColor=MUTED, spaceAfter=10)
kicker = ParagraphStyle("kicker", fontName="Helvetica-Bold", fontSize=9.5, leading=12,
                        textColor=RED, spaceAfter=6)
code = ParagraphStyle("code", fontName="Courier", fontSize=8.7, leading=11.6, textColor=INK)


# ---------------------------------------------------------------- helpers
def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def C(s: str) -> str:
    """Inline code inside a Paragraph."""
    return f'<font face="Courier">{esc(s)}</font>'


def nav(*parts: str) -> str:
    """Console navigation path, bold with > separators. Parts are escaped."""
    return "<b>" + " &gt; ".join(esc(p) for p in parts) + "</b>"


def P(text: str, st: ParagraphStyle = body):
    return Paragraph(text, st)


def Code(text: str):
    pre = Preformatted(text.strip("\n"), code, maxLineLength=90)
    t = Table([[pre]], colWidths=[AVAIL])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return [t, Spacer(1, 7)]


def Note(text: str, kind: str = "tip"):
    bg, bar, label = (TIP_BG, NAVY, "Tip") if kind == "tip" else (WARN_BG, RED, "Careful")
    t = Table([[Paragraph(f"<b>{label}:</b> {text}", cell)]], colWidths=[AVAIL])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 3, bar),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return [t, Spacer(1, 8)]


def Bullets(items):
    return [ListFlowable(
        [ListItem(P(i, li), leftIndent=14) for i in items],
        bulletType="bullet", start="•", leftIndent=14, bulletFontSize=9,
        bulletColor=NAVY,
    ), Spacer(1, 4)]


def Steps(items, start=1):
    return [ListFlowable(
        [ListItem(P(i, li), leftIndent=18) for i in items],
        start=start,
        bulletType="1", bulletFormat="%s.", leftIndent=18, bulletFontName="Helvetica-Bold",
        bulletFontSize=9.5, bulletColor=NAVY,
    ), Spacer(1, 4)]


def _pad(st, n=5):
    st += [
        ("LEFTPADDING", (0, 0), (-1, -1), n),
        ("RIGHTPADDING", (0, 0), (-1, -1), n),
        ("TOPPADDING", (0, 0), (-1, -1), n),
        ("BOTTOMPADDING", (0, 0), (-1, -1), n),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    return st


def Tbl(header, rows, widths):
    data = [[Paragraph(h, cellb) for h in header]]
    for r in rows:
        data.append([Paragraph(c, cell) if isinstance(c, str) else c for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    st = [
        ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, NAVY),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, LINE),
    ]
    for i in range(2, len(data), 2):
        st.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
    t.setStyle(TableStyle(_pad(st)))
    return [t, Spacer(1, 8)]


def KV(rows, widths):
    data = [[Paragraph(k, cellb), Paragraph(v, cell)] for k, v in rows]
    t = Table(data, colWidths=widths)
    st = [
        ("BACKGROUND", (0, 0), (0, -1), HEAD_BG),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
    ]
    t.setStyle(TableStyle(_pad(st, 4)))
    return [t, Spacer(1, 8)]


def on_page(canv, doc):
    canv.saveState()
    canv.setFont("Helvetica", 8)
    canv.setFillColor(MUTED)
    canv.drawString(M, PAGE_H - 12 * mm,
                    "mnsh1  ·  Oracle Cloud free ARM server  ·  setup guide")
    canv.drawRightString(PAGE_W - M, 11 * mm, f"Page {doc.page}")
    canv.setStrokeColor(LINE)
    canv.setLineWidth(0.5)
    canv.line(M, PAGE_H - 14 * mm, PAGE_W - M, PAGE_H - 14 * mm)
    canv.restoreState()


# ---------------------------------------------------------------- content
S = []

# ---- cover ----------------------------------------------------------------
S += [
    P("SETUP GUIDE", kicker),
    P("Getting mnsh1 up on Oracle Cloud", title),
    P("A free 2-core / 12 GB ARM server, grabbed automatically by GitHub Actions. "
      "This guide walks you through the GitHub secrets, the Oracle terminal and the "
      "login username, step by step.", subtitle),
    P("Oracle's Always Free tier includes an Ampere ARM virtual machine, but in busy "
      "regions the console just says <i>Out of capacity</i> every time you click "
      "Create. The repo you've been given fixes that: a GitHub Actions job retries the "
      "launch every five minutes, and the moment a slot opens it creates the instance "
      "for you. Your part is a one-time setup of roughly 15 minutes. After that, you wait."),
    P("What you'll end up with", h2),
]
S += KV([
    ("Name", "mnsh1"),
    ("Shape", "VM.Standard.A1.Flex (Ampere ARM, aarch64)"),
    ("CPU", "2 OCPU"),
    ("Memory", "12 GB"),
    ("Storage", "200 GB boot volume"),
    ("OS", "Ubuntu 24.04 Minimal, ARM build"),
    ("Login", "user <b>ubuntu</b>, SSH key only: " + C("ssh -i ~/.ssh/oci ubuntu@<ip>")),
    ("Cost", "$0. Stays inside the Always Free limits (4 OCPU / 24 GB / 200 GB storage)."),
], [32 * mm, AVAIL - 32 * mm])

S += [P("Before you start, you need", h2)]
S += Bullets([
    "An <b>Oracle Cloud account</b> (cloud.oracle.com). Sign-up asks for a card for "
    "identity verification; nothing in this guide is billed.",
    "A <b>GitHub account</b>.",
    "A <b>terminal</b> on your computer: Terminal on macOS, any shell on Linux, or "
    "PowerShell on Windows 10/11. All of them ship with " + C("ssh") + " and "
    + C("ssh-keygen") + ".",
    "About 15 minutes, and a scratch text file to paste values into as you go "
    "(outside the repo folder).",
])

S += [P("The plan", h2)]
S += Steps([
    "<b>Collect your Oracle identity</b>: username, user OCID, tenancy OCID, region.",
    "<b>Create an API key</b>. This is how GitHub logs in to Oracle as you.",
    "<b>Open the Oracle terminal</b> (Cloud Shell) and look up your subnet.",
    "<b>Make an SSH key</b> on your computer.",
    "<b>Put the repo on GitHub</b> as a private repo.",
    "<b>Add the seven GitHub secrets</b>.",
    "<b>Run the workflow once</b> and read the log.",
    "<b>Wait.</b> When mnsh1 lands, log in as <b>ubuntu</b>.",
])
S += [PageBreak()]

# ---- 1. identity ----------------------------------------------------------
S += [
    P("1. Your Oracle identity: username and OCIDs", h1),
    P("Everything in Oracle Cloud is identified by an <b>OCID</b>, a long string starting "
      "with " + C("ocid1.") + ". You need two of them (your user and your tenancy), plus "
      "your region. Oracle calls these things by slightly different names in different "
      "places, so here is exactly where each one lives."),
]
S += Steps([
    "Sign in at <b>cloud.oracle.com</b>. The first screen asks for your <b>Cloud Account "
    "Name</b> (the tenancy name you chose at sign-up), then your <b>username</b> and "
    "password. Your username is normally the email you signed up with.",
    "<b>Region.</b> The top bar shows the current region, e.g. <i>India West (Mumbai)</i>. "
    "Free-tier VMs can only be created in your <b>home region</b>, so leave it as it is. "
    "The identifier you'll need looks like " + C("ap-mumbai-1") + "; it appears in the "
    "API-key preview in section 2, so there is no need to hunt for it now.",
    "<b>User OCID.</b> Click the profile icon (top right) " + nav("My profile") + ". "
    "The page shows your username and, under it, <b>OCID</b> with a <i>Copy</i> link. "
    "Paste it next to " + C("OCI_CLI_USER") + " in your scratch file.",
    "<b>Tenancy OCID.</b> Profile icon " + nav("Tenancy: <your name>") + ". Copy its "
    "<b>OCID</b> next to " + C("OCI_CLI_TENANCY") + ".",
])
S += Tbl(
    ["What the console calls it", "What it is", "Secret name"],
    [
        ["Cloud Account Name / Tenancy name", "The account itself. Used only to sign in.",
         "not a secret"],
        ["Username", "Who you are, usually your email. Used only to sign in.",
         "not a secret"],
        ["User OCID", "Machine ID of your user", C("OCI_CLI_USER")],
        ["Tenancy OCID", "Machine ID of the account", C("OCI_CLI_TENANCY")],
        ["Region identifier", "Where the VM lives, e.g. " + C("ap-mumbai-1"),
         C("OCI_CLI_REGION")],
    ],
    [50 * mm, AVAIL - 50 * mm - 42 * mm, 42 * mm],
)
S += Note("OCIDs are identifiers, not passwords. The only true secret in this whole "
          "setup is the private key file from section 2.")

# ---- 2. API key ------------------------------------------------------------
S += [
    P("2. Create an API key", h1),
    P("The GitHub job talks to Oracle through the OCI API. Instead of your password it "
      "uses an <b>API signing key</b>: a private key that lives in a GitHub secret, and "
      "a matching public key registered on your Oracle user."),
]
S += Steps([
    "Profile icon " + nav("My profile") + ". Find <b>API keys</b>. In the newer console "
    "layout it sits under the <b>Tokens and keys</b> tab; in the older one it is in the "
    "<b>Resources</b> list on the left.",
    "Click " + nav("Add API key") + " and choose <b>Generate API key pair</b>.",
    "Click <b>Download private key</b>. A file ending in " + C(".pem") + " lands in your "
    "Downloads. Do <b>not</b> set a passphrase. (You may also download the public key; "
    "you won't need it.)",
    "Click <b>Add</b>. A <b>Configuration file preview</b> appears. It looks like this:",
])
S += Code("""
[DEFAULT]
user=ocid1.user.oc1..aaaaaaaa...
fingerprint=3f:1a:9c:...:e2
tenancy=ocid1.tenancy.oc1..aaaaaaaa...
region=ap-mumbai-1
key_file=<path to your private keyfile> # TODO
""")
S += Steps([
    "Copy the four values " + C("user") + ", " + C("fingerprint") + ", " + C("tenancy")
    + " and " + C("region") + " into your scratch file. They become "
    + C("OCI_CLI_USER") + ", " + C("OCI_CLI_FINGERPRINT") + ", " + C("OCI_CLI_TENANCY")
    + " and " + C("OCI_CLI_REGION") + ".",
    "Open the downloaded " + C(".pem") + " in a <b>plain-text</b> editor (TextEdit in "
    "plain-text mode, Notepad, VS Code). The whole file, from "
    + C("-----BEGIN PRIVATE KEY-----") + " to " + C("-----END PRIVATE KEY-----")
    + " inclusive, becomes " + C("OCI_CLI_KEY_CONTENT") + ".",
], start=5)
S += Note("Never copy the " + C(".pem") + " into the repo folder, and never commit it. "
          "Anyone holding that file plus your OCIDs controls your entire Oracle account. "
          "It goes into a GitHub secret and nowhere else. Once mnsh1 is up and the "
          "workflow is disabled, you can delete the API key under "
          + nav("My profile", "API keys") + " to revoke it.", "warn")
S += Note("A user can have up to three API keys. If you lose the " + C(".pem")
          + ", delete that key, generate a new one, and update the fingerprint and "
          "key-content secrets.")
S += [CondPageBreak(80 * mm)]

# ---- 3. Cloud Shell --------------------------------------------------------
S += [
    P("3. The Oracle terminal (Cloud Shell)", h1),
    P("Oracle's console has a built-in terminal called <b>Cloud Shell</b>. It is a small "
      "Linux box in your browser with the " + C("oci") + " command-line tool "
      "pre-installed and <b>already logged in as you</b>, so there is nothing to "
      "configure. It is the quickest way to look up OCIDs without clicking around, and "
      "to sanity-check things later."),
]
S += Steps([
    "In the console, click the <b>Developer tools</b> icon in the top bar (the "
    + C(">_") + " terminal symbol, near the search bar and region name) "
    + nav("Cloud Shell") + ". The first launch takes 30&ndash;60 seconds.",
    "Cloud Shell already knows who you are. Print it and compare with sections 1&ndash;2:",
])
S += Code("""
echo "user:    $OCI_CS_USER_OCID"
echo "tenancy: $OCI_TENANCY"
echo "region:  $OCI_REGION"
""")
S += [P("If a variable prints empty, just use the values you copied from the console.",
        small)]
S += Steps([
    "Confirm the CLI works and see your availability domain(s). Mumbai shows a single "
    "one; that is expected.",
], start=3)
S += Code("""
oci iam availability-domain list --compartment-id "$OCI_TENANCY" \\
  --query 'data[].name' --output table
""")

S += [P("Find (or create) your network and copy the subnet OCID", h2),
      P("The instance has to be placed in a subnet of a <b>Virtual Cloud Network</b> "
        "(VCN). New accounts usually have none.")]
S += Steps([
    "Console menu (the three lines, top left) " + nav("Networking", "Virtual cloud networks")
    + ". If the list is empty: " + nav("Start VCN Wizard", "Create VCN with Internet Connectivity",
    "Start VCN Wizard") + ", give it a name such as " + C("mnsh-vcn") + ", keep the "
    "defaults, " + nav("Next", "Create") + ". It takes about a minute.",
    "Back in Cloud Shell, list the subnets and pick the <b>public</b> one:",
])
S += Code("""
oci network subnet list --compartment-id "$OCI_TENANCY" --output table \\
  --query 'data[].{name:"display-name", noPublicIp:"prohibit-public-ip-on-vnic", id:id}'
""")
S += [P("The row whose " + C("noPublicIp") + " column says " + C("false") + " is the "
        "public subnet. Its " + C("id") + " (" + C("ocid1.subnet.oc1...") + ") is "
        + C("OCI_SUBNET_ID") + ". Through the console instead: "
        + nav("open the VCN", "the subnet named public subnet-...", "OCID", "Copy") + ".")]
S += Steps([
    "Optional: see the Ubuntu ARM images the workflow chooses from. You don't need to "
    "set anything; it picks the newest one whose name contains <i>Minimal</i>. Only if "
    "you want to pin one exact image do you put its id in the optional "
    + C("OCI_IMAGE_ID") + " secret.",
], start=3)
S += Code("""
oci compute image list --compartment-id "$OCI_TENANCY" \\
  --operating-system "Canonical Ubuntu" --operating-system-version "24.04" \\
  --shape VM.Standard.A1.Flex --sort-by TIMECREATED --sort-order DESC \\
  --query 'data[].{name:"display-name", id:id}' --output table
""")
S += Note("Cloud Shell's home directory persists between sessions, but the session "
          "itself times out after about 20 idle minutes. Just reopen it.")

S += [P("Optional: the OCI CLI on your own computer", h2),
      P("Not required for this guide, but handy if you'd rather not use the browser "
        "terminal:")]
S += Code("""
# macOS
brew install oci-cli
# Linux / Windows (needs Python 3)
pip install oci-cli

oci setup config   # asks for user OCID, tenancy OCID, region; can generate the key
""")
S += [P(C("oci setup config") + " writes " + C("~/.oci/config") + " with the same "
        "user / fingerprint / tenancy / region values the GitHub secrets use, plus "
        + C("~/.oci/oci_api_key.pem") + ". If you let it generate a new key, upload the "
        "matching " + C("oci_api_key_public.pem") + " under "
        + nav("My profile", "API keys", "Add API key", "Paste a public key")
        + ", otherwise Oracle will not accept that key.")]
S += [CondPageBreak(80 * mm)]

# ---- 4. SSH key -------------------------------------------------------------
S += [
    P("4. An SSH key for logging in", h1),
    P("This is how <b>you</b> will log in to mnsh1. The public half goes to Oracle "
      "(through a GitHub secret) and is baked into the server when it is created; the "
      "private half never leaves your computer."),
]
S += Code("""
# macOS / Linux (Terminal) -- Windows 10/11 (PowerShell) is the same command
ssh-keygen -t ed25519 -f ~/.ssh/oci -C "mnsh1"
# press Enter twice for no passphrase (or set one; you'll type it at every login)

cat ~/.ssh/oci.pub            # Windows: Get-Content $HOME\\.ssh\\oci.pub
""")
S += [P("The output is a single line starting with " + C("ssh-ed25519 AAAA")
        + " and ending with " + C("mnsh1") + ". That whole line is "
        + C("SSH_PUBLIC_KEY") + ".")]
S += Note("Two different keys, two different jobs. The Oracle API key (" + C(".pem")
          + ") authenticates <b>GitHub to Oracle's API</b>. The SSH key ("
          + C("~/.ssh/oci") + ") authenticates <b>you to the server</b>. "
          + C("OCI_CLI_KEY_CONTENT") + " gets the " + C(".pem") + "; "
          + C("SSH_PUBLIC_KEY") + " gets the " + C(".pub") + " line.", "warn")
S += Note("Want a second person to be able to log in too? Put their public key on a "
          "second line of the " + C("SSH_PUBLIC_KEY") + " secret. One key per line.")
S += [P("Windows: if PowerShell says " + C("ssh-keygen") + " is not recognised, add it via "
        + nav("Settings", "Apps", "Optional features", "Add a feature", "OpenSSH Client")
        + ".", small)]

# ---- 5. GitHub repo ---------------------------------------------------------
S += [
    P("5. Put the repo on GitHub (private)", h1),
    P("Scheduled workflows only run from the default branch of a repo <b>you</b> own on "
      "GitHub, so you need your own copy. Make it <b>private</b>: the secrets themselves "
      "are never exposed either way, but a private repo keeps the run history, the "
      "success issue and any slip-ups out of public view."),
]
S += Steps([
    "On github.com click <b>+</b> (top right) " + nav("New repository") + ". Name: "
    + C("oraclefck") + " (anything works). Visibility: <b>Private</b>. Do <b>not</b> tick "
    "<i>Add a README</i>. Click <b>Create repository</b>.",
    "Get the files onto your computer and push them to your new repo:",
])
S += Code("""
git clone https://github.com/manish-ach/plzStopSpamming.git oraclefck
cd oraclefck
git remote set-url origin https://github.com/<your-github-username>/oraclefck.git
git push -u origin main

# or, with the GitHub CLI, create-and-push in one go:
gh repo create oraclefck --private --source . --push
""")
S += Steps([
    "Check on GitHub that you can see four things: " + C("README.md") + ", "
    + C("launch.sh") + ", " + C(".gitignore") + " and "
    + C(".github/workflows/retry.yml") + ". If the " + C(".github") + " folder is "
    "missing, the workflow doesn't exist. Use git rather than the web drag-and-drop "
    "uploader, which skips hidden dot-folders.",
], start=3)
S += Note("Secrets are per-repository. Even if the person who sent you this added you as "
          "a collaborator on their repo, use your own copy with your own Oracle values.")
S += [CondPageBreak(80 * mm)]

# ---- 6. secrets --------------------------------------------------------------
S += [
    P("6. Add the GitHub secrets", h1),
    P("In your repo: " + nav("Settings", "Secrets and variables", "Actions")
      + " (the <i>Settings</i> tab is on the repo's top bar; <i>Secrets and variables</i> "
      "sits under <i>Security</i> in the left sidebar). Under <b>Repository secrets</b> "
      "click <b>New repository secret</b>, type the <b>Name</b> exactly as in the table, "
      "paste the <b>Secret</b>, click <b>Add secret</b>. Repeat for each row."),
]
S += Tbl(
    ["Secret name", "What to paste", "Where it came from"],
    [
        [C("OCI_CLI_USER"), "User OCID, " + C("ocid1.user.oc1..") + "&hellip;",
         "Section 1, or " + C("user=") + " in the API-key preview"],
        [C("OCI_CLI_TENANCY"), "Tenancy OCID, " + C("ocid1.tenancy.oc1..") + "&hellip;",
         "Section 1, or " + C("tenancy=") + " in the preview"],
        [C("OCI_CLI_FINGERPRINT"), "16 pairs of hex separated by colons, e.g. "
         + C("3f:1a:9c:...:e2"), C("fingerprint=") + " in the preview"],
        [C("OCI_CLI_KEY_CONTENT"), "The <b>entire</b> " + C(".pem") + " file, BEGIN and "
         "END lines included, line breaks intact", "Section 2, step 6"],
        [C("OCI_CLI_REGION"), "Region identifier, e.g. " + C("ap-mumbai-1"),
         C("region=") + " in the preview"],
        [C("OCI_SUBNET_ID"), "Public subnet OCID, " + C("ocid1.subnet.oc1.") + "&hellip;",
         "Section 3"],
        [C("SSH_PUBLIC_KEY"), "The " + C("ssh-ed25519 AAAA...") + " line", "Section 4"],
    ],
    [44 * mm, 74 * mm, AVAIL - 118 * mm],
)
S += [P("Optional secrets", h2)]
S += Tbl(
    ["Secret name", "When you'd set it"],
    [
        [C("DISCORD_WEBHOOK"), "To get the public IP as a Discord message the moment "
         "mnsh1 lands. See below."],
        [C("OCI_COMPARTMENT_ID"), "Only if you created a separate compartment and want "
         "the VM (and the subnet) there. Default is the root compartment, which is fine."],
        [C("OCI_IMAGE_ID"), "Only to pin one exact image OCID (section 3). Normally "
         "leave it unset."],
    ],
    [44 * mm, AVAIL - 44 * mm],
)
S += [P("Common paste mistakes", h2)]
S += Bullets([
    "No quotes around any value.",
    "Secret names are case-sensitive: " + C("OCI_CLI_USER") + ", not "
    + C("oci_cli_user") + ".",
    C("OCI_CLI_REGION") + " is the identifier (" + C("ap-mumbai-1") + "), not the "
    "display name (<i>India West (Mumbai)</i>).",
    "The key content must be multi-line, exactly as in the file. Select-all in the "
    "editor, copy, paste into the secret box. GitHub keeps the line breaks.",
    "GitHub never shows a secret again after saving. If in doubt, open it, click "
    "<b>Update</b>, and paste again.",
])
S += [P("Optional: Discord ping", h2),
      P("In Discord: " + nav("Server Settings", "Integrations", "Webhooks", "New Webhook")
        + ", pick the channel, <b>Copy Webhook URL</b>, and save it as the "
        + C("DISCORD_WEBHOOK") + " secret. When mnsh1 lands you get a message with the IP "
        "and the instance OCID. Without it you still get the GitHub issue and email, and "
        "the IP is in the Oracle console.")]
S += [P("Variables: already set for mnsh1", h2),
      P("The size and name are baked into the workflow defaults: name <b>mnsh1</b>, "
        "<b>2 OCPU</b>, <b>12 GB</b>, <b>200 GB</b> boot volume, Ubuntu 24.04 Minimal ARM. "
        "You do not need to create any Variables. If you ever want different values, use "
        "the <b>Variables</b> tab next to Secrets: " + C("OCI_DISPLAY_NAME") + ", "
        + C("OCI_OCPUS") + ", " + C("OCI_MEMORY_GB") + ", " + C("OCI_BOOT_VOLUME_GB")
        + ", " + C("OCI_OS_VERSION") + ".")]
S += [CondPageBreak(80 * mm)]

# ---- 7. run ------------------------------------------------------------------
S += [P("7. Run it once and read the log", h1)]
S += Steps([
    "Repo " + nav("Actions") + " tab. If GitHub asks, click <i>I understand my workflows, "
    "go ahead and enable them</i>.",
    "Left sidebar: <b>Grab OCI A1 free instance</b> " + nav("Run workflow")
    + " (right-hand side) " + nav("Run workflow") + " (green button).",
    "After about ten seconds a run appears. Click it " + nav("launch")
    + ", then expand <b>Attempt launch</b>.",
])
S += Tbl(
    ["What the log says", "What it means", "What to do"],
    [
        [C("Out of capacity in ... will retry"), "Auth and config are correct; Oracle "
         "simply has no free ARM slot right now. This is the normal state, sometimes for "
         "days.", "Nothing. The cron keeps trying every 5 minutes."],
        [C("Rate-limited by OCI (429)"), "Oracle asked us to slow down.", "Nothing."],
        [C("SUCCESS -- A1 instance is RUNNING"), "You got it.", "Go to section 8."],
        [C("Non-capacity error") + " (red)", "Something in the secrets or values is "
         "wrong. The real message is a few lines above it.", "See the table below."],
    ],
    [48 * mm, AVAIL - 48 * mm - 48 * mm, 48 * mm],
)
S += [P("Fixing a red run", h2)]
S += Tbl(
    ["Error text contains", "Likely cause", "Fix"],
    [
        [C("NotAuthenticated") + " / " + C("401"), "User OCID, fingerprint or key content "
         "don't match each other, or the key was added to a different user.",
         "Simplest: delete the API key, generate a new one, re-paste "
         + C("OCI_CLI_USER") + ", " + C("OCI_CLI_FINGERPRINT") + ", "
         + C("OCI_CLI_KEY_CONTENT") + " and " + C("OCI_CLI_TENANCY") + "."],
        [C("set OCI_SUBNET_ID") + " or " + C("set SSH_PUBLIC_KEY"),
         "That secret is missing or its name is misspelled.", "Add it with the exact name."],
        [C("NotAuthorizedOrNotFound") + " mentioning the subnet", "Wrong subnet OCID, or "
         "the subnet lives in another compartment or region.",
         "Copy the OCID again (section 3)."],
        [C("LimitExceeded"), "Your tenancy has no A1 quota, or another A1 instance already "
         "uses it.", "Console menu " + nav("Governance & Administration",
         "Limits, Quotas and Usage") + ": search <i>A1</i> and check that <i>Cores for "
         "Standard.A1 based VM and BM Instances</i> is 4. Delete other A1 VMs you don't "
         "need."],
        [C("Could not resolve an image OCID"), "No Ubuntu 24.04 ARM image found by that "
         "name in your region.", "Set " + C("OCI_IMAGE_ID") + " to an id from the image "
         "command in section 3."],
        [C("Invalid private key") + " / " + C("could not deserialize"), "The "
         + C(".pem") + " was pasted incompletely, or it has a passphrase.",
         "Re-paste the whole file; regenerate without a passphrase if needed."],
    ],
    [56 * mm, 52 * mm, AVAIL - 108 * mm],
)
S += Note("After the first successful manual run (green, even if it only said "
          "<i>Out of capacity</i>), the 5-minute schedule takes over on its own. GitHub "
          "cron runs are often 5&ndash;20 minutes late during busy hours; that is fine.")
S += Note("GitHub <b>disables scheduled workflows after 60 days without a commit</b> to the "
          "repo. If it is still hunting after two months, push a tiny commit (edit the "
          "README) or re-enable it from the Actions tab.", "warn")

# ---- 8. landed ----------------------------------------------------------------
S += [P("8. When mnsh1 lands", h1)]
S += Bullets([
    "GitHub opens an <b>issue</b> in your repo titled <i>&hellip;instance created</i> and "
    "emails you. The issue is deliberately generic and contains no IP.",
    "If you set " + C("DISCORD_WEBHOOK") + ", the channel receives the <b>public IP</b> "
    "and the instance OCID.",
    "Otherwise the IP is in the console: menu " + nav("Compute", "Instances", "mnsh1")
    + ", field <b>Public IP address</b>. Or from Cloud Shell:",
])
S += Code("""
iid=$(oci compute instance list --compartment-id "$OCI_TENANCY" \\
        --display-name mnsh1 --lifecycle-state RUNNING \\
        --query 'data[0].id' --raw-output)
oci compute instance list-vnics --instance-id "$iid" \\
  --query 'data[0]."public-ip"' --raw-output
""")
S += Bullets([
    "<b>Stop the retry job:</b> " + nav("Actions", "Grab OCI A1 free instance")
    + ", the <b>&hellip;</b> menu top right " + nav("Disable workflow")
    + ". (The script will never create a second mnsh1 even if you forget, but there is "
    "no reason to keep it running.)",
])
S += [CondPageBreak(80 * mm)]

# ---- 9. first login -----------------------------------------------------------
S += [
    P("9. First login: the terminal and the username", h1),
    P("The Ubuntu image comes with one ready-made user, <b>ubuntu</b>, and it can only log "
      "in with the SSH key you registered. There is no password and root login is "
      "disabled; use " + C("sudo") + " for admin commands. (Oracle Linux images use "
      "<b>opc</b> instead. For Ubuntu images it is always <b>ubuntu</b>.)"),
]
S += Code("""
ssh -i ~/.ssh/oci ubuntu@<PUBLIC_IP>
# first time only: type "yes" to accept the host fingerprint
""")
S += [P("If you get " + C("Permission denied (publickey)") + ": you are pointing at the "
        "wrong private key file, using the wrong username (it is " + C("ubuntu")
        + ", not " + C("root") + "), or the " + C("SSH_PUBLIC_KEY") + " secret had a "
        "typo. The last one means the key baked into the server is wrong; fix the secret, "
        "terminate the instance from the console and let the workflow create it again.",
        small)]

S += [P("Save the connection as a shortcut", h2),
      P("Add this to " + C("~/.ssh/config") + " on your computer (create the file if it "
        "does not exist), and from then on " + C("ssh mnsh1") + " is all you type:")]
S += Code("""
Host mnsh1
    HostName <PUBLIC_IP>
    User ubuntu
    IdentityFile ~/.ssh/oci
""")

S += [P("First five minutes on the box", h2)]
S += Code("""
sudo apt update && sudo apt full-upgrade -y        # patch everything
sudo hostnamectl set-hostname mnsh1                 # nicer prompt
sudo timedatectl set-timezone <Region/City>         # list: timedatectl list-timezones
sudo reboot                                         # log back in after ~30 s
""")

S += [P("Optional: your own username instead of ubuntu", h2),
      P("Run these as <b>ubuntu</b>. The new user gets the same SSH key. Unlike "
        "<b>ubuntu</b>, it will be asked for the password you set here whenever it uses "
        + C("sudo") + ".")]
S += Code("""
sudo adduser --gecos "" mnsh                 # replace mnsh with the name you want
sudo usermod -aG sudo mnsh
sudo mkdir -p /home/mnsh/.ssh
sudo cp ~/.ssh/authorized_keys /home/mnsh/.ssh/
sudo chown -R mnsh:mnsh /home/mnsh/.ssh && sudo chmod 700 /home/mnsh/.ssh
# from your computer:  ssh -i ~/.ssh/oci mnsh@<PUBLIC_IP>
""")

S += [P("Optional: opening a port (for example a web server)", h2),
      P("Two firewalls sit in front of mnsh1 and both default to <i>SSH only</i>. You have "
        "to open a port in both.")]
S += Steps([
    "<b>Oracle side.</b> Menu " + nav("Networking", "Virtual cloud networks", "your VCN",
    "Security Lists", "Default Security List for ...", "Add Ingress Rules")
    + ": Source CIDR " + C("0.0.0.0/0") + ", IP Protocol <b>TCP</b>, Destination port "
    "range <b>80</b>. Repeat for <b>443</b> if you need HTTPS.",
    "<b>Ubuntu side.</b> Oracle's Ubuntu images ship with iptables rules that reject "
    "everything except port 22:",
])
S += Code("""
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo apt install -y iptables-persistent    # answer Yes to save the current rules
sudo netfilter-persistent save
""")
S += [CondPageBreak(80 * mm)]

# ---- 10. safety ----------------------------------------------------------------
S += [P("10. Keeping it safe and free", h1)]
S += Bullets([
    "<b>The repo stays private.</b> Its files contain nothing secret, but the run logs "
    "and issue history are yours.",
    "<b>The " + C(".pem") + " lives only in the GitHub secret</b> (and, if you like, a "
    "password manager). Not in Downloads forever, not in the repo, not in a chat.",
    "<b>Revoke when done.</b> Once mnsh1 exists and the workflow is disabled, delete the "
    "API key under " + nav("My profile", "API keys") + ". GitHub then cannot touch your "
    "account at all. Create a new key if you ever need the workflow again.",
    "<b>Guard " + C("~/.ssh/oci") + ".</b> If you lose it, the ways back in are the OCI "
    "console's serial console or re-creating the instance.",
    "<b>Free means free inside the limits:</b> 4 OCPU, 24 GB RAM, 200 GB block storage "
    "and 10 TB outbound traffic per month, all Always Free. mnsh1 uses 2 / 12 / 200. "
    "Don't attach extra block volumes: the storage allowance is already fully used, so "
    "a second A1 VM's boot disk would be billable.",
    "<b>Idle reclaim.</b> On plain Free Tier accounts Oracle may reclaim an Always Free "
    "VM that sits idle for a week (roughly under 20% CPU, memory and network the whole "
    "time). Run something on it, or upgrade the account to <i>Pay As You Go</i>, which "
    "stays at $0 while you remain within the free limits and exempts you from reclaim.",
])

# ---- worksheet ----------------------------------------------------------------
S += [P("Worksheet", h1),
      P("Fill this in as you go if you prefer paper. These are identifiers, not secrets. "
        "<b>Never write down the private key or the " + C(".pem") + " contents.</b>")]
blank = ""
S += Tbl(
    ["Item", "Value"],
    [
        ["Cloud Account Name (tenancy name)", blank],
        ["Username (email)", blank],
        ["Region identifier (e.g. ap-mumbai-1)", blank],
        ["User OCID, last 8 characters", blank],
        ["Tenancy OCID, last 8 characters", blank],
        ["API key fingerprint", blank],
        ["Public subnet OCID, last 8 characters", blank],
        ["GitHub repo URL", blank],
        ["Public IP of mnsh1", blank],
        ["Workflow disabled? API key deleted?", blank],
    ],
    [70 * mm, AVAIL - 70 * mm],
)
S += [P("Guide version: September 2026. Console labels move around occasionally; if a "
        "menu item is not exactly where this says, use the console search box at the top.",
        small)]

# ---------------------------------------------------------------- build
OUT.parent.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(
    str(OUT), pagesize=A4, leftMargin=M, rightMargin=M, topMargin=22 * mm,
    bottomMargin=20 * mm, title="mnsh1 setup guide",
    subject="Grabbing a free Oracle Cloud ARM server with GitHub Actions",
)
doc.build(S, onFirstPage=on_page, onLaterPages=on_page)
print(f"wrote {OUT}")
