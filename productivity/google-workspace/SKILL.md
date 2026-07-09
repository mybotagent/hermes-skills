---
name: google-workspace
description: "Gmail, Calendar, Drive, Docs, Sheets via gws CLI or Python."
version: 1.1.0
author: Nous Research
license: MIT
platforms: [linux, macos, windows]
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 token (created by setup script)
  - path: google_client_secret.json
    description: Google OAuth2 client credentials (downloaded from Google Cloud Console)
metadata:
  hermes:
    tags: [Google, Gmail, Calendar, Drive, Sheets, Docs, Contacts, Email, OAuth]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [himalaya]
---

# Google Workspace

Gmail, Calendar, Drive, Contacts, Sheets, and Docs — through Hermes-managed OAuth and a thin CLI wrapper. When `gws` is installed, the skill uses it as the execution backend for broader Google Workspace coverage; otherwise it falls back to the bundled Python client implementation.

## References

- `references/gmail-search-syntax.md` — Gmail search operators (is:unread, from:, newer_than:, etc.)
- `references/cron-job-patterns.md` — Automated calendar cron jobs (daily summary, weekly preview, midday reminder)

## Scripts

- `scripts/setup.py` — OAuth2 setup (run once to authorize)
- `scripts/google_api.py` — compatibility wrapper CLI. It prefers `gws` for operations when available, while preserving Hermes' existing JSON output contract.

## First-Time Setup

The setup is fully non-interactive — you drive it step by step so it works
on CLI, Telegram, Discord, or any platform.

Define a shorthand first:

```bash
GSETUP="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py"
```

### Step 0: Check if already set up

```bash
$GSETUP --check
```

If it prints `AUTHENTICATED`, skip to Usage — setup is already done.

### Step 1: Triage — ask the user what they need

Before starting OAuth setup, ask the user about Advanced Protection:

**"Does your Google account use Advanced Protection (hardware
security keys required to sign in)? If you're not sure, you probably don't
— it's something you would have explicitly enrolled in."**  

- **No / Not sure** → Normal setup. Continue below.
- **Yes** → Their Workspace admin must add the OAuth client ID to the org's
  allowed apps list before Step 4 will work. Let them know upfront.

**⚠️ Note on services/scopes:** The `setup.py` script always requests ALL
scopes (Gmail, Calendar, Drive, Contacts, Sheets, Docs). There is no
`--services` flag to narrow them. If the user only needs Calendar, tell them
they can **deselect the unwanted scopes** on the Google consent screen during
Step 3. The script handles partial scopes gracefully via
`OAUTHLIB_RELAX_TOKEN_SCOPE`.

If the user needs **email only**, they don't need this skill at all. Use the
`himalaya` skill instead — it works with a Gmail App Password
(Settings → Security → App Passwords) and takes 2 minutes to set up.
No Google Cloud project needed. Load the himalaya skill and follow its setup
instructions.

### Step 2: Create OAuth credentials (one-time, ~5 minutes)

Tell the user:

> You need a Google Cloud OAuth client. This is a one-time setup:
>
> 1. Create or select a project:
>    https://console.cloud.google.com/projectselector2/home/dashboard
> 2. Enable the required APIs from the API Library:
>    https://console.cloud.google.com/apis/library
>    Enable: Gmail API, Google Calendar API, Google Drive API,
>    Google Sheets API, Google Docs API, People API
> 3. Create the OAuth client here:
>    https://console.cloud.google.com/apis/credentials
>    Credentials → Create Credentials → OAuth 2.0 Client ID
> 4. Application type: "Desktop app" → Create
> 5. If the app is still in Testing, add the user's Google account as a test user here:
>    https://console.cloud.google.com/auth/audience
>    Audience → Test users → Add users
> 6. Download the JSON file and tell me the file path
>
> Important Hermes CLI note: if the file path starts with `/`, do NOT send only the bare path as its own message in the CLI, because it can be mistaken for a slash command. Send it in a sentence instead, like:
> `The JSON file path is: /home/user/Downloads/client_secret_....json`

Once they provide the path:

```bash
$GSETUP --client-secret /path/to/client_secret.json
```

If they paste the raw client ID / client secret values instead of a file path,
write a valid Desktop OAuth JSON file for them yourself, save it somewhere
explicit (for example `~/Downloads/hermes-google-client-secret.json`), then run
`--client-secret` against that file.

### Step 3: Get authorization URL

All scopes are always requested (see Step 1 note about narrowing on the
consent screen):

```bash
$GSETUP --auth-url
```

This prints a single URL. Send that exact URL to the user.

The script also saves the pending OAuth session (state + PKCE verifier) into
`~/.hermes/google_oauth_pending.json` so a later exchange can use it even on
a headless system.

Agent rules for this step:
- Send the printed URL to the user as a single clickable link.
- Tell the user that the browser will likely fail on `http://localhost:1` after approval, and that this is expected.
- Tell them to copy the ENTIRE redirected URL from the browser address bar.
- If the user gets `Error 403: access_denied`, send them directly to `https://console.cloud.google.com/auth/audience` to add themselves as a test user.

### Step 4: Exchange the code

The user will paste back either a URL like `http://localhost:1/?code=4/0A...&scope=...`
or just the code string. Either works. The `--auth-url` step stores a temporary
pending OAuth session locally so `--auth-code` can complete the PKCE exchange
later, even on headless systems:

```bash
$GSETUP --auth-code "THE_URL_OR_CODE_THE_USER_PASTED"
```

If `--auth-code` fails, the script prints an error and exits. The most common
cause is an expired code (Google's OAuth codes expire in minutes). In that case,
run `--auth-url` again to get a fresh URL and have the user retry with the
newest browser redirect only.

**⚠️ Discord/remote re-auth pitfall — code expiry loop:**
When the user is not on the same machine (Discord, Telegram, etc.), the OAuth
code routinely expires before the exchange completes. The sequence — click link
→ log in → consent → browser shows ERR_UNSAFE_PORT → copy URL → paste back
into chat → agent processes it — takes longer than Google's ~2 minute code TTL.

*Strategy to break the loop:*

1. Generate a fresh auth URL AND immediately prepare to exchange. Send the URL
   and ask the user to act *now* — explain that the code expires in ~2 minutes
   and they need to paste back immediately after clicking.

2. Use `execute_code` (Python, not terminal shell) for the exchange call to
   eliminate any shell character-parsing delays or `&`-interpretation concerns:

   ```python
   from hermes_tools import terminal
   result = terminal(
       'python ~/.hermes/skills/productivity/google-workspace/scripts/setup.py '
       '--auth-code "THE_URL_OR_CODE"',
       timeout=30
   )
   ```

3. If it fails twice in a row with `invalid_grant: code_verifier or verifier is
   not needed`, switch to a two-phase approach:
   - Phase A: `rm -f ~/.hermes/google_oauth_pending.json` then `--auth-url`.
     This clears any stale pending session so the new URL has a fresh PKCE pair.
   - Phase B: Send the URL. Tell the user clearly: "Click this now, copy the
     address bar URL, and paste it back in the same message." The goal is to
     get the paste back within 30 seconds, before the code expires.

4. If the user keeps getting ERR_UNSAFE_PORT but the code still expires,
   try instructing them to copy ONLY the `code=...` parameter value (the long
   base64 string after `code=` and before `&scope=`), not the full URL. Pass
   just that raw code string to `--auth-code` instead. The script accepts it.

5. **Last resort**: Have the user run the auth from a machine where they can
   keep the browser open and paste immediately — a desktop browser on the same
   machine as the Discord client works best.

### Step 5: Verify

```bash
$GSETUP --check
```

Should print `AUTHENTICATED`. Setup is complete — token refreshes automatically from now on.

### Notes

- Token is stored at `~/.hermes/google_token.json` and auto-refreshes.
- Pending OAuth session state/verifier are stored temporarily at `~/.hermes/google_oauth_pending.json` until exchange completes.
- If `gws` is installed, `google_api.py` points it at the same `~/.hermes/google_token.json` credentials file. Users do not need to run a separate `gws auth login` flow.
- To revoke: `$GSETUP --revoke`

## Usage

All commands go through the API script. Set `GAPI` as a shorthand:

```bash
GAPI="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/google_api.py"
```

### Gmail

```bash
# Search (returns JSON array with id, from, subject, date, snippet)
$GAPI gmail search "is:unread" --max 10
$GAPI gmail search "from:boss@company.com newer_than:1d"
$GAPI gmail search "has:attachment filename:pdf newer_than:7d"

# Read full message (returns JSON with body text)
$GAPI gmail get MESSAGE_ID

# Send
$GAPI gmail send --to user@example.com --subject "Hello" --body "Message text"
$GAPI gmail send --to user@example.com --subject "Report" --body "<h1>Q4</h1><p>Details...</p>" --html
$GAPI gmail send --to user@example.com --subject "Hello" --from '"Research Agent" <user@example.com>' --body "Message text"

# Reply (automatically threads and sets In-Reply-To)
$GAPI gmail reply MESSAGE_ID --body "Thanks, that works for me."
$GAPI gmail reply MESSAGE_ID --from '"Support Bot" <user@example.com>' --body "Thanks"

# Labels
$GAPI gmail labels
$GAPI gmail modify MESSAGE_ID --add-labels LABEL_ID
$GAPI gmail modify MESSAGE_ID --remove-labels UNREAD
```

### Calendar

```bash
# List events (defaults to next 7 days)
$GAPI calendar list
$GAPI calendar list --start 2026-03-01T00:00:00Z --end 2026-03-07T23:59:59Z

# Create event (ISO 8601 with timezone required)
$GAPI calendar create --summary "Team Standup" --start 2026-03-01T10:00:00-06:00 --end 2026-03-01T10:30:00-06:00
$GAPI calendar create --summary "Lunch" --start 2026-03-01T12:00:00Z --end 2026-03-01T13:00:00Z --location "Cafe"
$GAPI calendar create --summary "Review" --start 2026-03-01T14:00:00Z --end 2026-03-01T15:00:00Z --attendees "alice@co.com,bob@co.com"

# NOTE: calendar create does NOT support --reminder. To add reminders
# (popup/email notifications), patch the event afterwards using the
# Google Calendar Python API — get the event, set reminders.overrides,
# then update. See the Reminders section below for the exact script.

# Delete event
$GAPI calendar delete EVENT_ID
```

### Drive

```bash
# Search existing files
$GAPI drive search "quarterly report" --max 10
$GAPI drive search "mimeType='application/pdf'" --raw-query --max 5

# Get metadata for a single file
$GAPI drive get FILE_ID

# Upload a local file (auto-detects MIME type)
$GAPI drive upload /path/to/report.pdf
$GAPI drive upload /path/to/image.png --name "Logo.png" --parent FOLDER_ID

# Download (binary files download as-is; Google-native files export to a
# sensible default — Docs→pdf, Sheets→csv, Slides→pdf, Drawings→png)
$GAPI drive download FILE_ID
$GAPI drive download DOC_ID --output ~/doc.pdf
$GAPI drive download DOC_ID --export-mime text/plain --output ~/doc.txt

# Create a folder
$GAPI drive create-folder "Reports"
$GAPI drive create-folder "Q4" --parent FOLDER_ID

# Share
$GAPI drive share FILE_ID --email alice@example.com --role reader
$GAPI drive share FILE_ID --email alice@example.com --role writer --notify
$GAPI drive share FILE_ID --type anyone --role reader        # anyone with link
$GAPI drive share FILE_ID --type domain --domain example.com --role reader

# Delete — defaults to trash (reversible). Use --permanent to skip the trash.
$GAPI drive delete FILE_ID
$GAPI drive delete FILE_ID --permanent
```

### Contacts

```bash
$GAPI contacts list --max 20
```

### Sheets

```bash
# Create a new spreadsheet
$GAPI sheets create --title "Q4 Budget"
$GAPI sheets create --title "Inventory" --sheet-name "Stock"

# Read
$GAPI sheets get SHEET_ID "Sheet1!A1:D10"

# Write
$GAPI sheets update SHEET_ID "Sheet1!A1:B2" --values '[["Name","Score"],["Alice","95"]]'

# Append rows
$GAPI sheets append SHEET_ID "Sheet1!A:C" --values '[["new","row","data"]]'
```

### Docs

```bash
# Read
$GAPI docs get DOC_ID

# Create a new Doc (optionally seeded with body text)
$GAPI docs create --title "Meeting Notes"
$GAPI docs create --title "Draft" --body "First paragraph..."

# Append text to the end of an existing Doc
$GAPI docs append DOC_ID --text "Additional content to append"
```

### Reminders — via Python API only

The `calendar create` subcommand does **not** support `--reminder`. To add popup or email reminders to an event, patch it after creation using the `googleapiclient` Python API:

```python
from google_api import build_service, get_credentials
service = build_service("calendar", "v3")

# Get the event you just created (replace with your event ID)
event = service.events().get(calendarId="primary", eventId="EVENT_ID").execute()

# Set reminders
event["reminders"] = {
    "useDefault": False,
    "overrides": [
        {"method": "popup", "minutes": 30},   # phone/browser alert
        # {"method": "email", "minutes": 30},  # email notification (optional)
    ]
}
result = service.events().update(
    calendarId="primary", eventId=event["id"], body=event
).execute()
print(f"Reminders set for: {result['summary']}")
```

**Pitfall**: The `calendar create` CLI silently ignores any `--description` field that contains reminder-like syntax. Always use the Python API shown above to set reminders. For simple events without reminders, the CLI works fine.

### Recurrence (RRULE) — via Python API only

The `calendar create` subcommand does **not** support recurring events (RRULE). To create events that repeat (e.g., "first Friday of every month"), use the `googleapiclient` Python API directly through `build_service`:

```python
from google_api import build_service
service = build_service("calendar", "v3")
event = {
    "summary": "Monthly Report",
    "start": {"dateTime": "2026-06-05T08:30:00", "timeZone": "America/New_York"},
    "end": {"dateTime": "2026-06-05T09:30:00", "timeZone": "America/New_York"},
    "recurrence": ["RRULE:FREQ=MONTHLY;BYDAY=1FR"],
}
result = service.events().insert(calendarId="primary", body=event).execute()
```

Common RRULE patterns:

| Pattern | Meaning |
|---------|---------|
| `FREQ=MONTHLY;BYDAY=1FR` | First Friday |
| `FREQ=MONTHLY;BYMONTHDAY=10,11,12,13,14,15,16` | Window of dates (e.g. CPI release) |
| `FREQ=MONTHLY;BYDAY=-1FR,-2FR` | Last two Fridays of month |
| `FREQ=WEEKLY;BYDAY=TH` | Every Thursday |

**Pitfall**: The `calendar create` CLI returns `{"status": "created"}` but ignores `recurrence` if passed. Always use the Python API (as shown above) for recurring events. Individual events (like FOMC with fixed dates) work fine via the CLI.

## Output Format

All commands return JSON. Parse with `jq` or read directly. Key fields:

- **Gmail search**: `[{id, threadId, from, to, subject, date, snippet, labels}]`
- **Gmail get**: `{id, threadId, from, to, subject, date, labels, body}`
- **Gmail send/reply**: `{status: "sent", id, threadId}`
- **Calendar list**: `[{id, summary, start, end, location, description, htmlLink}]`
- **Calendar create**: `{status: "created", id, summary, htmlLink}`
- **Drive search**: `[{id, name, mimeType, modifiedTime, webViewLink}]`
- **Drive get**: `{id, name, mimeType, modifiedTime, size, webViewLink, parents, owners}`
- **Drive upload**: `{status: "uploaded", id, name, mimeType, webViewLink}`
- **Drive download**: `{status: "downloaded", id, name, path, mimeType}`
- **Drive create-folder**: `{status: "created", id, name, webViewLink}`
- **Drive share**: `{status: "shared", permissionId, fileId, role, type}`
- **Drive delete**: `{status: "trashed" | "deleted", fileId, permanent}`
- **Contacts list**: `[{name, emails: [...], phones: [...]}]`
- **Sheets get**: `[[cell, cell, ...], ...]`
- **Sheets create**: `{status: "created", spreadsheetId, title, spreadsheetUrl}`
- **Docs create**: `{status: "created", documentId, title, url}`
- **Docs append**: `{status: "appended", documentId, inserted_at, characters}`

## Service Account Authentication

As an alternative to OAuth user tokens (which expire or get revoked), you can use a Google Cloud **Service Account**:

1. Create a service account in Google Cloud Console (IAM → Service Accounts)
2. Download its JSON key → save to `~/.hermes/google_service_account.json`
3. Share the target Google Calendar with the service account email (Calendar settings → Share)
4. Save the user's calendar email in `~/.hermes/google_calendar_user.txt`
5. `get_credentials()` in `google_api.py` auto-detects the service account key and uses it

The service account works for Calendar read/write. **Pitfall**: `calendarId="primary"` resolves to the service account's own empty calendar — `_resolve_calendar_id()` overrides it to the shared user email from `google_calendar_user.txt`.

## Rules

1. **Never send email, create/delete calendar events, delete Drive files, share files, or modify Docs/Sheets without confirming with the user first.** Show what will be done (recipients, file IDs, content, share role) and ask for approval. For `drive delete`, prefer the default trash (reversible) over `--permanent`.
2. **Check auth before first use** — run `setup.py --check`. If it fails, guide the user through setup.
3. **Use the Gmail search syntax reference** for complex queries — load it with `skill_view("google-workspace", file_path="references/gmail-search-syntax.md")`.
4. **Calendar times must include timezone** — always use ISO 8601 with offset (e.g., `2026-03-01T10:00:00-06:00`) or UTC (`Z`).
5. **Respect rate limits** — avoid rapid-fire sequential API calls. Batch reads when possible.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `NOT_AUTHENTICATED` | Run setup Steps 2-5 above |
| `REFRESH_FAILED` | Token revoked or expired — redo Steps 3-5 |
| `HttpError 403: Insufficient Permission` | Missing API scope — `$GSETUP --revoke` then redo Steps 3-5 |
| `AUTHENTICATED (partial)` or "Token missing scopes" | New write capabilities (Drive write/delete, Docs create/edit) require re-authorization. `$GSETUP --revoke` then redo Steps 3-5 to grant the upgraded scopes. |
| `HttpError 403: Access Not Configured` | API not enabled — user needs to enable it in Google Cloud Console |
| `ModuleNotFoundError` | Run `$GSETUP --install-deps` |
| Advanced Protection blocks auth | Workspace admin must allowlist the OAuth client ID |
| OAuth codes expire before exchange (`invalid_grant: code_verifier or verifier is not needed`) | Switch to **Service Account** (see Service Account Authentication section). The PKCE code expires in ~1 minute; if the user can't paste the redirect URL fast enough, service account is the reliable alternative. |
| `TOKEN_REVOKED` / Token expired or revoked | Try `--check` first. If refresh fails, either re-run OAuth setup OR switch to Service Account — `get_credentials()` auto-detects `google_service_account.json` and uses it preferentially. |
| OAuth code keeps expiring (`invalid_grant`) during agent-mediated setup | The PKCE auth code expires in ~1 minute. When the agent sends the URL to a user via Discord/etc., the round-trip often exceeds the expiry window. **Workaround:** Have the user paste just the `code=` value from the redirect URL address bar (not the full URL) — the setup.py accepts bare codes. If this still fails, switch to a **Service Account** (see below). |
| `state` parameter missing from redirect URL | Desktop app OAuth redirects may omit the `state` parameter. This is safe — setup.py's `_extract_code_and_state()` handles `state=None` gracefully by skipping CSRF validation. The code expiry is almost always the real cause of failure, not the missing state. |

### Service Account Alternative (for headless/server environments)

When the OAuth PKCE desktop flow keeps failing due to user interaction delays, use a Google Service Account instead:

1. **Create a service account** at https://console.cloud.google.com/iam-admin/serviceaccounts
2. **Download JSON key** → save to `~/.hermes/google_service_account.json`
3. **Share the target Google Calendar** with the service account email (Calendar settings → Share with specific people → add `NAME@PROJECT.iam.gserviceaccount.com` → "Make changes to events" or "See all event details")
4. **Update `get_credentials()`** in `google_api.py` to check for `google_service_account.json` first:

```python
SA_PATH = HERMES_HOME / "google_service_account.json"
if SA_PATH.exists():
    from google.oauth2.service_account import Credentials as SACredentials
    return SACredentials.from_service_account_file(str(SA_PATH), scopes=SCOPES)
```

The service account has no refresh-token expiry — it works indefinitely and requires no user interaction.
| `invalid_grant: code_verifier or verifier is not needed` | OAuth code expired before exchange completed. Codes last ~2 minutes. Generate a fresh URL (`rm pending; --auth-url`), send to user, and have them paste back immediately. See "Discord/remote re-auth pitfall" in Step 4. |
| `TOKEN_INVALID` | Token file is corrupt or irrecoverable. Run `$GSETUP --revoke`, then redo Steps 3-5 from scratch. |
| Advanced Protection blocks auth | Workspace admin must allowlist the OAuth client ID |

## Revoking Access

```bash
$GSETUP --revoke
```
