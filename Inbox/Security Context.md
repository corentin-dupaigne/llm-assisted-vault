# Security Context

| | |
|---|---|
| **App** | `<app name>` |
| **Version / commit** | `<version or commit SHA this doc describes>` |
| **Last updated** | `<YYYY-MM-DD>` by `<name>` |
| **Related** | [MASVS coverage matrix](./masvs-coverage-matrix.md) |

> Purpose: describe what we protect, from whom, and how exposed it is.
> Every section feeds a decision in the coverage matrix (noted as **→ Feeds**). If a section changes nothing there, cut it.

---

## 1. App overview

`<2–3 sentences: what the app does, who uses it (students, public, internal staff…), rough expected number of users.>`

## 2. Sensitive data inventory

**→ Feeds:** STORAGE, CRYPTO, PRIVACY · choice of MAS-L1 vs MAS-L2

| Data | Sensitivity | On device? (where) | In transit? (to where) | On backend? | Notes |
|---|---|---|---|---|---|
| `<e.g. session token>` | High | `<e.g. Keychain>` | `<e.g. → API, HTTPS>` | Yes | |
| `<e.g. email, name>` | Medium | | | | |
| `<e.g. user-generated content>` | | | | | |
| `<e.g. third-party API key>` | | | | | |

**Sensitivity scale:**
- **Low**: public or harmless if leaked
- **Medium**: personal data (name, email, preferences)
- **High**: credentials, tokens, keys, location history, health, financial, or anything with legal or regulatory weight (GDPR special categories)

## 3. Authentication & authorization

**→ Feeds:** AUTH

- **Login method(s):** `<email/password, Sign in with Apple, OAuth provider…>`
- **Session mechanism:** `<token type (JWT, opaque…), lifetime, refresh strategy, where stored>`
- **Logout / revocation:** `<is the token invalidated server-side?>`
- **Local / biometric auth:** `<Face ID / Touch ID? used for what?>`
- **Roles & permissions:** `<single user type, or admin/user…? who can access whose data?>`
- **Sensitive operations:** `<actions needing re-authentication, e.g. account deletion, payment>`

## 4. Architecture & data flows

**→ Feeds:** NETWORK · scope of ZAP and the red team

```
<diagram: iOS app ↔ backend API ↔ database; app → third-party services>
```

| Endpoint / service | Owner (us / third party) | Purpose | Data exchanged | Protocol |
|---|---|---|---|---|
| `<api.example.com>` | Us | Main API | | HTTPS |
| `<e.g. Firebase Analytics>` | Third party | | | |

## 5. Platform interactions

**→ Feeds:** PLATFORM, PRIVACY

- **URL schemes / universal links:** `<list, and which parameters they accept>`
- **WebViews:** `<used? loading local or remote content? JavaScript bridge?>`
- **Permissions requested:** `<camera, location, contacts, notifications…, and why each is needed>`
- **Extensions / widgets / App Groups:** `<any shared containers?>`
- **Pasteboard, screenshots, background snapshots:** `<is sensitive data ever displayed or copied?>`

## 6. Dependencies

**→ Feeds:** CODE

- **Package manager(s):** `<Swift Package Manager / CocoaPods / Carthage>` (lockfile: `<path>`)
- **Minimum iOS version:** `<deployment target>`

| SDK / library | Purpose | Has access to sensitive data? |
|---|---|---|
| | | |

## 7. Threat actors & business assets

**→ Feeds:** MAS-L1 vs MAS-L2 · whether to include MAS-R

| Threat actor | Plausible? | What they'd want |
|---|---|---|
| Malicious app on the same device | `<yes/no>` | `<e.g. read tokens via shared storage, hijack deep links>` |
| Attacker with physical access / stolen phone | | `<e.g. extract stored data>` |
| Network attacker (public Wi-Fi) | | `<e.g. intercept traffic>` |
| The user themselves (reverse engineer, cheater) | | `<e.g. unlock premium features, cheat>` |
| Attacker targeting the backend directly | | `<e.g. access other users' data via the API>` |

- **Business assets worth protecting from tampering:** `<premium features, in-app currency, proprietary logic… or "none">`
- **Impact of a breach:** `<what's the worst realistic outcome: data leak, account takeover, reputation…>`

## 8. Profile decision

- **Base profile:** `<e.g. MAS-L1 + MAS-P>`
- **Justification:** `<one or two lines, referencing sections 2 and 7>`

**Adjustments to the base profile:**

| Change | Control(s) / test(s) | Reason (link to section above) |
|---|---|---|
| `<Added / Removed>` | `<e.g. L2 storage tests for STORAGE-1>` | `<e.g. §2: app stores location history>` |

**Out of scope:** `<e.g. MASVS-RESILIENCE: no business assets worth tampering with (§7)>`

---

## Changelog

| Date | Change | Author |
|---|---|---|
| `<YYYY-MM-DD>` | Initial draft | |