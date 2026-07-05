# GitHub Actions Secrets — Copy/Paste Checklist

Paste each value into **Settings → Secrets and variables → Actions** as a new secret.

---

# Render service environment variables

TELEGRAM_BOT_TOKEN=
TELEGRAM_BOT_USERNAME=
TELEGRAM_ADMIN_IDS=
JWT_SECRET_KEY=
XENDIT_SECRET_KEY=
PAYMONGO_SECRET_KEY=
PAYMONGO_PUBLIC_KEY=
MAGPIE_API_KEY=
MAGPIE_WEBHOOK_SECRET=
ENVIRONMENT=production
ALLOWED_ORIGINS=
DATABASE_URL= (set by Render managed DB or external DB)

---

# Cloud Run (GCP)

GCP_SA_KEY= (paste full JSON service account key)
GCP_PROJECT=
CLOUD_RUN_SERVICE=
CLOUD_RUN_REGION=

---

# AWS (ECS / Fargate / Lightsail)

AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
DB_PASSWORD=
TELEGRAM_BOT_TOKEN=
TELEGRAM_BOT_USERNAME=
TELEGRAM_ADMIN_IDS=
JWT_SECRET_KEY=
ADMIN_USER_PASSWORD=
XENDIT_SECRET_KEY= (legacy/optional)
PAYMONGO_SECRET_KEY= (optional)
PAYMONGO_PUBLIC_KEY= (optional)
PAYMONGO_WEBHOOK_SECRET= (optional)
PHOTONPAY_APP_ID= (optional)
PHOTONPAY_APP_SECRET=d45dcc80d0f9f9f9a63c5d0b0bf9f9f9eeb5eef9
PHOTONPAY_SITE_ID= (optional)
TRANSFI_API_KEY= (optional)
TRANSFI_WEBHOOK_SECRET= (optional)

---

# EC2 deploy

EC2_HOST=
EC2_USER=
EC2_SSH_KEY= (paste PEM private key contents)
EC2_APP_DIR=

---

# Generic

GITHUB_TOKEN= (provided by Actions)
CF_API_TOKEN=
CF_ZONE_ID=

# Notes

- For multiline secrets (JSON, PEM), paste the exact content preserving newlines.
- After adding secrets, run the appropriate workflow manually from Actions to verify.
