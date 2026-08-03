# scan-exposed-keys: Passive API Key Exposure Scanner

Finds public repositories that expose API keys, the typical vibe-coding pattern:
`NEXT_PUBLIC_*` keys, Supabase/Firebase configs, and `.env` files committed to GitHub.

**This tool is passive and ethical by design.** It only reads what is already public
(public repos, public files). It NEVER uses a found key. Its purpose is responsible
disclosure: document the exposure and report it to the owner.

## Why this exists

Projects generated quickly (vibe coding) commonly commit real keys:
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` with the real project URL
- Firebase API keys in `app.json`/`firebase.json`
- `.env` files committed to the repo

An anon key alone is not a secret, but combined with a misconfigured RLS it can expose
data. Documenting and reporting these is a legitimate portfolio and service.

## Install

Requires `gh` CLI authenticated (used for GitHub API). No other dependencies.

```bash
gh auth login
```

## Usage

```bash
# Scan for AWS keys (default)
python3 scripts/scan-exposed-keys.py --pattern AKIA

# Scan for Stripe secret keys
python3 scripts/scan-exposed-keys.py --pattern sk_live

# Scan for Google API keys
python3 scripts/scan-exposed-keys.py --pattern AIza

# Scan for OpenAI/Anthropic keys
python3 scripts/scan-exposed-keys.py --pattern sk-

# JSON output for automation
python3 scripts/scan-exposed-keys.py --pattern AKIA --json
```

## Patterns and severity

| Pattern | What it finds | Severity |
|---------|---------------|----------|
| `AKIA` | AWS Access Key | HIGH |
| `sk_live` | Stripe Secret Key | HIGH |
| `sk-` | OpenAI/Anthropic Key | HIGH |
| `AIza` | Google API Key | MEDIUM |
| Supabase (via query) | anon key + URL | MEDIUM |

## What is filtered

The scanner excludes known noise:
- READMEs of regex/tooling repos (apiguesser, keyhacks, etc.)
- `.example` / `.sample` / `.env.example` files (placeholders)
- Documentation files (SETUP, DEPLOY, AGENTS, CLAUDE, llms.txt)

## Honest limits

- **GitHub secret scanning** automatically blocks known AWS/Stripe/OpenAI keys, so
  real high-severity keys are rare in public repos.
- The most common real finding is **Supabase/Firebase anon keys** in configs, which are
  MEDIUM severity.
- The GitHub code search API has rate limits; run in small batches.

## Ethics and disclosure (MANDATORY)

1. **Never use a found key.** Accessing the owner's data with an exposed key is a crime.
2. **Never test the target beyond reading what is public.**
3. Report via the responsible channel: a GitHub issue on the repo (if public), or the
   owner's security contact.
4. Report ONLY the exposure, with a clear fix suggestion. Do not demand payment.
5. In Brazil and most jurisdictions, accessing a system without authorization is illegal
   (Lei 12.737/2012). Reading public files is fine; using a leaked key is not.

## Output example

```
=== Scanning for AWS Access Key (severity: HIGH) ===
(passive: only public data, never using a key)

[HIGH] AWS Access Key
  repo: owner/project
  file: .env
  url:  https://github.com/owner/project/blob/main/.env
  key:  AKIA... (masked, never used)
```
