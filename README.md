# LinkedIn Auto-Post — Shravan Kumar

Automated daily LinkedIn posting for **Irukulla Shravan Kumar** (Medical Writing | Scientific Writer II at Bristol Myers Squibb).

## How It Works

- GitHub Actions runs daily at **9:00 AM IST**
- Picks the next post from `posts/` folder sequentially (day01 → day02 → ...)
- Posts to LinkedIn via the REST API
- Auto-refreshes expired tokens

## Setup Guide

### Step 1: Create LinkedIn App

1. Go to https://www.linkedin.com/developers/apps
2. Login with Shravan's LinkedIn account
3. Click **Create App**
4. Fill: App name = `Shravan Auto Post`, link any LinkedIn Page
5. Note the **Client ID** and **Client Secret** from Auth tab

### Step 2: Request API Access

1. In your app → **Products** tab
2. Enable: **Share on LinkedIn** + **Sign In with LinkedIn using OpenID Connect**

### Step 3: Get Access Token

1. In **Auth** tab → Add redirect URL: `http://localhost:8080/callback`
2. Open in browser (replace YOUR_CLIENT_ID):

```
https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=YOUR_CLIENT_ID&redirect_url=http://localhost:8080/callback&scope=openid%20profile%20w_member_social
```

3. Authorize → copy the `code` from redirect URL
4. Exchange for token:

```bash
curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
  -d "grant_type=authorization_code" \
  -d "code=YOUR_CODE" \
  -d "redirect_uri=http://localhost:8080/callback" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET"
```

5. Save the `access_token` and `refresh_token` from response

### Step 4: Get Person ID

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "LinkedIn-Version: 202606" \
     "https://api.linkedin.com/v2/userinfo"
```

Use the `sub` field as PERSON_ID.

### Step 5: Create GitHub PAT

1. https://github.com/settings/tokens → Generate new token (classic)
2. Scope: `repo`
3. Copy token

### Step 6: Add Secrets to This Repo

Go to: Settings → Secrets and variables → Actions → New repository secret

| Secret Name | Value |
|---|---|
| `LINKEDIN_ACCESS_TOKEN` | From Step 3 |
| `LINKEDIN_PERSON_ID` | From Step 4 |
| `LINKEDIN_CLIENT_ID` | From Step 1 |
| `LINKEDIN_CLIENT_SECRET` | From Step 1 |
| `LINKEDIN_REFRESH_TOKEN` | From Step 3 |
| `GH_PAT` | From Step 5 |

### Step 7: Enable Actions

Go to: Actions tab → Enable workflows

## Done!

The bot will post daily at 9 AM IST. You can also trigger manually from Actions → Daily LinkedIn Post → Run workflow.

## Post Schedule

30 days of medical writing thought-leadership content covering:
- Career insights & mentoring
- CSR, Protocol, ICF writing tips
- Regulatory affairs (FDA/EMA)
- AI in medical writing
- Industry trends

## Test Locally

```bash
export LINKEDIN_ACCESS_TOKEN="your_token"
export LINKEDIN_PERSON_ID="your_id"
python post_to_linkedin.py
```
