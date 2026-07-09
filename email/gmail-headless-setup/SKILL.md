---
name: gmail-headless-setup
description: "Set up Gmail access for a Hermes agent on Discord/headless contexts via himalaya + pass + Gmail App Password — when OAuth PKCE flow fails or when user wants different accounts per service. Includes verified install commands, config template, and account-separation pattern."
version: 1
metadata:
  hermes:
    tags: [Gmail, himalaya, headless, Discord, App-Password, OAuth-fallback]
---

# Gmail Headless Setup

When Google OAuth's PKCE flow is unreliable (Discord code-expiry loops,
`invalid_grant`, ERR_UNSAFE_PORT) or when the user wants **different
accounts for Gmail vs Calendar**, use himalaya + a Gmail App Password
instead. ~2 minutes, no browser interaction, no code expiry.

## When This Recipe Wins

| Scenario | Recommended path |
|---|---|
| Discord/Telegram/Slack agent + Gmail | **This recipe** |
| User wants different Gmail + Calendar accounts | **This recipe** for Gmail + service-account for Calendar |
| Local CLI user + Gmail | OAuth (`google-workspace`) — one-time browser flow OK |
| Agent needs Calendar/Drive/Docs too | OAuth (`google-workspace`) — bundles scopes |

The decision rule: **if the agent can't sit next to the user at a browser
for ~5 minutes, prefer himalaya + App Password over OAuth.**

## Full Setup (verified July 2026)

### Step 1: User creates Gmail App Password

User does this in their browser (must be signed into target Gmail):

1. https://myaccount.google.com/security
2. **2-Step Verification** must be ON (toggle on first if not — requires phone)
3. https://myaccount.google.com/apppasswords
4. App name: `hermes-himalaya` → **Create**
5. 16-char password shown (e.g. `abcd efgh ijkl mnop`) — copy with spaces

> ⚠️ **Do NOT invent a slash command to handle the secret.** Hermes has
> no `/set-secret`. Real options when the user is in Discord:
>
> 1. User pastes the 16-char password once in chat → agent runs the
>    direct-gpg workaround in Step 4 → password appears once in chat log.
>    **Recommend rotating (deleting + recreating the app password)
>    immediately after Step 6 succeeds.**
> 2. User runs `pass insert email/gmail-app-pass` from their own
>    terminal and pushes via `pass git` sync.
> 3. Switch to OAuth (`google-workspace` skill) — but PKCE codes
>    routinely expire in the Discord round-trip.
>
> The "auto-deleting slash command" and "private DM that user deletes
> after" mentioned in the prior version **do not exist as reliable
> mechanisms** in Hermes — Discord messages persist for the channel
> history, and Hermes has no slash command for ephemeral secret
> capture. Be honest about this and recommend rotation after setup.
>
> App name choice: any custom string works (`hermes-himalaya`,
> `google-hermes`, etc.). Tell the user to use something recognizable
> so they remember which app to rotate later.

### Step 2: Agent installs himalaya CLI

```bash
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh \
  | PREFIX=~/.local sh
export PATH="$HOME/.local/bin:$PATH"
himalaya --version   # confirm: v1.2.0+
```

Add `export PATH="$HOME/.local/bin:$PATH"` to `~/.bashrc` so it persists.

### Step 3: Install `pass` and create a headless GPG key

```bash
sudo apt-get install -y pass

cat > /tmp/gpg-batch <<'EOF'
%no-protection
Key-Type: RSA
Key-Length: 4096
Name-Real: hermes-himalaya
Name-Email: hermes@localhost
Expire-Date: 0
%commit
EOF
gpg --batch --gen-key /tmp/gpg-batch

KEY=$(gpg --list-secret-keys --keyid-format=long hermes@localhost \
  | awk '/^sec/{print $2}' | cut -d/ -f2)
pass init "$KEY"
```

The `%no-protection` directive creates a key with **no passphrase**. This
is required for headless agent use — a passphrase would prompt every
`pass show` and hang the agent. Trade-off: anyone with filesystem access
to `~/.gnupg/private-keys-v1.d/` can read the password store. Acceptable
in a single-user VM.

### Step 4: User stores the app password

**If user has direct shell access** (their own machine, SSH):
```bash
pass insert email/gmail-app-pass
# paste the 16-char password at prompt
```

**If user is in Discord/Telegram with no direct shell** (most common case
for this skill): `pass insert` will silently fail because gpg-agent's
pinentry needs a real TTY and the Hermes `terminal` tool runs without
one. Use the **direct gpg encryption workaround**:

```bash
# Wait for user to paste the 16-char password in chat
SECRET="<16-char-or-no-space-16-char>"
GPG_ID=$(cat ~/.password-store/.gpg-id)
mkdir -p ~/.password-store/email

printf '%s' "$SECRET" | gpg --batch --yes \
  --trust-model always \
  --recipient "$GPG_ID" \
  --encrypt \
  --output ~/.password-store/email/gmail-app-pass.gpg

# Verify
pass show email/gmail-app-pass
```

Why this works: `gpg --encrypt --recipient <public-key>` does NOT call
pinentry for the recipient's secret key. Only the recipient's *public*
key is needed, which is in the keyring. `--trust-model always` skips the
trust check.

What does NOT work (silently exits 1, no stderr captured):
```bash
echo "$SECRET" | pass insert email/gmail-app-pass          # pipe, no TTY
pass insert email/gmail-app-pass <<< "$SECRET"             # here-string, no TTY
printf '%s\n' "$SECRET" | GPG_TTY=$(tty) pass insert ...   # tty resolves to /dev/null
terminal(command="pass insert ...", pty=true)              # gpg-agent rejects fake TTY
gpg --batch --pinentry-mode loopback --passphrase '' --symmetric  # "Invalid passphrase"
```

### Step 5: Write the config

```bash
mkdir -p ~/.config/himalaya
```

`~/.config/himalaya/config.toml`:

```toml
[accounts.gmail]
email = "user@gmail.com"
display-name = "User Name"
default = true

backend.type = "imap"
backend.host = "imap.gmail.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "user@gmail.com"
backend.auth.type = "password"
backend.auth.cmd = "pass show email/gmail-app-pass"

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.gmail.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "user@gmail.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "pass show email/gmail-app-pass"

# v1.2.0+ syntax — REQUIRED for Gmail. The singular [folder.alias] form is
# silently ignored, causing `message send` to exit non-zero AFTER SMTP
# delivery succeeds. On retry the script sends a duplicate email.
folder.aliases.inbox = "INBOX"
folder.aliases.sent = "[Gmail]/Sent Mail"
folder.aliases.drafts = "[Gmail]/Drafts"
folder.aliases.trash = "[Gmail]/Trash"
```

### Step 6: Verify

```bash
himalaya folder list                       # should list Gmail folders
himalaya envelope list --page-size 5       # latest 5 inbox messages
himalaya message read 1                    # read message ID 1
```

## Account Separation Pattern

A common real-world case: **personal Gmail** for the agent + **work/shared
Calendar** via service account. OAuth bundles all scopes under one
identity, so this is awkward with `google-workspace`. With himalaya +
service account it's clean:

| Service | Account | Mechanism |
|---|---|---|
| Gmail (`sanghee.lee2222@gmail.com`) | Personal | himalaya + App Password (this recipe) |
| Calendar (`tkd1496@gmail.com`) | Shared/work | Service account (`google-workspace` skill) |

The two auth files don't collide:
- `~/.password-store/` — himalaya
- `~/.hermes/google_service_account.json` — Calendar

The agent must explicitly route: Gmail queries → himalaya,
Calendar queries → google-workspace service-account path.

## Pitfalls

1. **No-passphrase GPG key is mandatory for headless use.** With a
   passphrase, every `pass show` blocks on interactive prompt.
2. **App Password requires 2FA.** No workaround — user must enable
   2-Step Verification first.
3. **Gmail folder aliases MUST be `[Gmail]/Sent Mail` etc.**, not `Sent`.
   Use `folder.aliases.*` (plural, dotted) under the account section.
4. **Himalaya not on default PATH** after `PREFIX=~/.local` install —
   persist via `~/.bashrc`.
5. **Don't mix himalaya pass store with OAuth `google_token.json` in the
   same decision path** — Calendar queries can pick the wrong credential.
   Always route Gmail → himalaya, Calendar/Drive → google-workspace.
6. **`curl | sh` install requires user approval** in Hermes (security scan
   flags pipe-to-interpreter). Either pre-approve once or use
   `tirith run`/`vet` first.
7. **`pass` not installed by default** on minimal Ubuntu — apt-install
   first, then init GPG key, then `pass init`.
8. **`pass insert` is broken from the Hermes `terminal` tool.** The
   command silently exits with code 1 because gpg-agent pinentry
   needs a real TTY. The direct `gpg --encrypt --recipient <pubkey>`
   workaround in Step 4 is the only path that works in Discord/headless
   setups. Tested July 2026.
9. **The chat history contains the 16-char password after setup.**
   Always tell the user to rotate (delete + recreate) the app
   password at https://myaccount.google.com/apppasswords once
   `himalaya envelope list` succeeds in Step 6. Without rotation,
   anyone with read access to the chat channel has the credential.
10. **Don't mix himalaya pass store with OAuth `google_token.json`**
    in the same decision path — Gmail queries can pick the wrong
    credential. Always route Gmail → himalaya, Calendar/Drive →
    google-workspace.

## Discord-Specific Workflow Lessons (tested July 2026)

### App name consistency

The user may change the app name mid-setup (`hermes-himalaya` →
`google-hermes` → `hermes-google`). **Pin the app name ONCE** at the
start of Step 1 and refuse to proceed until it's confirmed. Each name
generates a different 16-char password, so flipping names mid-flow
makes it impossible to know which password was rotated.

```
"앱 이름은 정확히 하나만 정해줘. 변경하면 새 16자리 다시 생성해야 함."
```

### Channel/thread boundary check FIRST

Before asking for the app password, verify the current channel/thread
topic allows Gmail work. Users often ask for Gmail in a calendar or
investment thread — refuse politely and redirect to the home channel
or a dedicated #infra thread. This is governed by the
`channel-context-discipline` skill, not this one.

### Diagnostic priority when "Gmail broken"

If user reports Gmail stopped working, check in this order:

1. **OAuth token revoked?** — `~/.hermes/google_token.json` may have
   `TOKEN_REVOKED` status. Don't auto-retry OAuth; route to himalaya.
2. **Service account still alive?** — Calendar often keeps working via
   `google_service_account.json` even when OAuth user token is dead.
   Offer Gmail via himalaya + Calendar via service-account as the
   cleanest split.
3. **App password rotated by user?** — User may have rotated without
   telling agent. Symptom: `pass show` decrypts OK but auth fails.
   Re-run direct-gpg workaround with the new password.
4. **`pass show` works but himalaya fails** — check the `auth.cmd`
   path in `config.toml` matches the actual store path.

### User-preferred handoff pattern

The user prefers: **agent guides, user executes critical steps
themselves.** Concretely: agent provides the URL/command, user pastes
back the result. Don't try to automate `pass insert` over chat when
the user has shell access — tell them to run it locally and confirm
with `pass show` output. This keeps secrets off the chat history
entirely.

Phrasing that works:
```
"브라우저에서 새 16자리 만들고, 본인 터미널에서:
   pass insert email/gmail-app-pass
실행 후 pass show로 검증되면 '다음진행' 알려줘."
```

### Rotation sequence (canonical)

When user says "이미 지움" / "회전했어" / "다음진행":

1. Verify the old `pass show` returns the OLD password (so we know
   store still works).
2. Ask user to paste the NEW 16-char password → direct-gpg workaround.
3. Verify `pass show` returns the NEW password.
4. Tell user to rotate again if they want the new password out of
   chat history (yes, rotate twice in a row — once to remove the
   leaked one, once to remove the next one).

Step 4 sounds paranoid but matches the user's threat model: assume
chat log is forever-leaked.

## Reference

The full recipe is also captured in
`/home/ubuntu/.hermes/skills/email/himalaya/references/discord-headless-setup.md`
on the local install (write-protected to the bundled himalaya skill from
the curator path; this umbrella skill provides the same content).