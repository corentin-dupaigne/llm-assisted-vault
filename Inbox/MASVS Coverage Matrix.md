# MASVS Coverage Matrix

| | |
|---|---|
| **App** | `<app name>` |
| **Standard** | OWASP MASVS v2 (controls from mas.owasp.org/MASVS) |
| **Target profile(s)** | `<e.g. MAS-L1 + MAS-P>` (see justification below) |
| **Last updated** | `<YYYY-MM-DD>` by `<name>` |

## Profile justification

> Which MAS profiles apply and why. Base this on `docs/security/context.md` (sensitive data, auth, backend).
> Reference: mas.owasp.org/Profiles, e.g. L1+P for low-risk data, L2+P for sensitive data (health, messaging), add R if the app holds business assets worth tampering with.

`<2–4 sentences>`

## Legend

**Scope:** ✅ in scope · ❌ out of scope (reason required in "Out of scope & accepted risks") · ❓ to decide

**Status:**
- ✅ Verified: check in place, no open finding
- ⚠️ Open finding(s): link the issue
- 🔧 Check planned, not implemented yet
- ⏳ Not covered yet
- 🚫 Accepted risk

**Automated** = runs in the pipeline on every push/PR. **Manual** = red team / review, run periodically.
The "planned" entries below are suggestions: replace them with what you actually implement.

---

## MASVS-STORAGE: data at rest

| ID | Requirement | Scope | Automated check | Manual check | MASWE / MASTG refs | Status | Issues |
|---|---|---|---|---|---|---|---|
| STORAGE-1 | The app securely stores sensitive data | ❓ | planned: Semgrep custom rules (UserDefaults, plist, files), MobSF | planned: inspect app container on device / simulator | | ⏳ | |
| STORAGE-2 | The app prevents leakage of sensitive data | ❓ | planned: Semgrep (logging of sensitive data) | planned: check logs, backups, screenshots, pasteboard | | ⏳ | |

## MASVS-CRYPTO

| ID | Requirement | Scope | Automated check | Manual check | MASWE / MASTG refs | Status | Issues |
|---|---|---|---|---|---|---|---|
| CRYPTO-1 | The app employs current strong cryptography and uses it according to industry best practices | ❓ | planned: Semgrep / SonarQube (weak algorithms), MobSF | planned: code review of crypto usage | | ⏳ | |
| CRYPTO-2 | The app performs key management according to industry best practices | ❓ | planned: gitleaks, MobSF (hardcoded keys) | planned: review key storage (Keychain / Secure Enclave) | | ⏳ | |

## MASVS-AUTH

| ID | Requirement | Scope | Automated check | Manual check | MASWE / MASTG refs | Status | Issues |
|---|---|---|---|---|---|---|---|
| AUTH-1 | The app uses secure authentication and authorization protocols and follows the relevant best practices | ❓ | planned: ZAP on backend API | planned: red team (session handling, token reuse, access control between users) | | ⏳ | |
| AUTH-2 | The app performs local authentication securely according to the platform best practices | ❓ | | planned: red team (Face ID / Touch ID bypass) | | ⏳ | |
| AUTH-3 | The app secures sensitive operations with additional authentication | ❓ | | planned: red team | | ⏳ | |

## MASVS-NETWORK: data in transit

| ID | Requirement | Scope | Automated check | Manual check | MASWE / MASTG refs | Status | Issues |
|---|---|---|---|---|---|---|---|
| NETWORK-1 | The app secures all network traffic according to the current best practices | ❓ | planned: MobSF (ATS exceptions in Info.plist) | planned: intercept traffic with mitmproxy | | ⏳ | |
| NETWORK-2 | The app performs identity pinning for all remote endpoints under the developer's control | ❓ | | planned: red team (pinning bypass attempt) | | ⏳ | |

## MASVS-PLATFORM

| ID | Requirement | Scope | Automated check | Manual check | MASWE / MASTG refs | Status | Issues |
|---|---|---|---|---|---|---|---|
| PLATFORM-1 | The app uses IPC mechanisms securely | ❓ | planned: MobSF (URL schemes, universal links) | planned: red team (malicious deep links) | | ⏳ | |
| PLATFORM-2 | The app uses WebViews securely | ❓ | planned: Semgrep (WKWebView config, JS bridges) | planned: red team | | ⏳ | |
| PLATFORM-3 | The app uses the user interface securely | ❓ | | planned: review (sensitive fields, screenshots in app switcher) | | ⏳ | |

## MASVS-CODE

| ID | Requirement | Scope | Automated check | Manual check | MASWE / MASTG refs | Status | Issues |
|---|---|---|---|---|---|---|---|
| CODE-1 | The app requires an up-to-date platform version | ❓ | planned: CI check on deployment target | | | ⏳ | |
| CODE-2 | The app has a mechanism for enforcing app updates | ❓ | | planned: review | | ⏳ | |
| CODE-3 | The app only uses software components without known vulnerabilities | ❓ | planned: OSV-Scanner (Package.resolved / Podfile.lock) | | | ⏳ | |
| CODE-4 | The app validates and sanitizes all untrusted inputs | ❓ | planned: Semgrep, SonarQube | planned: red team (deep link params, API responses) | | ⏳ | |

## MASVS-RESILIENCE (only if MAS-R is in your profile)

| ID | Requirement | Scope | Automated check | Manual check | MASWE / MASTG refs | Status | Issues |
|---|---|---|---|---|---|---|---|
| RESILIENCE-1 | The app validates the integrity of the platform | ❓ | | planned: red team (jailbreak detection bypass) | | ⏳ | |
| RESILIENCE-2 | The app implements anti-tampering mechanisms | ❓ | | planned: red team (repackaging) | | ⏳ | |
| RESILIENCE-3 | The app implements anti-static analysis mechanisms | ❓ | planned: MobSF (binary analysis) | | | ⏳ | |
| RESILIENCE-4 | The app implements anti-dynamic analysis techniques | ❓ | | planned: red team (Frida detection) | | ⏳ | |

## MASVS-PRIVACY (MAS-P)

| ID | Requirement | Scope | Automated check | Manual check | MASWE / MASTG refs | Status | Issues |
|---|---|---|---|---|---|---|---|
| PRIVACY-1 | The app minimizes access to sensitive data and resources | ❓ | planned: MobSF (declared permissions) | planned: review permissions vs actual need | | ⏳ | |
| PRIVACY-2 | The app prevents identification of the user | ❓ | | planned: review (tracking, device identifiers) | | ⏳ | |
| PRIVACY-3 | The app is transparent about data collection and usage | ❓ | | planned: review (privacy manifest, App Store privacy labels) | | ⏳ | |
| PRIVACY-4 | The app offers user control over their data | ❓ | | planned: review (account / data deletion) | | ⏳ | |

---

## Out of scope & accepted risks

| ID | Decision | Reason | Decided by / date |
|---|---|---|---|
| `<e.g. RESILIENCE-*>` | Out of scope | `<e.g. no business assets worth tampering with; MAS-R not in target profile>` | |

## Coverage summary

| Category | In scope | Verified ✅ | Open ⚠️ | Not covered ⏳ |
|---|---|---|---|---|
| STORAGE | | | | |
| CRYPTO | | | | |
| AUTH | | | | |
| NETWORK | | | | |
| PLATFORM | | | | |
| CODE | | | | |
| RESILIENCE | | | | |
| PRIVACY | | | | |

## Changelog

| Date | Change | Author |
|---|---|---|
| `<YYYY-MM-DD>` | Initial draft | |