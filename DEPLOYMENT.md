# Deployment Guide

## Quick Start (Manual Deploy — Recommended First)

SSH into your VPS and run:

```bash
ssh root@YOUR_SERVER_IP
cd ~/ajay-ai-fund
git pull origin master
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

> **Tip:** Get manual deployment stable before enabling automated deploys.

---

## Automated Deploy via GitHub Actions

The repository includes a deploy workflow (`.github/workflows/deploy.yml`) that
can be triggered manually from the **Actions** tab. Once you are confident in
the setup, you can add a `push` trigger to deploy automatically on every merge
to `master`.

### 1. Generate an SSH Key (on your VPS)

```bash
# If you don't already have a key pair:
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/github_deploy -N ""

# Add the public key to authorized_keys:
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
```

### 2. Add GitHub Secrets

Go to **GitHub → Settings → Secrets and variables → Actions** and add:

| Secret     | Value                                                        |
|------------|--------------------------------------------------------------|
| `HOST`     | Your server IP address (e.g. `123.45.67.89`)                 |
| `USERNAME` | SSH user (e.g. `root`)                                       |
| `PORT`     | SSH port (default `22` — only needed if different)           |
| `KEY`      | The **full** private key from `~/.ssh/github_deploy`         |

To copy the private key:

```bash
cat ~/.ssh/github_deploy
```

Paste the **entire** output (including `-----BEGIN ... KEY-----` and
`-----END ... KEY-----` lines) into the `KEY` secret.

### 3. Test SSH Access

From your local machine, verify you can connect:

```bash
ssh -i ~/.ssh/github_deploy root@YOUR_SERVER_IP
```

If this fails, GitHub Actions will also fail — fix SSH access first.

### 4. Trigger a Deploy

- **Manual:** Go to **Actions → Deploy → Run workflow**.

---

## Process Managers

For production, run the app behind a process manager so it restarts on
crashes and survives reboots.

### systemd

> **Security note:** Running as `root` is shown for simplicity. In
> production, create a dedicated user (e.g. `deploy`) with limited
> privileges and update `User` and `WorkingDirectory` accordingly.

```bash
sudo tee /etc/systemd/system/ajay-ai-fund.service <<EOF
[Unit]
Description=AI Fund Trading Bot
After=network.target

[Service]
User=root
WorkingDirectory=/root/ajay-ai-fund
ExecStart=/usr/local/bin/uvicorn app.main:app --host 0.0.0.0 --port 5000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now ajay-ai-fund
```

### Docker

```bash
docker compose up -d
```

---

## Disabling Automated Deploy

If you want CI green without deployment, simply delete
`.github/workflows/deploy.yml` or remove the `push` trigger from it.
The CI workflow (`.github/workflows/ci.yml`) is independent and will
continue to lint and test on every push.
