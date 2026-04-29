# Resend Domain Setup Guide for Production Email

## Why this is needed
Resend in **test mode** only allows sending emails to the verified owner email
(currently `andrehangar@gmail.com`). To send password reset emails to ANY user,
you must verify a domain you own.

Without this, `/api/auth/forgot-password` will silently fail to deliver emails
(it returns 200 to the user for privacy, but the email is never sent).

## Step-by-step

### 1. Buy or use an existing domain
Use a domain you own — e.g. `cibospirituale.it` or a subdomain like `mail.amenapp.com`.

### 2. Add the domain to Resend
1. Login at https://resend.com
2. Sidebar → **Domains** → **Add Domain**
3. Enter your domain (e.g. `cibospirituale.it`)
4. Choose region: **eu-west-1** (closer to Italy = faster)

### 3. Add DNS records to your DNS provider
Resend will show you **3 records** to add:

| Type | Name | Value |
|------|------|-------|
| MX   | `send` | `feedback-smtp.eu-west-1.amazonses.com` (priority 10) |
| TXT  | `send` | `v=spf1 include:amazonses.com ~all` |
| TXT  | `resend._domainkey` | `p=MIGfMA0...` (long DKIM key) |

Add them in the DNS panel of your provider:
- **Aruba**: Pannello → DNS → Modifica record
- **Cloudflare**: DNS → Records → Add record
- **Namecheap**: Domain List → Manage → Advanced DNS
- **GoDaddy**: My Products → DNS → Manage zones

⚠️ Do NOT add the trailing `.cibospirituale.it` if your provider auto-appends it.

### 4. Verify
- Click **Verify DNS Records** in Resend dashboard
- Verification takes 5-30 minutes (DNS propagation)
- Status changes from "Pending" → "Verified" with a green check

### 5. Update backend env
```bash
# /app/backend/.env
SENDER_EMAIL=noreply@cibospirituale.it
```

### 6. Restart backend
```bash
sudo supervisorctl restart backend
```

### 7. Test
```bash
curl -X POST https://YOUR_BACKEND/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"any-real-user@gmail.com"}'
```

Check the inbox of the test email — it should arrive within seconds.
Check backend logs:
```bash
tail -f /var/log/supervisor/backend.err.log | grep -i resend
```

## Common issues

### "Domain not verified" even after 30 min
- Verify TXT record value has no extra quotes
- Re-check DKIM key has no line breaks (it must be one long line)
- Use https://mxtoolbox.com to inspect DNS records

### Emails go to spam
- Add a `DMARC` record (optional but recommended):
  - Type: TXT
  - Name: `_dmarc`
  - Value: `v=DMARC1; p=none; rua=mailto:postmaster@cibospirituale.it`
- Warm up the domain: send slowly (10-50 emails/day) for the first week

### Rate limit reached
Resend free plan = 100 emails/day, 3000/month. Upgrade to Pro ($20/mo) for 50k/mo.

## Quick verification
After setup, the response from `/api/auth/forgot-password` is unchanged (always 200),
but you'll see in backend logs:
- ✅ `INFO: Password reset email sent to user@example.com`
- ❌ `ERROR: Failed to send reset email to user@example.com: ...`
