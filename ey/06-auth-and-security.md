# API Auth & Security — OAuth2, OIDC, JWT, mTLS, API Keys

> EY GDS — API & Integration Developer (Senior) — 8-hour prep pack, file 06

**What this file buys you:** the JD lists *Authentication and Security (OAuth2, OIDC, JWT, mTLS, API Keys)* as good-to-have, but in an integration role it is the thing every scenario question terminates in — "how does the Logic App authenticate to the downstream API without storing credentials", "how do you secure APIs in APIM", "three consumers with three security profiles, design the policy structure". This file gives you spoken answers with real RFC numbers, real Entra ID claim names, and real APIM policy XML so you can answer at architect level instead of "we use JWT".

**If you only have 35 minutes:** read §1 (grants), §5 (JWT validation checklist + code), §7 (Entra ID), §8 (APIM policies), §13 (the partner-API scenario), and the Rapid Fire.

## Table of Contents

| § | Section | Qs |
|---|---------|-----|
| 1 | [OAuth 2.0 — Roles & Grant Types in 2026](#1-oauth-20--roles--grant-types-in-2026) | Q1–Q10 |
| 2 | [OAuth 2.1, the Security BCP, and What Is Actually Standard](#2-oauth-21-the-security-bcp-and-what-is-actually-standard) | Q11–Q13 |
| 3 | [Scopes, Audience, Resource Indicators](#3-scopes-audience-resource-indicators) | Q14–Q17 |
| 4 | [Introspection, Revocation & Client Authentication](#4-introspection-revocation--client-authentication) | Q18–Q24 |
| 5 | [JWT — Structure, Attacks, and the Validation Checklist](#5-jwt--structure-attacks-and-the-validation-checklist) | Q25–Q33 |
| 6 | [OIDC on Top of OAuth](#6-oidc-on-top-of-oauth) | Q34–Q41 |
| 7 | [Microsoft Entra ID Specifics](#7-microsoft-entra-id-specifics) | Q42–Q52 |
| 8 | [Enforcing It All in Azure APIM](#8-enforcing-it-all-in-azure-apim) | Q53–Q59 |
| 9 | [mTLS](#9-mtls) | Q60–Q66 |
| 10 | [API Keys](#10-api-keys) | Q67–Q70 |
| 11 | [OWASP API Security Top 10 (2023)](#11-owasp-api-security-top-10-2023) | Q71–Q76 |
| 12 | [Platform Security — TLS, CORS, WAF, Secrets, Webhooks, Privacy](#12-platform-security--tls-cors-waf-secrets-webhooks-privacy) | Q77–Q88 |
| 13 | [Zero Trust & The Partner-API Scenario](#13-zero-trust--the-partner-api-scenario) | Q89–Q92 |
| — | [Interviewer Traps](#interviewer-traps) | 12 |
| — | [30-Second Whiteboard Versions](#30-second-whiteboard-versions) | 3 |
| — | [Rapid Fire](#rapid-fire) | 40 |

**Spec numbers you should be able to drop without hesitating**

| RFC | What it is |
|-----|-----------|
| 6749 | OAuth 2.0 Authorization Framework |
| 6750 | Bearer Token Usage |
| 7009 | Token Revocation |
| 7515 / 7516 / 7517 / 7518 / 7519 | JWS / JWE / JWK / JWA / JWT |
| 7523 | JWT profile for client authentication + authorization grants (`private_key_jwt`) |
| 7636 | PKCE |
| 7662 | Token Introspection |
| 8252 | OAuth 2.0 for Native Apps (BCP) |
| 8414 | Authorization Server Metadata (`/.well-known/oauth-authorization-server`) |
| 8628 | Device Authorization Grant |
| 8693 | Token Exchange (Jan 2020) |
| 8705 | Mutual-TLS Client Authentication and Certificate-Bound Access Tokens |
| 8707 | Resource Indicators |
| 9068 | JWT Profile for OAuth 2.0 Access Tokens |
| 9101 | JWT-Secured Authorization Request (JAR) |
| 9126 | Pushed Authorization Requests (PAR) |
| 9207 | `iss` parameter in the authorization response (mix-up defence) |
| 9449 | DPoP — Demonstrating Proof of Possession (Sept 2023) |
| 9700 | Best Current Practice for OAuth 2.0 Security (Jan 2025) |

---

## 1. OAuth 2.0 — Roles & Grant Types in 2026

### Q1. What are the four roles in OAuth 2.0?
`[EASY]`

**Answer:** Four roles, from RFC 6749. **Resource Owner** — the human (or entity) who owns the data. **Client** — the application requesting access on their behalf. **Authorization Server (AS)** — issues tokens after authenticating the resource owner and/or the client; in our world that is Microsoft Entra ID. **Resource Server (RS)** — the API that holds the data and validates the token. In an Azure integration, APIM usually acts as the *policy enforcement point* in front of the resource server, and the backend Function/Logic App is the resource server proper.

The bit interviewers actually listen for: **OAuth is a delegated authorization protocol, not an authentication protocol.** It answers "what may this client do", not "who is this user". OIDC is the layer that answers the second question.

**If they push back — "so is OAuth authentication or authorization?"** — Authorization. Using a raw OAuth access token as proof of identity is the classic mistake that OIDC was created to fix, because the access token's audience is the API, not the client, so a malicious API can replay it. Identity comes from the `id_token`, and only after validating `aud`, `nonce` and signature.

---

### Q2. Walk me through the Authorization Code flow with PKCE. Why is it the default for everything now?
`[MEDIUM]`

**Answer:** The client generates a random `code_verifier` (43–128 chars), hashes it with SHA-256 and base64url-encodes it into `code_challenge`, and sends the user to the authorization endpoint with `code_challenge` + `code_challenge_method=S256`. The user authenticates, the AS redirects back with a short-lived `code`. The client then POSTs that code to the token endpoint **together with the original `code_verifier`**; the AS re-hashes it, compares to what it stored, and only then issues tokens. That binds the code to the client instance that started the flow.

PKCE (RFC 7636) started as a mobile-app fix for the "another app registered the same custom URL scheme and stole the code" attack. It is now the default for **all** clients — including confidential server-side web apps — because RFC 9700 requires public clients to use it and recommends it for confidential clients, and it also blocks authorization-code injection where an attacker plants their own code into your session.

```
GET /authorize
  ?response_type=code
  &client_id=11112222-bbbb-3333-cccc-4444dddd5555
  &redirect_uri=https%3A%2F%2Fapp.contoso.com%2Fcallback
  &scope=openid%20profile%20api%3A%2F%2Forders-api%2FOrders.Read
  &state=Xq7c9F2mNb
  &nonce=7Zk1pQ4wRt
  &code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
  &code_challenge_method=S256
```

Python side, generating the pair correctly:

```python
import base64
import hashlib
import secrets


def make_pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) per RFC 7636 S256."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


if __name__ == "__main__":
    v, c = make_pkce_pair()
    print(len(v), v[:16], c)
```

**If they push back — "the client secret already protects a confidential client, so why PKCE?"** — The secret protects the *token* endpoint. PKCE protects the *authorization code* between the redirect and the token call, which is where code injection and code interception happen. They defend different legs, so you use both. Also `plain` is not acceptable as `code_challenge_method` — always `S256`.

---

### Q3. When is Client Credentials the right grant? Show me the request.
`[EASY-MEDIUM but the single most important one for this role]`

**Answer:** Client Credentials is the machine-to-machine grant: **there is no user**, the client *is* the resource owner, and it authenticates as itself to get an app-only token. Every backend integration — a Logic App calling a partner REST API, a Function draining a Service Bus queue and posting to SAP, APIM calling a downstream service — uses this. In Entra ID the resulting token carries `roles` (application permissions), not `scp`, and has **no** `sub`/user claims worth anything.

```http
POST /{tenant-id}/oauth2/v2.0/token HTTP/1.1
Host: login.microsoftonline.com
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=11112222-bbbb-3333-cccc-4444dddd5555
&scope=api%3A%2F%2Forders-api%2F.default
&client_assertion_type=urn%3Aietf%3Aparams%3Aoauth%3Aclient-assertion-type%3Ajwt-bearer
&client_assertion=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsIng1dCI6Ii4uLiJ9....
```

Python, using MSAL with a certificate (no shared secret on disk):

```python
import msal

TENANT_ID = "aaaabbbb-0000-cccc-1111-dddd2222eeee"
CLIENT_ID = "11112222-bbbb-3333-cccc-4444dddd5555"

app = msal.ConfidentialClientApplication(
    client_id=CLIENT_ID,
    authority=f"https://login.microsoftonline.com/{TENANT_ID}",
    client_credential={
        "private_key": open("/run/secrets/orders-client.key").read(),
        "thumbprint": "AA11BB22CC33DD44EE55FF66AA77BB88CC99DD00",
        "public_certificate": open("/run/secrets/orders-client.pem").read(),
    },
)

# MSAL caches in memory; acquire_for_client checks the cache first.
result = app.acquire_token_for_client(scopes=["api://orders-api/.default"])
if "access_token" not in result:
    raise RuntimeError(f"{result.get('error')}: {result.get('error_description')}")
token = result["access_token"]
```

**If they push back — "why `/.default` and not the individual scope?"** — Because in the client-credentials flow Entra ID does not do incremental consent; `/.default` means "give me every application permission that has already been admin-consented for this resource". Asking for `api://orders-api/Orders.Read` by name in client credentials returns `AADSTS1002012`-family errors. `/.default` is Entra-specific syntax, not part of RFC 6749.

**Better answer if you want to sound senior:** on Azure you do not use client credentials with a secret at all. You use a **managed identity**, which is client credentials with a certificate that the platform mints and rotates for you — see Q47.

---

### Q4. Why is the Implicit grant deprecated?
`[MEDIUM]`

**Answer:** Implicit (`response_type=token`) returned the access token in the URL **fragment** straight from the authorization endpoint. That puts a bearer credential in browser history, in the Referer header, in any JS that reads `location.hash`, and in server logs if a proxy is misconfigured — and there is no client authentication and no PKCE binding, so a code/token injection has nothing stopping it. It also cannot return refresh tokens safely, so SPAs had to do hidden-iframe renewals that third-party-cookie blocking has now killed anyway.

RFC 9700 says clients **SHOULD NOT** use the implicit grant or any response type that issues access tokens from the authorization endpoint. The replacement for SPAs is Authorization Code + PKCE with CORS on the token endpoint, plus refresh token rotation.

**If they push back — "but our SPA still uses implicit"** — Then the migration is: switch `response_type=token` to `code`, add `code_challenge`/`code_verifier`, enable CORS on the token endpoint, and turn on refresh token rotation with a short access token TTL. In Entra ID that is flipping the app registration platform from "implicit grant: access tokens/ID tokens" checkboxes to the SPA platform type, which enables the CORS-enabled token endpoint and rotating refresh tokens.

---

### Q5. Why is ROPC (password grant) forbidden?
`[EASY]`

**Answer:** Resource Owner Password Credentials makes the client collect the user's actual username and password and post them to the token endpoint. That trains users to type corporate credentials into arbitrary apps, gives the client a copy of a long-lived credential, and is structurally incompatible with MFA, Conditional Access, passwordless, federated IdPs and step-up auth — the AS never gets to interact with the user. RFC 9700 is unambiguous: the ROPC grant **MUST NOT** be used.

The only place you still see it is legacy test automation. The correct replacement for that is a dedicated service principal with client credentials, or the Device Authorization Grant for a human-in-the-loop headless case.

**If they push back — "we need it for our automated test suite"** — Use client credentials with a test service principal scoped to a test tenant/data set, or Entra's ROPC is blocked anyway for federated users and any account with MFA. If you truly need a user context, use device code in a one-time bootstrap and cache the refresh token in Key Vault.

---

### Q6. What is the Device Authorization Grant and when do you use it?
`[MEDIUM]`

**Answer:** RFC 8628. For input-constrained devices — a TV, a CLI on a headless VM, a shop-floor scanner. The device POSTs to the *device authorization* endpoint, gets back a `device_code`, a short `user_code` and a `verification_uri`, shows the user "go to microsoft.com/devicelogin and type ABCD-EFGH", then **polls** the token endpoint with `grant_type=urn:ietf:params:oauth:grant-type:device_code` until the user finishes.

The polling contract matters: the AS returns `authorization_pending` while waiting, `slow_down` if you poll faster than the returned `interval`, `expired_token` when the `device_code` TTL passes, and `access_denied` if the user refuses.

```python
import time

import requests

TENANT = "aaaabbbb-0000-cccc-1111-dddd2222eeee"
CLIENT_ID = "11112222-bbbb-3333-cccc-4444dddd5555"
BASE = f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0"

start = requests.post(
    f"{BASE}/devicecode",
    data={"client_id": CLIENT_ID, "scope": "api://orders-api/Orders.Read offline_access"},
    timeout=10,
).json()
print(start["message"])            # "To sign in, use a web browser to open ... and enter CODE"

interval = int(start.get("interval", 5))
deadline = time.monotonic() + int(start["expires_in"])
while time.monotonic() < deadline:
    time.sleep(interval)
    r = requests.post(
        f"{BASE}/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": CLIENT_ID,
            "device_code": start["device_code"],
        },
        timeout=10,
    ).json()
    if "access_token" in r:
        print("got token, expires_in", r["expires_in"])
        break
    if r.get("error") == "slow_down":
        interval += 5
    elif r.get("error") != "authorization_pending":
        raise SystemExit(r)
```

**If they push back — "isn't device code a phishing risk?"** — Yes, device-code phishing is real: the attacker starts the flow and social-engineers a victim into entering *their* code. Mitigations are Conditional Access policies that block device code flow except for named devices/apps, short code TTLs, and user education. Entra ID has a dedicated Conditional Access condition for "Device code flow" under authentication flows.

---

### Q7. Access token vs refresh token — and where do you store them?
`[MEDIUM]`

**Answer:** The **access token** is the credential you present to the API; it is short-lived and should be treated as opaque by the client. The **refresh token** is a long-lived credential you present only to the *authorization server* to get a new access token without user interaction; it never goes to the resource server. In Entra ID an access token's default lifetime is randomised between **60 and 90 minutes** (about 75 on average) deliberately, so that expiry traffic does not spike on the hour; with Continuous Access Evaluation the long-lived variant is 20–28 hours.

Storage: for a browser SPA, **not** localStorage — any XSS reads it. The 2026 answer is a **BFF (backend-for-frontend)**: tokens live server-side, the browser holds only a `Secure; HttpOnly; SameSite=Lax` session cookie, and the BFF attaches the access token when proxying. For a mobile app, the OS keystore/keychain. For a server-side service, in memory with an MSAL token cache — never in a file or an env var that ends up in a container image.

**If they push back — "why not localStorage, it's convenient?"** — Because there is no browser mechanism that stops JavaScript from reading it, so one XSS on any page of your origin equals full token theft and the token keeps working until `exp`. HttpOnly cookies are not readable by JS; the residual risk becomes CSRF, which you handle with SameSite plus an anti-forgery token. Trade one unmitigable risk for one mitigable one.

---

### Q8. Why are refresh tokens rotated, and what does rotation detect?
`[MEDIUM]`

**Answer:** With rotation, every use of a refresh token invalidates it and returns a new one. The point is **theft detection**: if the same refresh token is presented twice, either the legitimate client or an attacker has a stale copy, so the AS revokes the entire token family and forces re-authentication. RFC 9700 requires that refresh tokens for public clients are either sender-constrained (mTLS/DPoP) or rotated.

The operational gotcha is that a network failure between "AS issued new RT" and "client persisted new RT" leaves the client with a dead token. Real implementations give a small grace/reuse window (a few seconds) so a retried request with the previous RT succeeds once rather than nuking the family.

**If they push back — "so how do you actually revoke access mid-session?"** — Refresh rotation only bites at renewal time. For genuine mid-session revocation you need either short access-token TTLs (the access token dies within minutes), a deny-list checked by the RS, or Continuous Access Evaluation, where Entra ID and CAE-aware resources exchange revocation events and the RS challenges the client with a `WWW-Authenticate` claims challenge.

---

### Q9. Opaque access tokens vs self-contained JWT access tokens — trade-off?
`[HARD]`

**Answer:** A **JWT access token** (RFC 9068 defines the standard profile, with `typ: at+jwt`) is self-contained: the resource server validates the signature against JWKS and needs zero network calls, which is why it scales and why an APIM gateway can enforce it at line rate. The cost is that it is a **bearer credential valid until `exp`** — you cannot un-issue it, and every claim you add is claim bloat travelling on every request.

An **opaque/reference token** is a random string; the RS must call the AS's introspection endpoint (RFC 7662) to learn anything. That gives you instant revocation and keeps PII off the wire, at the cost of a network round trip per request (mitigated with a short cache, typically 30–60 s) and a hard dependency on AS availability.

Practical rule: **JWT at the edge for internal/first-party APIs; reference tokens for high-risk or externally-issued tokens where immediate revocation is a compliance requirement.** A common hybrid is *phantom tokens*: the client holds an opaque token, the gateway introspects once and swaps it for a short-lived JWT that it forwards to the backend — you get revocation at the edge and stateless validation behind it.

**If they push back — "how do you revoke a JWT?"** — Three real options, and I would name all three: (1) short TTL — 5–15 minutes — plus refresh rotation, which bounds the damage window and is what 90% of systems actually do; (2) a deny-list keyed on the `jti` claim in Redis with a TTL equal to the token's remaining lifetime, which is cheap because the list only ever holds tokens that have not yet expired; (3) reference tokens/introspection, i.e. don't use a JWT for that surface.

---

### Q10. Give me the grant-type decision table.
`[EASY — but say it fast and you sound fluent]`

| Scenario | Grant | Notes |
|---|---|---|
| Server-side web app with a user | `authorization_code` + PKCE | Confidential client; secret/cert **and** PKCE |
| SPA | `authorization_code` + PKCE | Public client, no secret, rotating RTs, BFF preferred |
| Mobile / desktop | `authorization_code` + PKCE (RFC 8252) | System browser, not an embedded webview; loopback or app-claimed https redirect |
| **Service → service, no user** | **`client_credentials`** | **The integration default. Managed identity on Azure.** |
| CLI on a headless box / smart device | `device_code` (RFC 8628) | Poll, honour `interval` and `slow_down` |
| API A calls API B *as the user* | `urn:ietf:params:oauth:grant-type:jwt-bearer` (Entra OBO) / RFC 8693 token exchange | Preserves user identity down the chain |
| Renewing without the user | `refresh_token` | Rotate; sender-constrain for public clients |
| Anything with a password | ❌ ROPC | RFC 9700: MUST NOT |
| Token straight from `/authorize` | ❌ implicit | RFC 9700: SHOULD NOT |

---

## 2. OAuth 2.1, the Security BCP, and What Is Actually Standard

### Q11. What is OAuth 2.1 and is it final?
`[MEDIUM — accuracy is the whole point of this answer]`

**Answer:** OAuth 2.1 is a **consolidation, not a new protocol**. It folds RFC 6749, RFC 6750, PKCE and the security BCP into one document and removes the parts the community stopped recommending. As of now it is still an **Internet-Draft** — `draft-ietf-oauth-v2-1`, revision 15, dated 2 March 2026 — not an RFC; the working group milestone is to submit it to the IESG around December 2026. So the correct phrasing in an interview is *"OAuth 2.1 is on the standards track but not yet published as an RFC; the normative security requirements it captures are already published as RFC 9700."*

What 2.1 changes versus 2.0:
- PKCE **required** for all clients using the authorization code flow.
- Implicit grant **removed**.
- ROPC (password grant) **removed**.
- Redirect URIs compared by **exact string match**.
- Bearer tokens **must not** be passed in query strings.
- Refresh tokens for public clients must be sender-constrained or one-time-use.

**If they push back — "so should we adopt 2.1 now?"** — You already can, functionally: implement RFC 9700 (published January 2025) and you are OAuth 2.1-compliant in substance. Don't tell a client "we're waiting for 2.1" — the requirements are shipped.

---

### Q12. What does RFC 9700 actually require?
`[HARD — this is the answer that separates you from a candidate reciting a blog post]`

**Answer:** RFC 9700, *Best Current Practice for OAuth 2.0 Security*, January 2025. The normative core:

| Requirement | Strength |
|---|---|
| Public clients use PKCE; AS must support it and enforce `code_verifier` at the token endpoint | MUST / MUST |
| PKCE is RECOMMENDED for confidential clients too | SHOULD |
| AS must mitigate PKCE **downgrade** attacks (attacker strips `code_challenge`) | MUST |
| Redirect URIs matched by exact string comparison (localhost port is the carve-out) | MUST |
| Implicit / any response type issuing tokens at `/authorize` | SHOULD NOT |
| ROPC | MUST NOT |
| Refresh tokens for public clients: sender-constrained **or** rotated | MUST |
| Sender-constraining access tokens via mTLS or DPoP | SHOULD |

The PKCE-downgrade point is the one nobody mentions: if the AS accepts a token request with no `code_verifier` for a code that was issued *with* a `code_challenge`, PKCE is decorative. The defence is that the AS binds the challenge to the code and rejects the token request if the verifier is missing.

**If they push back — "what about mix-up attacks?"** — Two defences: `iss` in the authorization response (RFC 9207) so the client knows which AS answered, and per-AS redirect URIs. Combined with exact redirect matching and `state`, that closes the mix-up family.

---

### Q13. What are PAR and JAR, and would you use them?
`[HARD — only if they go deep, but a two-line answer scores]`

**Answer:** **PAR** (RFC 9126, Pushed Authorization Requests) has the client POST the authorization request parameters to the AS over a **back channel** first, getting back a `request_uri` that it then passes in the front-channel redirect. The browser only ever sees an opaque reference, so parameters can't be tampered with, aren't length-limited by the URL, and are authenticated by the client's credentials. **JAR** (RFC 9101) does something similar by wrapping the request parameters in a signed JWT.

You use them in high-assurance profiles — FAPI 2.0, open banking, anything where a regulator is involved. For a typical enterprise integration on Entra ID they are not required, and Entra ID does not expose a PAR endpoint, so I would not claim we use it.

**If they push back — "why not use them everywhere?"** — Extra round trip, extra client complexity, and no benefit if you already do exact redirect matching + PKCE + `state`. Adopt when the profile demands it (FAPI 2.0 mandates PAR), not by default.

---

## 3. Scopes, Audience, Resource Indicators

### Q14. What is the `scope` parameter for, and how do scopes differ from roles?
`[MEDIUM]`

**Answer:** `scope` is the **delegated permission the user consents to give the client** — "this app may read your orders". It is a space-delimited string, it appears in the token as `scp` in Entra ID (or `scope` in most other ASes), and it is always a *subset* of what the user themselves can do. A scope never grants more than the user has.

Roles (`roles` claim in Entra) are different: either **app roles assigned to a user** (RBAC for humans) or **application permissions** granted to a service principal with admin consent (RBAC for daemons, no user involved). The rule of thumb: `scp` = "the app is acting for a user and may do this"; `roles` = "this principal itself may do this".

**Critical point for API design:** scopes are **coarse-grained authorization about the client**. They are *not* a substitute for object-level authorization. `Orders.Read` says the app may read orders; it does not say it may read *order 4711*. That check is yours — see BOLA in §11.

**If they push back — "how many scopes should an API define?"** — Few and behavioural, not one per endpoint. `Orders.Read`, `Orders.Write`, `Orders.ReadWrite.All` for the admin/daemon case. Dozens of micro-scopes produce consent screens nobody reads and a token bloated with `scp`.

---

### Q15. What is the `aud` claim really for, and what happens if you don't check it?
`[HARD — high-probability question]`

**Answer:** `aud` names the resource the token was minted for. If your API accepts a token whose `aud` is someone else's API, you have a **confused deputy**: a client legitimately obtains a token for API-X, replays it at your API, and your API happily acts on it. Microsoft's own docs call this out explicitly and warn that you must only accept tokens whose `aud` matches one of your own App ID URIs, and that you must never try to validate a Microsoft Graph token — Graph tokens have a proprietary format and are not yours to validate.

So the rule is: **`aud` check is mandatory and must be an allow-list of your own identifiers, never a substring or prefix match.**

```python
# WRONG - accepts api://orders-api-staging, api://orders-api.evil.com
if audience.startswith("api://orders-api"):
    ...

# RIGHT - exact membership in a small allow-list
ALLOWED_AUDIENCES = frozenset({
    "api://orders-api",                         # App ID URI  (v2 tokens)
    "11112222-bbbb-3333-cccc-4444dddd5555",     # client id   (v2 tokens sometimes)
})
if audience not in ALLOWED_AUDIENCES:
    raise PermissionError("bad audience")
```

**If they push back — "our API is behind APIM, does APIM check it?"** — Only if you tell it to. `validate-jwt` does not check audience unless you supply an `<audiences>` element; `validate-azure-ad-token` similarly needs `<audiences>` or `<client-application-ids>`. A `validate-jwt` policy with only an `<openid-config>` element verifies the signature and expiry and lets **every token from that whole tenant** through. That is a real production incident pattern.

---

### Q16. What are Resource Indicators (RFC 8707) and why do they matter for an integration layer?
`[HARD]`

**Answer:** RFC 8707 adds a `resource` parameter to the authorization and token requests so the client can say explicitly *which* protected resource the token is for. The AS then mints a token whose `aud` is that resource and whose scopes are narrowed to what that resource understands. Without it, an AS that supports many APIs may issue one token with a union audience or a generic audience, and that token becomes a skeleton key across your estate.

For an integration platform this matters because one orchestration often touches four downstream APIs. With resource indicators you request four narrowly-scoped tokens instead of one broad one, so a compromised downstream can only replay against itself. It is also the mechanism the MCP authorization spec adopted so an agent's token cannot be replayed against a different MCP server.

```http
POST /oauth2/token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&resource=https%3A%2F%2Forders.contoso.com
&scope=orders.read
&client_id=...&client_assertion_type=...&client_assertion=...
```

**If they push back — "does Entra ID support it?"** — Entra ID's equivalent is baked into scope syntax: you request `api://orders-api/.default` or `https://graph.microsoft.com/.default`, and the resource part of the scope determines `aud`. Entra will refuse to issue one token for two different resources, which achieves the same isolation. So the honest answer is "Entra solves it with resource-qualified scopes rather than the RFC 8707 `resource` parameter."

---

### Q17. Scope vs audience vs role in one sentence each.
`[EASY]`

- **Audience (`aud`)** — *who the token is for*. Wrong audience = reject, no exceptions.
- **Scope (`scp`)** — *what the client was delegated by a user*. Coarse-grained, consent-driven.
- **Role (`roles`)** — *what this principal is*, either a user's app role or an app-only permission. No user consent, admin consent only.
- **And separately:** object-level authorization — *may this principal touch this specific record* — which lives in your code and is in **no** token.

---

## 4. Introspection, Revocation & Client Authentication

### Q18. What is token introspection, and when would you use it instead of validating the JWT locally?
`[MEDIUM-HARD — the trade-off answer, not the definition answer]`

> **Answer:** Introspection is RFC 7662 — the resource server POSTs the token to the authorization server's introspection endpoint and gets back a JSON document whose only required member is `active: true|false`. You use it when you need **real-time revocation** or when the token is opaque and you literally cannot read it. The price is honest and I'd say it out loud: **one network call to the AS on every request**, so you've traded stateless O(1) validation for a hard runtime dependency on the identity provider, and you've made the AS a component in your availability maths.

The request. Note it is **POST** — the spec says a server MAY disallow GET precisely so tokens don't end up in access logs — and the endpoint **MUST require authorization**, normally client authentication:

```http
POST /oauth2/introspect HTTP/1.1
Host: as.contoso.com
Authorization: Basic b3JkZXJzLWFwaTpzM2NyM3Q=
Content-Type: application/x-www-form-urlencoded

token=mF_9.B5f-4.1JqM&token_type_hint=access_token
```

The response, all members after `active` being OPTIONAL:

```json
{
  "active": true,
  "scope": "orders.read orders.write",
  "client_id": "11112222-bbbb-3333-cccc-4444dddd5555",
  "sub": "5f3a...",
  "aud": "api://orders-api",
  "iss": "https://as.contoso.com/",
  "token_type": "Bearer",
  "exp": 1787059200,
  "iat": 1787055600,
  "jti": "d0ab...c91"
}
```

An unknown, malformed, expired or revoked token gets **HTTP 200 with `{"active": false}`** — not a 4xx. That is deliberate: no error taxonomy means no oracle. The spec also says the response for an inactive token SHOULD NOT include any additional information.

**The three things that separate a senior answer here:**

1. **`active: true` is not authorization.** It means "issued by me, not revoked, inside its validity window". You still check `aud`, `iss`, `scope`/roles, and object-level permission yourself — see the checklist in [Q30](#q30-give-me-the-jwt-validation-checklist-the-one-you-would-put-in-a-code-review).
2. **Caching.** RFC 7662 explicitly permits caching "at the cost of liveness" and forbids caching beyond the `exp` in the response. A 30–60 second cache keyed on a hash of the token turns a per-request hop into a per-minute hop and bounds your revocation lag to the cache TTL. Cache the **hash**, never the raw token, so a memory dump or a Redis snapshot isn't a bag of live credentials.
3. **Throttling.** The security considerations call out that an unthrottled introspection endpoint is a token-fishing oracle — an attacker polls candidate token values looking for a 200 with `active: true`. Rate-limit per calling resource server.

**The Azure reality, which is worth saying because it's checkable:** Microsoft Entra ID's v2.0 metadata document at `https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration` contains **no `introspection_endpoint`**, no `revocation_endpoint`, and no `pushed_authorization_request_endpoint`. Entra issues self-contained JWTs and expects local validation against `jwks_uri`. So on an Entra-based integration platform the answer to "do you introspect?" is *no, and here is what we do instead*: short lifetimes, JWKS validation at the APIM edge, and Continuous Access Evaluation for near-real-time revocation.

**If they push back — "so introspection is strictly worse?"** — No. It's the right call in three situations: the token was issued by a **third party** whose signing keys or claim semantics you don't want to couple to; a **regulator** requires that a revoked credential stops working within seconds, which is common in payments and open banking (see [FS](12-financial-services-integration.md)); or the token carries PII you don't want traversing every hop, in which case an opaque token plus introspection keeps the data at the AS. Otherwise, local validation.

---

### Q19. What does RFC 7009 token revocation actually revoke?
`[MEDIUM — the trap is answering "the token" and stopping]`

> **Answer:** RFC 7009 gives the AS a `/revoke` endpoint: the client POSTs `token` plus an optional `token_type_hint` of `access_token` or `refresh_token`. The AS returns **HTTP 200 both when it revoked something and when the token was invalid** — again, no oracle. The important semantics are the cascade: if you revoke a **refresh token**, the AS **SHOULD** also invalidate all access tokens issued from that same authorization grant; if you revoke an **access token**, the AS **MAY** revoke the associated refresh token.

```http
POST /oauth2/revoke HTTP/1.1
Host: as.contoso.com
Authorization: Basic b3JkZXJzLWNsaWVudDpzM2NyM3Q=
Content-Type: application/x-www-form-urlencoded

token=45ghiukldjahdnhzdauz&token_type_hint=refresh_token
```

Errors are the RFC 6749 set plus one: **`unsupported_token_type`** when the AS won't revoke that kind of token. And `503` means "the token still exists, retry" — clients must honour `Retry-After` rather than assuming success.

**The part interviewers are actually testing:** revocation at the AS does not stop a **self-contained JWT** at the resource server. The RS never asks the AS anything, so a revoked-but-unexpired JWT keeps validating until `exp`. The spec itself concedes "there could be a propagation delay" and tells clients not to use the token after a 200. So revocation is a *refresh-time* control unless the RS introspects. That is the single most misunderstood thing in this area.

**Entra ID specifics.** No revocation endpoint. To kill a user's sessions you call Microsoft Graph `POST /users/{id}/revokeSignInSessions`, which invalidates **all refresh tokens issued to applications for that user and their browser session cookies** by stamping `signInSessionsValidFromDateTime`. Microsoft's own note: "there might be a small delay of a few minutes before tokens are revoked", and it does not work for external/B2B users because they sign in at their home tenant. For a **service principal**, there is no equivalent one-shot — you remove the credential (secret or certificate) from the app registration and, if it matters, remove the app role assignment; issued app-only access tokens still live to `exp`.

**If they push back — "then how do you kill access in under a minute?"** — Continuous Access Evaluation. CAE-enabled resources accept long-lived tokens (20–28 hours) but subscribe to critical events — user disabled, password reset, session revoked, risk elevated — and when one fires the resource returns `401` with a `WWW-Authenticate` claims challenge, and the client goes back to Entra for a fresh token that it will not get. It's the standards-shaped version of "the RS asks", pushed rather than polled. If the resource is your own API, the equivalent is a `jti` deny-list in Redis, which I'll cover in [Q32](#q32-why-are-jwts-hard-to-revoke-and-what-do-you-actually-do-about-it).

---

### Q20. Reference tokens or self-contained tokens — and how would you actually build the hybrid?
`[HARD — the platform-engineering answer]`

> **Answer:** The paved-road pattern is the **phantom token**: external clients get an opaque reference token, the gateway introspects it once, caches the result briefly, and forwards a short-lived signed JWT to the backend. External surface gets real-time revocation and leaks no claims; internal services get stateless validation and never learn about the AS. One introspection per request-at-the-edge, zero inside the mesh.

Concretely, on Azure APIM the edge does the swap and the backend only ever sees a JWT it can validate against JWKS. The APIM half, with the introspection result cached so the AS sees roughly one call per token per minute rather than one per request:

```xml
<inbound>
  <base />
  <!-- 1. pull the opaque token -->
  <set-variable name="opaque"
    value="@(context.Request.Headers.GetValueOrDefault("Authorization","").Replace("Bearer ",""))" />

  <!-- 2. cache key is a hash, never the credential itself -->
  <set-variable name="cacheKey"
    value="@(Convert.ToBase64String(System.Security.Cryptography.SHA256.Create()
              .ComputeHash(System.Text.Encoding.UTF8.GetBytes((string)context.Variables["opaque"]))))" />

  <cache-lookup-value key="@("introspect:" + (string)context.Variables["cacheKey"])"
                      variable-name="introspection" caching-type="internal" />

  <choose>
    <when condition="@(!context.Variables.ContainsKey("introspection"))">
      <send-request mode="new" response-variable-name="introspectResponse" timeout="5" ignore-error="false">
        <set-url>https://as.contoso.com/oauth2/introspect</set-url>
        <set-method>POST</set-method>
        <set-header name="Authorization" exists-action="override">
          <value>@("Basic " + Convert.ToBase64String(System.Text.Encoding.UTF8
                    .GetBytes("apim-gateway:" + context.Variables["introspectSecret"])))</value>
        </set-header>
        <set-header name="Content-Type" exists-action="override">
          <value>application/x-www-form-urlencoded</value>
        </set-header>
        <set-body>@("token=" + System.Net.WebUtility.UrlEncode((string)context.Variables["opaque"])
                    + "&amp;token_type_hint=access_token")</set-body>
      </send-request>
      <set-variable name="introspection"
        value="@(((IResponse)context.Variables["introspectResponse"]).Body.As&lt;JObject&gt;().ToString())" />
      <cache-store-value key="@("introspect:" + (string)context.Variables["cacheKey"])"
                         value="@((string)context.Variables["introspection"])"
                         duration="60" caching-type="internal" />
    </when>
  </choose>

  <!-- 3. active:false stops here -->
  <choose>
    <when condition="@(!(bool)JObject.Parse((string)context.Variables["introspection"])["active"])">
      <return-response>
        <set-status code="401" reason="Unauthorized" />
        <set-header name="WWW-Authenticate" exists-action="override">
          <value>Bearer error="invalid_token", error_description="token is not active"</value>
        </set-header>
      </return-response>
    </when>
  </choose>

  <!-- 4. forward identity to the backend as a signed, short-lived internal token -->
  <set-header name="Authorization" exists-action="override">
    <value>@("Bearer " + (string)context.Variables["internalJwt"])</value>
  </set-header>
</inbound>
```

The `internalJwt` is minted by a tiny signer — a Function or a sidecar — with a 60-second `exp`, `aud` set to the specific backend, and the subject/scopes copied from the introspection response. Backends validate it exactly like any other JWT ([Q31](#q31-show-me-the-python-jwks-caching-key-rotation-the-lot)).

| | Self-contained JWT | Reference token + introspection | Phantom token |
|---|---|---|---|
| RS→AS calls per request | 0 | 1 (cacheable ~30–60 s) | 1 at the edge only |
| Revocation lag | up to `exp` | cache TTL | cache TTL at the edge |
| Claims on the wire externally | all of them | none | none |
| AS is on the critical path | no | yes | yes, at one hop |
| Fits APIM/Entra out of the box | yes | no introspection endpoint in Entra | needs a signer component |

**If they push back — "isn't the phantom token just adding a component?"** — Yes, and you only pay for it where the external surface justifies it: partner APIs, open-banking-style consumers, anything where a compliance control says "credential revocation takes effect within N seconds". For first-party internal traffic it's over-engineering; validate the JWT locally and move on.

---

### Q21. What client authentication methods exist at the token endpoint, and which do you pick?
`[MEDIUM — near-certain in an integration interview]`

> **Answer:** Four that matter. `client_secret_basic` puts client id and secret in an HTTP Basic header; `client_secret_post` puts them in the form body. Both are shared secrets and I treat them as the floor, not the target. `private_key_jwt` (RFC 7523) has the client sign a short-lived JWT assertion with a private key that never leaves it, so nothing replayable crosses the wire. `tls_client_auth` / `self_signed_tls_client_auth` (RFC 8705) authenticate the client with a **certificate at the TLS layer**. For a platform I standardise on **workload identity or `private_key_jwt`**, and secrets only where a legacy partner leaves no choice.

Entra ID's own metadata advertises exactly: `client_secret_post`, `private_key_jwt`, `client_secret_basic`, `self_signed_tls_client_auth`.

| Method | Credential | What leaks if TLS/logs leak | Verdict |
|---|---|---|---|
| `client_secret_basic` | shared secret, base64 in a header | the secret, replayable until rotated | acceptable, rotate ≤90 days |
| `client_secret_post` | shared secret, in the body | same, plus more likely in a body-logging proxy | prefer Basic over this |
| `private_key_jwt` | asymmetric key, assertion is single-use-ish | one expiring assertion; the key never moves | **the standards answer** |
| `tls_client_auth` | X.509 + private key | nothing usable at the app layer | best, if you own the PKI |
| Managed identity (Azure) | none — the platform issues it | nothing; there is no credential to leak | **the Azure answer** |

One detail that catches people out: RFC 6749 §2.3.1 requires that for HTTP Basic, `client_id` and `client_secret` are **`application/x-www-form-urlencoded`-percent-encoded first**, then joined with a colon, then base64'd. If the secret contains a `+` or `/` — and Entra's do — naive `base64(id + ":" + secret)` silently fails against a spec-compliant AS.

**`private_key_jwt` for real, against Entra ID.** The assertion's header carries a key hint, the payload proves who you are to the token endpoint, and the whole thing expires in minutes:

```python
import base64
import time
import uuid

import jwt  # PyJWT
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization

TENANT_ID = "aaaabbbb-0000-cccc-1111-dddd2222eeee"
CLIENT_ID = "11112222-bbbb-3333-cccc-4444dddd5555"
TOKEN_ENDPOINT = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def client_assertion(key_pem: bytes, cert_pem: bytes) -> str:
    private_key = serialization.load_pem_private_key(key_pem, password=None)
    cert = x509.load_pem_x509_certificate(cert_pem)
    now = int(time.time())
    return jwt.encode(
        {
            "aud": TOKEN_ENDPOINT,   # exactly the token endpoint, per Entra's docs
            "iss": CLIENT_ID,
            "sub": CLIENT_ID,        # iss == sub is the private_key_jwt signature move
            "jti": str(uuid.uuid4()),
            "nbf": now,
            "iat": now,
            "exp": now + 300,        # Entra guidance: 5-10 minutes after nbf, at most
        },
        private_key,
        algorithm="PS256",           # Entra documents PS256 (RSASSA-PSS) for assertions
        headers={
            "typ": "JWT",
            # base64url SHA-256 thumbprint of the certificate's DER encoding
            "x5t#S256": _b64u(cert.fingerprint(hashes.SHA256())),
        },
    )
```

and the token request that carries it:

```http
POST /aaaabbbb-0000-cccc-1111-dddd2222eeee/oauth2/v2.0/token HTTP/1.1
Host: login.microsoftonline.com
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=11112222-bbbb-3333-cccc-4444dddd5555
&scope=api%3A%2F%2Forders-api%2F.default
&client_assertion_type=urn%3Aietf%3Aparams%3Aoauth%3Aclient-assertion-type%3Ajwt-bearer
&client_assertion=eyJ0eXAiOiJKV1QiLCJhbGciOiJQUzI1NiIsIng1dCNTMjU2IjoiLi4uIn0...
```

In production I'd use MSAL (`ConfidentialClientApplication(client_credential={"private_key": ..., "thumbprint": ..., "public_certificate": ...})`) rather than hand-rolling — it handles the thumbprint format, SNI/`x5c`, and the token cache. Hand-rolling is for the interview whiteboard and for debugging someone else's client.

**If they push back — "we're on Azure, why any of this?"** — Because on Azure the right answer is **no credential at all**: a managed identity for anything running in Azure, and **workload identity federation** for anything outside it — GitHub Actions, an on-prem runner, an EKS pod — where the external OIDC token is exchanged for an Entra token under a federated credential, which is the RFC 7523 §2.1 assertion grant with someone else's IdP as the issuer. `private_key_jwt` is for the cases where neither is possible. That progression — managed identity → federated credential → certificate → secret — is the platform guardrail I'd write into the golden template. See [CI/CD & GitOps](05-cicd-iac-and-gitops.md) for the OIDC-to-Azure pipeline wiring.

---

### Q22. Explain mTLS client authentication and certificate-bound access tokens.
`[HARD]`

> **Answer:** RFC 8705 does two separable things. First, **client authentication**: the client presents an X.509 certificate in the TLS handshake to the token endpoint, and the AS identifies it either by matching an expected subject DN or SAN entry against the registered client — that's `tls_client_auth`, the PKI method — or by matching the certificate itself against the client's registered JWKS — that's `self_signed_tls_client_auth`. Second, and more interesting, **certificate binding**: the AS embeds a thumbprint of that certificate in the issued access token, so the token is no longer a bearer token. Steal it and it's inert without the private key.

Registered client metadata for the PKI method is one of `tls_client_auth_subject_dn`, `tls_client_auth_san_dns`, `tls_client_auth_san_uri`, `tls_client_auth_san_ip`, `tls_client_auth_san_email` — exactly one, so the match is unambiguous. And with mTLS auth the client **MUST** still send the `client_id` parameter, because TLS gives the AS a certificate, not an OAuth identity, and it needs the id to know which client's expectations to check.

The binding lives in the `cnf` (confirmation) claim:

```json
{
  "iss": "https://as.contoso.com/",
  "aud": "api://orders-api",
  "exp": 1787059200,
  "sub": "11112222-bbbb-3333-cccc-4444dddd5555",
  "cnf": {
    "x5t#S256": "bwcK0esc3ACC3DB2Y5_lESsXE8o9ltc05O89jdN-dg2"
  }
}
```

`x5t#S256` is the **base64url-encoded SHA-256 hash of the DER encoding of the X.509 certificate**. Introspection responses carry the same `cnf` structure, so it works for reference tokens too. The token type stays `Bearer` — RFC 8705 doesn't mint a new scheme — which is exactly why the resource-server check is mandatory:

> The protected resource MUST obtain, from its TLS implementation layer, the client certificate used for mutual TLS and MUST verify that the certificate matches the certificate associated with the access token.

In a Python resource server behind a TLS-terminating gateway you don't get the certificate from the socket, you get it from a header the gateway injects — `X-ARR-ClientCert` on Azure App Service/Functions, or whatever your ingress is configured to forward. The comparison:

```python
import base64
import hashlib
import hmac

from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding
from fastapi import HTTPException, Request


def enforce_cert_binding(request: Request, claims: dict) -> None:
    """RFC 8705 §3: the token's cnf.x5t#S256 must match the presenting client cert."""
    confirmation = claims.get("cnf", {}).get("x5t#S256")
    if confirmation is None:
        return  # not a certificate-bound token; policy decides whether that is allowed

    header = request.headers.get("x-arr-clientcert")
    if not header:
        raise HTTPException(401, "certificate-bound token presented without a client certificate")

    cert = x509.load_der_x509_certificate(base64.b64decode(header))
    der = cert.public_bytes(encoding=Encoding.DER)
    thumbprint = base64.urlsafe_b64encode(hashlib.sha256(der).digest()).rstrip(b"=").decode()
    if not hmac.compare_digest(thumbprint, confirmation):
        raise HTTPException(401, "cnf.x5t#S256 does not match the client certificate")
```

Note **`hmac.compare_digest`**, not `==` — constant time whenever you compare anything secret-derived. (`cert.fingerprint(hashes.SHA256())` gives the same bytes in one call; the explicit DER round-trip above is there because the spec defines the hash over the DER encoding and it is worth showing that you know that.)

**If they push back — "isn't this just mTLS, which we already have?"** — No, and the distinction is the whole point. Plain mTLS authenticates the *channel* between two hops. Certificate binding follows the *token* — the token itself records which key may present it, so it survives being handed to a different component and still refuses to work for anyone else. Plain mTLS between A and B says nothing about whether B may replay A's token to C. Deployment reality on Azure: APIM supports client certificates on both the frontend and to the backend, but Entra ID does not issue `cnf`-bound access tokens for general apps, so on an Entra-only estate the honest phrasing is *"we get mTLS at the channel level and sender-constraining is on the roadmap via DPoP or mTLS-bound tokens where the AS supports it"*. More mTLS mechanics in §9.

---

### Q23. What is DPoP and what does proof-of-possession actually buy you over a bearer token?
`[HARD — RFC 9449, September 2023]`

> **Answer:** A bearer token is a password: whoever holds it wins. DPoP — Demonstrating Proof of Possession — binds the token to a key pair the client holds. On every request the client sends an extra `DPoP` header containing a small JWT signed with its private key, covering the HTTP method, the URI, a timestamp, a unique id and a hash of the access token; the token itself carries `cnf.jkt`, the thumbprint of that public key. So a stolen token is useless without the private key, and a captured proof is useless for a different method or URL. It's the application-layer answer to the same problem mTLS solves at the transport layer.

The proof JWT: header `typ: "dpop+jwt"`, an **asymmetric** `alg`, and `jwk` carrying the public key (public parts only). Payload claims:

| Claim | Meaning |
|---|---|
| `jti` | unique id — the server tracks it to stop replay |
| `htm` | the HTTP method of the request being signed |
| `htu` | the target URI, **without** query or fragment |
| `iat` | creation time |
| `ath` | base64url SHA-256 hash of the access token — required when presenting the proof to a resource server |
| `nonce` | server-supplied value, required once the server has issued one |

And the wire format, which is the bit people get wrong — the scheme is **`DPoP`**, not `Bearer`:

```http
GET /orders/4711 HTTP/1.1
Host: api.contoso.com
Authorization: DPoP Kz~8mXK1EalYznwH-LC-1fBAo.4Ljp~zsPE_NeO.gxU
DPoP: eyJ0eXAiOiJkcG9wK2p3dCIsImFsZyI6IkVTMjU2Iiwiandr...
```

Server side, the token's `cnf.jkt` **MUST** be the base64url JWK SHA-256 thumbprint (RFC 7638) of the DPoP public key; the RS recomputes the thumbprint from the `jwk` in the proof header and compares. Failures come back as `WWW-Authenticate: DPoP error="invalid_dpop_proof"` or `error="invalid_token"`. Servers may demand a nonce — they reject with `400` plus a `DPoP-Nonce` response header and `use_dpop_nonce`, and the client retries including it. On lifetime the spec is blunt: accept proofs "for a relatively brief period on the order of seconds or minutes", track `jti` within that window, and tolerate a little clock skew forward.

Client-side proof generation, ES256, no library beyond PyJWT and cryptography:

```python
import base64
import hashlib
import json
import time
import uuid

import jwt
from cryptography.hazmat.primitives.asymmetric import ec

_private_key = ec.generate_private_key(ec.SECP256R1())  # persist this; it is the credential
_numbers = _private_key.public_key().public_numbers()


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


PUBLIC_JWK = {
    "kty": "EC",
    "crv": "P-256",
    "x": _b64u(_numbers.x.to_bytes(32, "big")),
    "y": _b64u(_numbers.y.to_bytes(32, "big")),
}


def jwk_thumbprint(jwk: dict) -> str:
    """RFC 7638: required members only, lexicographic order, no whitespace."""
    canonical = json.dumps(
        {"crv": jwk["crv"], "kty": jwk["kty"], "x": jwk["x"], "y": jwk["y"]},
        separators=(",", ":"),
        sort_keys=True,
    )
    return _b64u(hashlib.sha256(canonical.encode("utf-8")).digest())


def dpop_proof(method: str, url: str, access_token: str | None = None,
               nonce: str | None = None) -> str:
    payload = {
        "jti": str(uuid.uuid4()),
        "htm": method.upper(),
        "htu": url.split("?", 1)[0],          # no query, no fragment
        "iat": int(time.time()),
    }
    if access_token is not None:
        payload["ath"] = _b64u(hashlib.sha256(access_token.encode("ascii")).digest())
    if nonce is not None:
        payload["nonce"] = nonce
    return jwt.encode(
        payload,
        _private_key,
        algorithm="ES256",
        headers={"typ": "dpop+jwt", "jwk": PUBLIC_JWK},
    )


if __name__ == "__main__":
    print("jkt =", jwk_thumbprint(PUBLIC_JWK))
    print(dpop_proof("GET", "https://api.contoso.com/orders/4711", access_token="Kz~8mXK1"))
```

**DPoP vs mTLS-bound tokens, since they solve the same problem:**

| | DPoP (RFC 9449) | mTLS binding (RFC 8705) |
|---|---|---|
| Layer | application — survives TLS-terminating proxies, CDNs, WAFs | transport — breaks if anything terminates TLS and doesn't forward the cert |
| Client burden | generate a key, sign per request | obtain and rotate an X.509 cert |
| PKI needed | none | yes, or self-signed registration |
| Typical fit | SPAs, mobile, public clients | server-to-server, regulated B2B |
| Constrains | access **and** refresh tokens | access **and** refresh tokens |

**If they push back — "does this replace short token lifetimes?"** — No. DPoP removes the *value* of a stolen token; short lifetimes bound the *window*. They compose. RFC 9700 says refresh tokens for public clients MUST be either sender-constrained or rotated, and sender-constrained means precisely DPoP or mTLS. Also: DPoP is not a substitute for TLS — the proof is not an encryption mechanism and `htu`/`ath` are only meaningful over an authenticated channel.

---

### Q24. What is token exchange, and how do you preserve user identity across a chain of services?
`[HARD — RFC 8693, and the Entra OBO equivalent]`

> **Answer:** Token exchange, RFC 8693, is a grant type that lets a service swap one token for another: it presents the caller's token as the `subject_token` and gets back a token for a downstream resource, with the user's identity preserved and the calling service recorded as the **actor**. That is what stops the "gateway calls everything with a god-mode client-credentials token" anti-pattern, where the downstream can no longer tell who the request was really for. In Entra ID the equivalent is the **on-behalf-of flow**, which predates the RFC and uses a `jwt-bearer` grant with `requested_token_use=on_behalf_of`.

The standard request:

```http
POST /oauth2/token HTTP/1.1
Host: as.contoso.com
Content-Type: application/x-www-form-urlencoded

grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Atoken-exchange
&subject_token=eyJhbGciOiJSUzI1NiIsInR5cCI6ImF0K2p3dCJ9...
&subject_token_type=urn%3Aietf%3Aparams%3Aoauth%3Atoken-type%3Aaccess_token
&audience=https%3A%2F%2Fsettlement.contoso.com
&scope=settlement.write
&requested_token_type=urn%3Aietf%3Aparams%3Aoauth%3Atoken-type%3Aaccess_token
```

| Parameter | Required? |
|---|---|
| `grant_type` | REQUIRED — `urn:ietf:params:oauth:grant-type:token-exchange` |
| `subject_token` | REQUIRED — the token representing the party the request is for |
| `subject_token_type` | REQUIRED |
| `resource` / `audience` / `scope` | OPTIONAL — narrow the result to one downstream |
| `requested_token_type` | OPTIONAL |
| `actor_token` | OPTIONAL; `actor_token_type` REQUIRED whenever it is present |

Token type URIs are the `urn:ietf:params:oauth:token-type:` family — `access_token`, `refresh_token`, `id_token`, `saml1`, `saml2`, `jwt`. That `saml2` entry is not decoration: it is how you bridge a modern OAuth caller into a legacy SAML-consuming backend, which is a live problem on ERP and mainframe integrations.

The response **REQUIRES** `access_token`, `issued_token_type` and `token_type`, and there's a wrinkle worth quoting: if the issued token is not an OAuth bearer token, `token_type` is the literal string **`"N_A"`**.

```json
{
  "access_token": "eyJhbGciOiJFUzI1NiIsImtpZCI6IjEyIn0...",
  "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
  "token_type": "Bearer",
  "expires_in": 60
}
```

**Delegation is expressed by the `act` claim**, and it nests — the outermost `act` is the current actor, inner ones are prior actors, so a four-hop chain is auditable from the token alone:

```json
{
  "aud": "https://service26.example.com",
  "iss": "https://issuer.example.com",
  "exp": 1443904100,
  "nbf": 1443904000,
  "sub": "user@example.com",
  "act": {
    "sub": "https://service16.example.com",
    "act": {
      "sub": "https://service77.example.com"
    }
  }
}
```

The mirror-image claim is **`may_act`**, which the AS puts in a subject's token to state that a named party is *authorized to become the actor* for them — that's how you allow an admin or a service to impersonate without giving it a blanket impersonation permission.

**The Entra flavour you will actually type**, because Entra ID does not implement RFC 8693's grant type:

```http
POST /{tenant-id}/oauth2/v2.0/token HTTP/1.1
Host: login.microsoftonline.com
Content-Type: application/x-www-form-urlencoded

grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer
&client_id=11112222-bbbb-3333-cccc-4444dddd5555
&client_assertion_type=urn%3Aietf%3Aparams%3Aoauth%3Aclient-assertion-type%3Ajwt-bearer
&client_assertion=eyJ0eXAiOiJKV1QiLCJhbGciOiJQUzI1NiJ9...
&assertion=<the access token your API received>
&scope=api%3A%2F%2Fsettlement-api%2F.default
&requested_token_use=on_behalf_of
```

The middle-tier API must have been granted delegated permissions on the downstream, and the user (or an admin) must have consented — OBO cannot manufacture permissions the user doesn't have. That is the property you want: the chain can only narrow.

**If they push back — "why not just use client credentials for the internal hops?"** — Because you lose the user. Downstream authorization degrades to "the orchestrator is allowed", every audit trail says "orchestrator", and one compromised middle tier reads every customer's data instead of one customer's. Use client credentials for genuinely system-owned actions — a nightly reconciliation batch, a dead-letter replay — and token exchange or OBO for anything traceable to a person. This is the same argument I'd make for agentic systems in [10-genai-to-integration-bridge.md](10-genai-to-integration-bridge.md): an agent acting for a user must exchange, not impersonate.

---

## 5. JWT — Structure, Attacks, and the Validation Checklist

### Q25. Walk me through the structure of a JWT.
`[EASY — but the two sentences after the obvious answer are what score]`

> **Answer:** Three base64url segments separated by dots: header, payload, signature — that's the JWS Compact Serialization from RFC 7515. The header names the algorithm and the key; the payload is the claims; the signature covers `base64url(header) + "." + base64url(payload)`. The two things people forget: the payload is **signed, not encrypted** — anyone holding the token can read every claim — and a JWT can also be a **JWE**, which has five segments and is encrypted, but almost nothing in the OAuth world uses it.

```
eyJhbGciOiJSUzI1NiIsInR5cCI6ImF0K2p3dCIsImtpZCI6Ik5rSkNRVVUzT1RCQ1EifQ
.
eyJpc3MiOiJodHRwczovL2xvZ2luLm1pY3Jvc29mdG9ubGluZS5jb20vLi4uL3YyLjAiLCJhdWQiOiJhcGk6Ly9vcmRlcnMtYXBpIn0
.
dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk
```

| | JWS (RFC 7515) | JWE (RFC 7516) |
|---|---|---|
| Segments | 3 | 5: header, encrypted key, IV, ciphertext, tag |
| Guarantees | integrity + authenticity | confidentiality + integrity |
| Claims readable by holder | yes | no |
| Used for OAuth access tokens | almost always | rare; used for id_tokens in a few high-assurance profiles |

A "nested JWT" is a JWS wrapped inside a JWE with `cty: "JWT"` on the outer header — sign then encrypt, which is the correct order.

**Two details that mark you as having read the specs, not a blog post.** First, base64url has **no padding and no `+` or `/`** — it uses `-` and `_`. Every "why does my token break in a query string" bug is someone base64'ing instead of base64url'ing. Second, RFC 9068 says a JWT access token's `typ` header **SHOULD be `at+jwt`** and the resource server must **reject a token whose `typ` is something else**. That single check kills the whole class of cross-token-type confusion where an `id_token` is presented as an access token, or a client assertion is replayed at an API.

**If they push back — "so what should never go in a JWT?"** — Anything you would not print on a postcard. No secrets, no full PII payloads, no internal hostnames or connection strings. And nothing that must be current — a JWT is a snapshot of authorization at issue time, so "is this user still an admin" cannot be answered by the token.

---

### Q26. RS256, ES256, HS256, EdDSA — which do you use and why?
`[MEDIUM]`

> **Answer:** For anything crossing a trust boundary, **asymmetric** — the issuer signs with a private key, every verifier holds only the public key from JWKS, so a compromised resource server cannot mint tokens. RS256 is the interoperability default and what Entra ID uses. ES256 is the better modern choice on size and speed. HS256 is symmetric, which means every verifier can forge, so I only use it inside a single service — for example signing a short-lived internal callback URL.

| `alg` | Family | Signature size | Where it belongs |
|---|---|---|---|
| `HS256` | HMAC-SHA256, symmetric | 32 bytes | one service signing for itself; **never** issuer→multiple verifiers |
| `RS256` | RSASSA-PKCS1-v1_5 + SHA-256 | 256 bytes at RSA-2048 | the universal default; Entra's `id_token_signing_alg_values_supported` is exactly `["RS256"]` |
| `PS256` | RSASSA-PSS + SHA-256 | 256 bytes | preferred by FAPI; Entra documents PS256 for **client assertions** |
| `ES256` | ECDSA P-256 + SHA-256 | 64 bytes | smaller tokens, fast verify; needs a good RNG and non-reused nonces |
| `EdDSA` | Ed25519, added to JOSE by RFC 8037 | 64 bytes | cleanest option where both ends support it; deterministic, no RNG footgun |

Practical notes. RSA **verification** is cheap (small public exponent) and RSA **signing** is expensive — which is the right way round, because the AS signs once and thousands of resource servers verify. ECDSA is the reverse-ish and produces tokens roughly 190 bytes shorter, which matters when you're near a header limit ([Q33](#q33-my-tokens-are-getting-huge-and-a-gateway-started-returning-431-what-is-going-on)). ECDSA has a history of catastrophic implementation bugs — **CVE-2022-21449**, the "Psychic Signatures" flaw in Java 15–18, accepted a signature of `r = s = 0` for any message — which is an argument for EdDSA where you have the choice.

**If they push back — "why not just use HS256, it's simpler?"** — Because key distribution is the whole problem. With HS256 every API that validates the token holds the key that mints tokens, so compromising the least-important service in the estate gives you a token factory for the most important one. There's also no rotation story: rotating a shared secret is a coordinated outage across every verifier, whereas rotating an asymmetric key is publishing a new `kid` in JWKS and letting clients pick it up. And HS256 is the vector for algorithm confusion — [Q27](#q27-what-is-the-algnone-attack-and-what-is-algorithm-confusion).

---

### Q27. What is the `alg:none` attack, and what is algorithm confusion?
`[HARD — the single highest-probability security question in this file]`

> **Answer:** Both are the same root cause: **trusting the `alg` value in the attacker-supplied header**. In `alg: none`, the attacker sets the header algorithm to `none`, strips the signature, and a library that reads the header to decide how to verify concludes there's nothing to verify. In algorithm confusion, the attacker takes a valid RS256 token, flips `alg` to `HS256`, and HMAC-signs it using your **RSA public key as the secret** — and your public key is, by definition, public: it's sitting in your JWKS document. The fix for both is one line: **pin the accepted algorithms server-side and ignore the header's claim about itself.**

The confusion attack in full, because being able to describe the mechanics is what separates "I've heard of it" from "I've thought about it":

1. Fetch the issuer's JWKS from `/.well-known/openid-configuration` → `jwks_uri`. Public.
2. Convert the JWK's `n`/`e` to a PEM public key. Deterministic.
3. Take any valid token. Change the header to `{"alg":"HS256","kid":"<the same kid>"}`, and change the payload to whatever you want — `"roles":["Admin"]`, a different `sub`, a later `exp`.
4. HMAC-SHA256 the `header.payload` string using **the exact PEM bytes** as the HMAC key.
5. Present it. A server that does `verify(token, key=public_key_pem)` and derives the algorithm from the header will treat the PEM as an HMAC secret, recompute the same MAC, and accept.

The vulnerable shape, and why PyJWT is not vulnerable by default:

```python
import jwt

# PyJWT >= 2.0 REFUSES this - algorithms is a required argument.
#   jwt.decode(token, key=public_pem)
#   -> DecodeError: It is required that you pass in a value for the "algorithms" argument
#
# These are the two ways people re-introduce the bug by hand:

# 1. reading the algorithm out of the token (the classic)
header = jwt.get_unverified_header(token)
claims = jwt.decode(token, key, algorithms=[header["alg"]])   # BUG: attacker chooses

# 2. an over-broad allowlist that spans families
claims = jwt.decode(token, key, algorithms=["RS256", "HS256"])  # BUG: HS256 is reachable

# CORRECT: one family, pinned, and the key type matches it
claims = jwt.decode(token, public_key, algorithms=["RS256"], audience=AUD, issuer=ISS)
```

`alg: none` has the same shape. PyJWT will only accept it if you explicitly pass `algorithms=["none"]` with `key=None`, which nobody does by accident — but plenty of libraries in other ecosystems did, which is why **CVE-2015-9235** (`node-jsonwebtoken`) is still the canonical citation. The other half of the same family is `options={"verify_signature": False}`, which people add to debug a claim and then commit.

**If they push back — "our library is safe, so why do you care?"** — Because "our library" changes. This is a code-review rule, not a library fact: **the algorithm list is configuration, the `alg` header is untrusted input**, and if the two ever meet in the same expression, that's a finding. I'd add it to the platform's shared auth middleware so no team can get it wrong, plus a Semgrep rule in the pipeline's SAST stage ([CI/CD & GitOps](05-cicd-iac-and-gitops.md)) that flags `algorithms=` derived from anything non-literal.

---

### Q28. What are `kid` injection and `jku`/`x5u` abuse?
`[HARD — the attacks nobody prepares for]`

> **Answer:** The JOSE header has parameters that tell the verifier **where to get the key** — `kid` (a key identifier, RFC 7515 §4.1.4), `jwk` (an embedded public key, §4.1.3), `jku` (a URL to a JWK Set, §4.1.2) and `x5u` (a URL to a certificate, §4.1.5). All four are attacker-controlled. If your verifier obeys them, the attacker supplies their own key and signs their own token. The rule is: **the key source is pinned configuration; the only header parameter you may honour is `kid`, and only as an opaque lookup into keys you already fetched from a URL you chose.**

**`kid` injection.** `kid` is a string that your code uses as a lookup key, so it inherits whatever the lookup is:

| If `kid` is used as… | The attack | Example value |
|---|---|---|
| a filesystem path | path traversal to a file with known contents, then sign with that as the key | `../../../../dev/null` (empty key), `/proc/sys/kernel/randomize_va_space` |
| a SQL parameter | SQL injection returning an attacker-chosen key | `x' UNION SELECT 'attackerkey'--` |
| a shell argument | command injection | `foo; curl evil.com` |
| an index into a fetched JWKS | **nothing — this is the safe design** | `NkJCQUU3OTBCQ` |

**`jku`/`x5u` abuse.** RFC 7515 says only that the resource MUST be retrieved over TLS with server-identity validation — it says nothing about the URL being trustworthy, because the spec assumes the application decides which issuers it trusts. So a verifier that fetches whatever `jku` says will happily fetch `https://attacker.example/jwks.json`, get the attacker's public key, and verify the attacker's signature perfectly. Bypasses of naive allowlists are the usual URL-parsing zoo: open redirect on your own domain, `@` in the userinfo (`https://trusted.com@attacker.com/jwks`), and any host-prefix check (`trusted.com.attacker.com`).

The correct shape, in one sentence: **resolve JWKS from the discovery document of a pinned issuer, cache it, index it by `kid`, and reject any token whose `kid` isn't in that set after one rate-limited refresh.**

```python
ALLOWED_HEADER_PARAMS = {"alg", "typ", "kid"}

header = jwt.get_unverified_header(token)
extra = set(header) - ALLOWED_HEADER_PARAMS
if extra:                      # jku, x5u, jwk, x5c never appear in a token we trust
    raise HTTPException(401, f"unexpected JOSE header parameters: {sorted(extra)}")
```

**If they push back — "APIM validates the JWT, so is this our problem?"** — APIM gets this right by construction: `validate-jwt` takes an `<openid-config url="..."/>` element, i.e. **you** name the discovery document, and the header's `jku` is never consulted. So at the edge you're fine. It becomes your problem the moment a service validates tokens itself with hand-written code, which is exactly why this belongs in one shared, versioned auth library on the paved road rather than in nine repos.

---

### Q29. What are the quiet JWT bugs — the ones that don't look like attacks?
`[MEDIUM-HARD — these are what actually happen in production]`

> **Answer:** Four, and every one of them I'd expect to find in a real codebase. Unverified decode: someone calls decode with signature verification off to "just read the tenant id" and then makes a decision on it. Missing `aud`: the API accepts any token from the tenant, including one minted for a completely different API. Expiry never checked, usually because the validated claims got cached for longer than the token lives. And `nbf`/`iat` skew, where a fleet with drifting clocks rejects perfectly good tokens and someone "fixes" it by disabling time validation entirely.

**1. Unverified decode.** This is the one that hides in helper functions:

```python
# The bug: reads claims from an UNVERIFIED token to route or log, then trusts them.
claims = jwt.decode(token, options={"verify_signature": False})
tenant = claims["tid"]                 # attacker chooses this
db = connect(shard_for(tenant))        # ... and now chooses your shard
```

Unverified decode is legitimate for exactly two things: reading `kid` to select a key, and reading `iss` to select which of several trusted issuers to validate against — and even then only if `iss` is checked against an allowlist before it's used. Nothing from an unverified token may reach a decision, a log field that feeds alerting, or a database.

**2. Missing `aud`.** Covered in Q15; the operational tell is a `validate-jwt` policy with an `<openid-config>` element and no `<audiences>`.

**3. `exp` accepted because nobody checked it.** Two flavours. The library flavour — PyJWT verifies `exp` by default, but `python-jose`, hand-rolled base64 decoders, and anything with `options={"verify_exp": False}` copy-pasted from a unit test do not. And the flavour I've actually seen bite: the **validation result is cached**. If you memoise `validate(token) -> claims` for 15 minutes to save CPU, the token remains accepted for 15 minutes after it expires and, worse, after the user was disabled. Cache keyed on the token, TTL = `min(configured_ttl, exp - now)`, never a flat TTL.

```python
def cache_ttl(claims: dict, ceiling: int = 300) -> int:
    """Never outlive the token you validated."""
    remaining = int(claims["exp"]) - int(time.time())
    return max(0, min(ceiling, remaining))
```

**4. Clock skew.** `nbf` and `exp` are absolute seconds; a container whose clock is 45 seconds fast rejects tokens issued 30 seconds ago with `ImmatureSignatureError`. The fix is `leeway=60` — sixty seconds, not sixty minutes — plus actually running NTP/chrony (or on Azure, the host time sync) and alerting on drift. Never fix skew by disabling time verification.

**If they push back — "what do you return when validation fails?"** — `401` with `WWW-Authenticate: Bearer error="invalid_token", error_description="..."` per RFC 6750, and `403` when the token is valid but the scope or role is insufficient. Keep the description generic externally — "invalid token" — and put the specific reason (expired / bad audience / unknown kid) in the log with a correlation id. Telling an attacker *which* check failed is free reconnaissance.

---

### Q30. Give me the JWT validation checklist — the one you would put in a code review.
`[MEDIUM — memorise this; it is a recitable list and it lands]`

> **Answer:** Ten steps, in order, and I'd have this as a shared library rather than per-service code. One through six are the token; seven and eight are the client's authorization; nine and ten are the ones nobody has in a token at all.

1. **Parse the header only** — read `kid` and `alg` for routing. Nothing from the payload is trusted yet.
2. **Reject unexpected header parameters** — `jku`, `x5u`, `jwk`, `x5c` in an incoming access token mean someone is trying to choose your key.
3. **Select the key by `kid` from JWKS**, fetched from the `jwks_uri` in the **pinned issuer's** discovery document, cached, with one rate-limited refresh on an unknown `kid` for key rotation.
4. **Verify the signature with a pinned algorithm allowlist** — `algorithms=["RS256"]` — never the token's own `alg`. This is [Q27](#q27-what-is-the-algnone-attack-and-what-is-algorithm-confusion).
5. **`iss`** — exact string match against the expected issuer, including the trailing `/v2.0` on Entra v2 tokens. A prefix match is not a match.
6. **`aud`** — exact membership in a small allow-list of your own identifiers. And **`typ`** — reject anything that isn't `at+jwt`/`JWT` as your profile expects (RFC 9068).
7. **`exp` and `nbf`** — with ≤60 seconds of leeway, and `require` them so a token that simply omits `exp` is rejected rather than treated as eternal.
8. **Scopes and roles** — `scp` for delegated, `roles` for app permissions; check the specific one this endpoint needs, and return `403`, not `401`, when it's missing.
9. **Object-level authorization** — may *this* principal touch *this* record? The token says `Orders.Read`; it does not say "order 4711 belongs to this customer". This check is in **no token**, ever, and it is OWASP API #1 (BOLA).
10. **Log the decision** — `sub`/`oid`, `client_id`/`appid`, `jti`, the endpoint, and allow/deny, with a correlation id. Never log the token.

Steps 1–7 are mechanical and belong in middleware or the gateway. Steps 8–9 are business logic and cannot be delegated to APIM. Step 10 is what makes an incident investigable.

**If they push back — "APIM already does 1–8, why repeat it in the service?"** — Defence in depth, and specifically: because the pod is reachable from inside the VNet, from a misconfigured private endpoint, or from another service that was compromised. But I'd state the trade-off rather than dogma: if APIM is provably the only ingress — private-endpoint-only backend, network policy denying east-west — then validating fully at the edge and re-checking only steps 8–9 in the service is a defensible engineering decision, and I'd write that decision down in the runbook so the next person knows it was a choice.

---

### Q31. Show me the Python. JWKS caching, key rotation, the lot.
`[MEDIUM — expect to type this]`

> **Answer:** PyJWT's `PyJWKClient` already does the hard parts: it caches the JWK Set and, if a `kid` isn't in the cached set, it refreshes from the endpoint and retries the lookup **once** — which is exactly the key-rotation behaviour you want, and exactly the thing people re-implement badly. I wire it into a FastAPI dependency, pin the algorithm, and warm it at startup so the first real request doesn't pay for the JWKS fetch.

```python
"""Production-shaped JWT validation for a FastAPI resource server. PyJWT >= 2.10."""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Annotated, Any

import httpx
import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

log = logging.getLogger("auth")

TENANT_ID = "aaaabbbb-0000-cccc-1111-dddd2222eeee"
ISSUER = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
AUDIENCES = frozenset({"api://orders-api"})
ALGORITHMS = ["RS256"]                       # pinned; the token's alg header is ignored
DISCOVERY = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration"
ALLOWED_HEADER_PARAMS = {"alg", "typ", "kid", "x5t"}

bearer = HTTPBearer(auto_error=True)


@lru_cache(maxsize=1)
def jwks_client() -> PyJWKClient:
    """Discovery once, then a caching JWKS client.

    PyJWKClient defaults: cache_jwk_set=True, lifespan=300 s, max_cached_keys=16,
    cache_keys=False, timeout=30 s. get_signing_key() refreshes the set and retries
    once when the kid is unknown - that is the key-rotation path.
    """
    metadata = httpx.get(DISCOVERY, timeout=10.0).raise_for_status().json()
    if metadata["issuer"] != ISSUER:
        raise RuntimeError(f"issuer mismatch: {metadata['issuer']!r} != {ISSUER!r}")
    return PyJWKClient(metadata["jwks_uri"], cache_jwk_set=True, lifespan=300, timeout=10)


def _reject(detail: str, *, code: int = status.HTTP_401_UNAUTHORIZED) -> HTTPException:
    headers = ({"WWW-Authenticate": 'Bearer error="invalid_token"'}
               if code == status.HTTP_401_UNAUTHORIZED else None)
    return HTTPException(status_code=code, detail=detail, headers=headers)


def validate(token: str) -> dict[str, Any]:
    # 1-2. header only, and no key-sourcing parameters allowed
    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError as exc:
        raise _reject("malformed token") from exc
    unexpected = set(header) - ALLOWED_HEADER_PARAMS
    if unexpected:
        log.warning("rejected token with header params %s", sorted(unexpected))
        raise _reject("invalid token")
    if header.get("alg") not in ALGORITHMS:
        raise _reject("invalid token")           # blocks alg:none and HS/RS confusion early

    # 3. key by kid, with the rotation refresh handled inside PyJWKClient
    try:
        signing_key = jwks_client().get_signing_key_from_jwt(token)
    except jwt.exceptions.PyJWKClientError as exc:
        log.warning("no signing key for kid=%s: %s", header.get("kid"), exc)
        raise _reject("invalid token") from exc

    # 4-7. signature, iss, aud, exp, nbf - all enforced, none optional
    try:
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=ALGORITHMS,               # allowlist beats the header, always
            audience=list(AUDIENCES),
            issuer=ISSUER,
            leeway=60,                           # seconds of clock skew, not minutes
            options={
                "require": ["exp", "iat", "nbf", "iss", "aud", "sub"],
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iss": True,
                "verify_aud": True,
            },
        )
    except jwt.ExpiredSignatureError as exc:
        raise _reject("token expired") from exc
    except jwt.InvalidTokenError as exc:
        log.info("token rejected: %s", exc)      # specific reason to the log, not the caller
        raise _reject("invalid token") from exc


async def principal(
    request: Request,
    creds: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
) -> dict[str, Any]:
    claims = validate(creds.credentials)
    request.state.principal = claims
    return claims


def require(*required: str):
    """8. Scope/role gate. 403, not 401 - the token was fine, the permission was not."""
    wanted = frozenset(required)

    def dependency(claims: Annotated[dict[str, Any], Depends(principal)]) -> dict[str, Any]:
        granted = set(claims.get("scp", "").split()) | set(claims.get("roles", []))
        if not wanted & granted:
            raise _reject(f"requires one of {sorted(wanted)}", code=status.HTTP_403_FORBIDDEN)
        return claims

    return dependency


@asynccontextmanager
async def lifespan(_: FastAPI):
    started = time.perf_counter()
    jwks_client().get_jwk_set()                  # pay the fetch before traffic arrives
    log.info("jwks warmed in %.0f ms", (time.perf_counter() - started) * 1000)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/orders/{order_id}")
def get_order(order_id: str, claims: Annotated[dict, Depends(require("Orders.Read"))]):
    order = load_order(order_id)
    # 9. OBJECT-LEVEL AUTHORIZATION. In no token. Yours to write. Every time.
    if order.customer_id != claims.get("extension_customerId"):
        raise _reject("not found", code=status.HTTP_404_NOT_FOUND)
    return order
```

Three things to say while you type it. **The `/orders/{order_id}` handler returns 404, not 403**, on an object-level failure — a 403 confirms the record exists, which is an enumeration oracle. **`get_signing_key_from_jwt` handles rotation** so you don't need a bespoke cache; you only write your own (as in [07-python-for-integration-and-coding-round.md](07-python-for-integration-and-coding-round.md)) when you need async I/O or a single-flight cooldown to stop a thundering herd hammering the JWKS endpoint during a rotation. **Cost after warm-up is one RSA verification** — tens of microseconds — and zero network calls, which is the entire argument for self-contained tokens.

**If they push back — "what happens the moment the IdP rotates its signing key?"** — Entra publishes the new key in JWKS **before** it starts signing with it, so a client with a 5-minute cache picks it up in the normal refresh. The unknown-`kid` path is the belt and braces: first token with the new `kid` triggers one refresh, subsequent tokens hit cache. The failure mode to guard is a token with a genuinely bogus `kid` triggering a JWKS fetch per request — that's a free DoS amplifier against your IdP — so rate-limit the forced refresh (PyJWT's client refreshes at most once per lookup; add a cooldown if you're exposed to untrusted traffic).

---

### Q32. Why are JWTs hard to revoke, and what do you actually do about it?
`[HARD — you will get asked this; have the incident answer, not just the theory]`

> **Answer:** Because the whole design goal is that the resource server never asks anyone. Validation is a signature check against a public key, so there is no moment at which the RS could learn that the AS changed its mind. A JWT is valid until `exp`, full stop. There are exactly three real mitigations and I'd name all three: short lifetimes, a `jti` deny-list, or don't use a JWT on that surface. Everything else is one of those three wearing a hat.

| Mitigation | Revocation lag | Cost | When |
|---|---|---|---|
| Short `exp` + refresh rotation | up to the TTL (5–15 min) | more token-endpoint traffic | the default; ~90% of systems |
| `jti` deny-list in Redis | seconds | one lookup per request | high-value surfaces, incident response |
| Reference token + introspection | seconds | a network hop per request (cacheable) | regulated / external surfaces |
| Rotate the signing key | seconds — but it invalidates **everything** | full re-auth for every client | the break-glass option only |

The deny-list is the one people dismiss as "that makes it stateful", which misreads the maths. **You only store tokens that were revoked and have not yet expired.** With a 15-minute TTL, even a mass revocation of 100,000 sessions is 100,000 short Redis keys that self-delete — a few megabytes, not a token database:

```python
import redis

r = redis.Redis(host="cache.contoso.privatelink.redis.cache.windows.net", ssl=True)


def revoke(claims: dict) -> None:
    """Deny-list a single token until its natural expiry, then it evaporates."""
    ttl = int(claims["exp"]) - int(time.time())
    if ttl > 0:
        r.setex(f"revoked:{claims['jti']}", ttl, "1")


def is_revoked(claims: dict) -> bool:
    return r.exists(f"revoked:{claims['jti']}") == 1
```

The honest cost is a Redis round trip on every request, ~0.3 ms in-region, plus a **fail-open or fail-closed decision** when Redis is down that you must make deliberately and write in the runbook. My default: fail **closed** for money-moving endpoints, fail **open** with a loud alert for read-only ones — and say that out loud, because "what happens when the deny-list is unavailable" is the follow-up question.

For a **whole-principal** kill rather than a single token, deny-list by subject with a timestamp instead: store `revoked_before:{oid} = now`, and reject any token whose `iat` predates it. One key per user, and it covers every token they hold. That is the same mechanism Entra's `signInSessionsValidFromDateTime` implements centrally.

**The incident answer, which is what a techno-managerial interviewer is listening for.** A token leaks at 14:00. Order of operations: (1) deny-list the `jti` and, if it's a user, the subject — seconds; (2) revoke the refresh tokens at the AS so it cannot be renewed — `revokeSignInSessions` for a user, remove the credential for a service principal; (3) rotate the client's credential; (4) check the logs for what that `jti` did between issue and revocation, which only works if step 10 of the checklist was implemented; (5) only if the blast radius is unknown, rotate the signing key — and know that this logs out the entire estate, so it's a declared incident with comms, not an engineer's unilateral call.

**If they push back — "why not just make tokens 60 seconds long?"** — Because you move the load and the failure mode rather than removing them: the token endpoint now takes your entire request rate, an AS outage becomes a total outage in 60 seconds instead of degrading gracefully over an hour, and clock skew across the fleet starts rejecting legitimate traffic. 5–15 minutes is the industry sweet spot; Entra's own access-token default is deliberately randomised between **60 and 90 minutes** so that expiries don't stampede on the hour.

---

### Q33. My tokens are getting huge and a gateway started returning 431. What is going on?
`[MEDIUM — a real operational failure, and a great answer to have ready]`

> **Answer:** Claims bloat. Someone turned on the `groups` claim, the user is in 300 Entra groups, and each group is a 36-character GUID — so the payload alone is over 10 KB, base64url inflates it by a third, and the `Authorization` header blows past the gateway's header buffer. The failure is nasty because it's **per-user**: it works for everyone in the test tenant and fails for the one director who sits in every distribution list.

**The limits you're hitting**, all defaults from the vendors' own docs:

| Component | Directive / flag | Default |
|---|---|---|
| nginx | `large_client_header_buffers` | `4 8k` — one header line may not exceed 8 KB |
| nginx | `client_header_buffer_size` | `1k` |
| Apache httpd | `LimitRequestFieldSize` | `8190` bytes |
| Apache httpd | `LimitRequestFields` | `100` headers |
| Node.js | `--max-http-header-size` | 16 KiB (raised from 8 KiB in v13.13.0) |

Base64url costs you **4 bytes for every 3**, so a 6 KB claim set becomes an 8 KB token, plus `Authorization: Bearer ` and everything else in the request — and you're over nginx's 8 KB line limit. HTTP/2 HPACK helps on repeat requests but not on the first, and not at all if an intermediary re-expands the headers.

**Entra ID already anticipates this**, and the numbers are worth knowing exactly: if a user is a member of more groups than the overage limit — **150 for SAML tokens, 200 for JWTs** — Entra omits the `groups` claim entirely and emits an overage claim instead:

```json
{
  "_claim_names": { "groups": "src1" },
  "_claim_sources": {
    "src1": {
      "endpoint": "https://graph.microsoft.com/v1.0/users/{userID}/getMemberObjects"
    }
  }
}
```

There's also a `hasgroups: true` boolean for the length-limited cases. Either way your application has to go and ask Graph — which means a token-size problem silently becomes a **latency and Graph-throttling** problem in production, on exactly the accounts belonging to your most senior users.

**The fixes, in the order I'd apply them:**

1. **Don't put groups in the token.** Use **app roles** instead — a handful of short, app-specific strings in `roles` (`Orders.Approver`) rather than hundreds of tenant-wide GUIDs. This is the correct answer, not a workaround: group membership is a directory fact, application permission is an application fact.
2. **If you must have groups, filter them.** Entra's optional-claims configuration can emit only *groups assigned to this application* rather than all of them.
3. **Look entitlements up server-side**, keyed on the stable `oid`, from your own store with a short cache. Keeps the token small and lets you change permissions without waiting for token expiry.
4. **Move bulk context out of the header** — into the request body or a server-side session keyed by `jti`. Nothing in a JWT should be there because it was convenient.
5. **Raise the buffer only as a stopgap** (`large_client_header_buffers 8 16k`) and treat it as a ticket, not a fix — you will hit the next limit at the next hop, and some of those hops are managed services you cannot configure.

**If they push back — "what's the practical ceiling on a token?"** — I'd design for **under 4 KB** and alert at 6 KB, because 8 KB is where the common defaults live and you have no idea how many proxies are between the client and you. It's also worth watching in metrics: emit token size as a histogram in the auth middleware, and you'll see the bloat trend months before the first 431.

---

## 6. OIDC on Top of OAuth

### Q34. What does OpenID Connect actually add on top of OAuth 2.0?
`[MEDIUM]`

> OIDC is a thin identity layer on top of OAuth 2.0. OAuth gives you an access token that says *what a client may do*; OIDC adds an `id_token` — a signed JWT about *who the user is*, minted for the client — plus a standard set of claims, a standard discovery document, and a UserInfo endpoint. Practically it turns five vendor-specific "login with X" integrations into one protocol you can point at Entra ID, Okta, Ping or a partner's IdP with a config change.

What OAuth 2.0 deliberately leaves undefined, and OIDC pins down:

| Gap in plain OAuth 2.0 | What OIDC defines |
|---|---|
| No token about the user for the client | `id_token`, a JWT signed by the OP, `aud` = client_id |
| No standard user claims | `sub`, `name`, `preferred_username`, `email`, `email_verified`, `given_name`, `family_name`, `picture`, `updated_at` |
| No standard way to find endpoints | Discovery 1.0 — `/.well-known/openid-configuration` |
| No standard key distribution | `jwks_uri` in the discovery doc (JWK Set, RFC 7517) |
| No replay defence on the identity assertion | `nonce`, echoed into the `id_token` |
| No standard "who is this token for" endpoint for clients | UserInfo endpoint |
| No standard logout | RP-Initiated Logout 1.0, Front-Channel Logout 1.0, Back-Channel Logout 1.0 — all Final |
| No standard "give me a refresh token" signal | `offline_access` scope |

The trigger is the scope: **a request is an OIDC request if and only if `scope` contains `openid`.** Everything else — `profile`, `email`, `offline_access` — is additive. Entra ID does not support the `address` and `phone` OIDC scopes.

**If they push back — "so can I just use OAuth for login?"** — No, and that is the exact hole OIDC was written to close. A bare OAuth access token is issued *to a client, for an API*. If the API treats "I received a valid token" as proof of the user's identity, any other API that legitimately received a token from the same user can replay it and impersonate them. OIDC fixes this by making the identity assertion audience-bound to the client and nonce-bound to that specific login attempt.

---

### Q35. What is the difference between an `id_token` and an `access_token`, and what happens if a client sends me an `id_token` as a bearer token?
`[HARD — the single most common auth mistake in enterprise integration; expect it]`

> The `id_token` is for the client, the `access_token` is for the API. The `id_token`'s audience is the client ID, it carries no scopes, and it is a statement about a login event — so if a caller presents an `id_token` at my API, I reject it with a 401, every time. Accepting one is an authentication bypass: any app in the tenant can get an `id_token` for its own users and would then be able to drive my API.

| | `id_token` | `access_token` |
|---|---|---|
| Audience (`aud`) | The **client** (`client_id`) | The **API** (resource) |
| Consumed by | The client, once, at login | The resource server, on every call |
| Carries authorization | No — no `scp`, no `roles` | Yes — `scp` and/or `roles` |
| Format | Always a JWT (spec-mandated) | JWT or opaque — the API's choice |
| Replay defence | `nonce` | `aud` + short lifetime (+ DPoP/mTLS if sender-constrained) |
| Lifetime in Entra ID | 1 hour default | variable, 60–90 minutes (75 avg) |
| Should the client parse it? | Yes, that is its purpose | No — treat as an opaque string |

Why it happens in real projects: a frontend team wires up MSAL, sees two JWTs come back, and puts the wrong one in the `Authorization` header. It *works* against a naive API that only verifies the signature and issuer — which is precisely why the audience check is non-negotiable (see §3). In Entra ID both tokens are signed by the same tenant keys, so signature validation alone will not save you.

Two concrete rejection rules to state out loud:

```python
# In the resource server. Both checks are cheap and both are mandatory.

def reject_id_tokens(claims: dict, my_api_client_id: str) -> None:
    # 1. Audience must be THIS API. An id_token's aud is the calling client's id.
    if claims.get("aud") != my_api_client_id:
        raise PermissionError("token was not minted for this API")

    # 2. Belt and braces: an id_token carries neither scp nor roles.
    #    A genuine Entra access token always carries at least one.
    if "scp" not in claims and "roles" not in claims:
        raise PermissionError("token carries no authorization claims - looks like an id_token")
```

Rule 2 is a heuristic, rule 1 is the real defence. Also note the mirror-image mistake: the *client* must not crack open the access token to render "Hello, Priya". Microsoft's own guidance is explicit — clients must treat access tokens as opaque strings, and tokens for Microsoft-owned APIs may not even be parseable JWTs.

**If they push back — "our SPA needs the user's name, and only the access token is available"** — Then the SPA is holding the wrong artefact. Request `openid profile` so MSAL hands back an `id_token` and read the name from there, or call `/oidc/userinfo`. Never read the access token, and never send the `id_token` onward as authorization to the API — if the API genuinely needs user identity it gets it from the *access* token's `oid`/`sub`/`preferred_username`, which Entra puts there when the token is delegated.

---

### Q36. Walk me through the discovery document and JWKS. How do you handle signing key rotation?
`[MEDIUM-HARD — very likely, because it is the thing that breaks at 3am]`

> Every OIDC provider publishes a metadata document at `{issuer}/.well-known/openid-configuration`. I read `issuer`, `jwks_uri`, `token_endpoint` and `end_session_endpoint` from it rather than hardcoding URLs, then fetch the JWK Set from `jwks_uri` and pick the key by the token header's `kid`. For rotation, I cache the JWK Set with a TTL and refresh on an unknown `kid` — with a cooldown so a garbage token cannot turn into a JWKS stampede against the IdP.

The Entra ID metadata endpoints you must be able to recite:

| Purpose | URL |
|---|---|
| v2.0 discovery | `https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration` |
| v1.0 discovery | `https://login.microsoftonline.com/{tenant}/.well-known/openid-configuration` |
| v2.0 JWKS | `https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys` |
| Logout | `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/logout` |
| UserInfo | `https://graph.microsoft.com/oidc/userinfo` (hosted on Graph, not on login.microsoftonline.com) |

`{tenant}` is a tenant GUID, a verified domain, or `common` / `organizations` / `consumers`.

**The version trap:** you must read the metadata document that matches the *token's* `ver` claim, not the authority your app was configured with. A v1.0 token (`ver: 1.0`, `iss` ending `sts.windows.net/{tid}/`) is validated against the v1.0 metadata document; a v2.0 token (`ver: 2.0`, `iss` ending `/v2.0`) against the v2.0 one. Microsoft calls this out explicitly.

Key rotation, done properly:

```python
"""JWKS cache with kid-driven refresh and a cooldown. Stdlib + httpx only."""
import threading
import time

import httpx

DISCOVERY_TTL = 24 * 3600      # MS guidance: re-check signing keys about every 24h
REFRESH_COOLDOWN = 300         # never re-fetch JWKS more than once per 5 min


class JwksCache:
    def __init__(self, discovery_url: str) -> None:
        self._discovery_url = discovery_url
        self._lock = threading.Lock()
        self._keys: dict[str, dict] = {}
        self._issuer: str | None = None
        self._loaded_at = 0.0
        self._last_refresh_attempt = 0.0

    def _load(self) -> None:
        with httpx.Client(timeout=10.0) as client:
            meta = client.get(self._discovery_url).raise_for_status().json()
            jwks = client.get(meta["jwks_uri"]).raise_for_status().json()
        self._issuer = meta["issuer"]
        self._keys = {k["kid"]: k for k in jwks["keys"] if "kid" in k}
        self._loaded_at = time.monotonic()

    @property
    def issuer(self) -> str:
        self.key_for("")  # force an initial load
        return self._issuer or ""

    def key_for(self, kid: str) -> dict | None:
        with self._lock:
            now = time.monotonic()
            stale = now - self._loaded_at > DISCOVERY_TTL
            unknown = kid not in self._keys
            cooled = now - self._last_refresh_attempt > REFRESH_COOLDOWN
            if not self._keys or stale or (unknown and cooled):
                self._last_refresh_attempt = now
                self._load()
            return self._keys.get(kid)
```

Four rules that come out of this:

1. **Never pin a single key or a certificate thumbprint.** Entra rotates its signing keys on its own schedule and does not announce each rotation; a pinned key is a scheduled outage.
2. **Never fetch JWKS per request.** That is a self-inflicted DoS on the IdP and adds latency to every call. Cache it.
3. **Refresh on unknown `kid`, with a cooldown.** Without the cooldown an attacker sends 10k tokens with random `kid`s and you hammer `login.microsoftonline.com` until you are throttled.
4. **Fail closed on a JWKS fetch failure** if you have no usable cached key — do not fall back to "skip signature verification". That is CVE material.

**If they push back — "what about custom signing keys?"** — If an app uses the claims-mapping feature it gets its own signing keys, and you must fetch the metadata with the `appid` query parameter: `…/.well-known/openid-configuration?appid={client-id}`, which returns a `jwks_uri` of `…/discovery/keys?appid={client-id}`. Standard libraries do not do this for you.

---

### Q37. `nonce` versus `state` — what is the difference?
`[MEDIUM — candidates blur these constantly; being precise here is a differentiator]`

> They defend different things at different layers. `state` is an OAuth parameter that protects the *redirect*: it binds the callback to the browser session that started it, which is CSRF defence, and it never appears inside a token. `nonce` is an OIDC parameter that protects the *`id_token`*: the client generates it, the OP copies it verbatim into the token, and the client compares — which is replay defence for the identity assertion.

| | `state` | `nonce` |
|---|---|---|
| Defined by | OAuth 2.0 (RFC 6749) | OIDC Core 1.0 |
| Attack stopped | CSRF / session fixation on the callback | Replay of a previously issued `id_token` |
| Travels | Request → callback (never in the token) | Request → **inside the `id_token`** |
| Bound to | The user agent, ideally via a cookie or a value derived from one | The specific login attempt |
| Checked by | The client, comparing callback value to stored value | The client, comparing `id_token.nonce` to stored value |
| Required by Entra ID | Recommended | **Required** when requesting an `id_token` |

Two things worth adding, because they show you understand where each stops:

- `state` also carries app state — "the user was on `/orders/4711` when we bounced them to login". Do not put URLs or sensitive data in `state` directly; store them under a key in session storage and put the key in `state`. Otherwise you have built an open redirect and a data leak in one parameter.
- `state` does **not** stop authorization-code injection — an attacker planting a code they obtained into your legitimate session. That is what PKCE is for (see §1). So the modern set is `state` + `nonce` + PKCE, all three, and RFC 9207's `iss` on top for mix-up.

```python
import secrets

state = secrets.token_urlsafe(32)     # store server-side / in an httpOnly cookie
nonce = secrets.token_urlsafe(32)     # store alongside; compare against id_token.nonce
```

**If they push back — "PKCE is there, do I still need `state`?"** — Yes. PKCE binds the code to the client instance; it does not tell your app whether the callback belongs to the browser session that started it, and it does not stop a forced-login CSRF where the attacker logs the victim into the attacker's account. RFC 9700 lets PKCE substitute for `state` as *CSRF protection* specifically, but `state` remains the only mechanism carrying your own app state, so in practice you send both.

---

### Q38. When do you actually need the UserInfo endpoint?
`[MEDIUM]`

> Usually you do not. If the claims you need are already in the `id_token`, calling UserInfo is a wasted network hop on every login. You need it when the claim set is too big for a token, when you need fresher data than the token was minted with, when the OP issues opaque access tokens, or — with Entra ID — when you want profile data without configuring optional claims on the app registration.

Mechanics: UserInfo is an OAuth-protected resource. You call it with the **access token** issued for the `openid` scope (plus `profile`/`email` if you want those claims), and it returns a JSON claim set. The response can also be a signed and/or encrypted JWT, in which case the content type is `application/jwt`.

**The security rule people forget** — OIDC Core §5.3.2: *"The sub Claim in the UserInfo Response MUST be verified to exactly match the sub Claim in the ID Token; if they do not match, the UserInfo Response values MUST NOT be used."* Without that check, a token-substitution attack lets one user's profile be attached to another user's session.

On Entra ID specifically:

- The endpoint is `https://graph.microsoft.com/oidc/userinfo` — it lives on **Microsoft Graph**, not on the login host. So the access token you use is a Graph token, and you must not attempt to validate it yourself.
- It returns a small set — `sub`, and `name` / `family_name` / `given_name` / `picture` with `profile`, `email` with `email`. For anything richer you call Graph proper (`/me`), which is a different permission conversation.

**If they push back — "why not just call it on every request?"** — Because it is a synchronous dependency on the IdP inside your request path. If Graph is slow, your API is slow; if Graph is down, your API is down; and it burns throttling budget. Claims belong in the token, resolved once at login, refreshed at token refresh. If a claim is too volatile for that — group membership on a user who changes teams — do not put it in the token at all: look it up from your own store, or from Graph, on a cached basis, with an explicit staleness budget.

---

### Q39. Which claim is the durable identifier for a user — `sub`, `oid`, `email` or `upn`?
`[HARD — and it is a real data-integrity question, not trivia]`

> `sub` per the spec, `oid` in practice inside a Microsoft tenant, and never `email` or `upn`. `sub` in Entra ID is *pairwise* — the same human gets a different `sub` in each app registration — so it is stable but not correlatable across your own microservices. `oid` is the object ID of the user and is the same across every app in the tenant, so for an integration platform the real primary key is the pair `(tid, oid)`.

| Claim | Stable? | Same across apps? | Safe for authorization / DB key? |
|---|---|---|---|
| `sub` | Yes, immutable, never reassigned | **No** — pairwise per client ID | Yes, within one app |
| `oid` | Yes, immutable per user per tenant | Yes, within the tenant | Yes — this is the one |
| `tid` | Yes | Yes | Use *with* `oid`, never alone |
| `email` | **No** — mutable | n/a | **No** |
| `upn` / `preferred_username` / `unique_name` | **No** — mutable, may be a phone number | n/a | **No** — display only |

Microsoft's warning is blunt and worth quoting nearly verbatim: never use `email` or `upn` values to store or determine whether the user in an access token should have access to data — mutable claim values change over time, which makes them insecure and unreliable for authorization. The concrete failure: a user marries, IT renames `priya.k@contoso.com` to `priya.r@contoso.com`, and every row you keyed on email is now orphaned — or worse, gets re-attached when the old address is recycled to someone else.

Two more traps for the same question:

- **`sub` is scoped to the issuer.** Under standard OIDC, claims are interpreted within the issuer, so `sub: ABC123` from tenant A and `sub: ABC123` from tenant B are *different users*. If you use the tenant-independent `common` metadata endpoint you must include `tid` in the key. This matters the moment your platform serves more than one client organisation.
- **App-only tokens have no user.** In a client-credentials token there is no meaningful user identity — the `sub` is the service principal's object ID and `oid` identifies the service principal, not a person. If your audit table has a `user_id` NOT NULL column, daemon integrations will break it. Use the `idtyp` optional claim (value `app`) — Microsoft calls it the most accurate way for an API to tell an app-only token from an app+user token — and log the caller as a service identity.

**If they push back — "we federate B2B guests; does `oid` still work?"** — The guest gets an object in *your* resource tenant with its own `oid`, so `(tid, oid)` in your tenant remains a valid key; the `idp` claim tells you where they actually authenticated. What you must not do is key on the guest's home-tenant identifier or the `#EXT#` UPN.

---

### Q40. Front-channel versus back-channel logout — which do you implement?
`[MEDIUM-HARD]`

> Front-channel logout signs a user out by loading each application's logout URL in a hidden iframe or a browser redirect chain — it is simple but depends on third-party cookies, so it is increasingly unreliable. Back-channel logout has the OP POST a signed `logout_token` server-to-server to each RP, which is reliable but requires each RP to maintain a session store it can invalidate by `sid` or `sub`. Entra ID implements RP-initiated and front-channel logout, so on Azure I design for short sessions plus Continuous Access Evaluation rather than pretending logout is instantaneous everywhere.

The three specs, all Final at the OpenID Foundation:

| Spec | Mechanism | Fails when |
|---|---|---|
| RP-Initiated Logout 1.0 | RP redirects the user to `end_session_endpoint`, optional `post_logout_redirect_uri` | Only signs out at the OP + that one RP |
| Front-Channel Logout 1.0 | OP renders an `<iframe>`/GET per RP logout URI | Browsers block third-party cookies; a slow or dead RP silently fails; you get no confirmation |
| Back-Channel Logout 1.0 | OP POSTs a signed `logout_token` JWT to each RP's backchannel URI | RP is stateless / JWT-only with no session store to kill |

Entra ID specifics you should say:

- The endpoint is `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/logout`, GET or POST, with `post_logout_redirect_uri` that must match a registered redirect URI.
- Single sign-out is configured per app registration with a **Front-channel logout URL**. Entra sends an HTTP GET there when the user signs out of any other app in the tenant; your app must clear the session and return **200**.
- Signing out at the OP does not invalidate already-issued access tokens. They stay valid until `exp`. This is the point candidates miss.

So the honest architecture answer: **logout is a session concept, not a token concept.** For APIs, the levers that actually revoke access are short access-token lifetimes, refresh-token revocation, and Continuous Access Evaluation — where a CAE-capable client and resource get long-lived tokens (20–28 hours) that are revoked in near-real-time on critical events such as account disablement or password change.

**If they push back — "how do we kill a compromised session right now?"** — Revoke the refresh tokens (Graph `revokeSignInSessions`), disable the account, and rely on CAE for near-real-time propagation to CAE-aware resources. For non-CAE resources, the worst-case window is the access-token lifetime, which is why 60–90 minutes matters and why you do not raise it to 24 hours "for performance".

---

### Q41. What is the hybrid flow, and would you use it today?
`[MEDIUM — a "do you know why the old code looks like that" question]`

> Hybrid flow returns an `id_token` directly from the authorization endpoint *and* an authorization code, using `response_type=code id_token`. It existed so a server-rendered web app could establish a session immediately without waiting for the code redemption. Today I would not choose it for a new build — plain code flow with PKCE and `response_mode=form_post` gives you the same result with one fewer token exposed in the front channel.

The permitted hybrid `response_type` values are `code id_token`, `code token`, and `code id_token token`. In the two variants that return a token from `/authorize` you must also validate `at_hash` (binds the access token to the `id_token`) and `c_hash` (binds the code), or you have reintroduced the injection attacks the code flow avoids.

Why it lingers in enterprise codebases: the old ASP.NET / OWIN OpenID Connect middleware defaulted to `code id_token`, so a decade of internal .NET apps are wired that way, and in Entra ID that requires ticking **ID tokens (used for implicit and hybrid flows)** in Authentication, or setting `enableIdTokenIssuance: true` under `implicitGrantSettings` in the manifest. If that box is unticked and the app requests `response_type=id_token`, Entra returns `unsupported_response`.

One concrete cost of the front-channel variants: the **group claim overage limit drops to six groups** when the token comes back through the implicit part of a hybrid flow, versus 200 for a normal JWT — because the response travels in the URL. That alone breaks group-based authorization in most enterprise tenants (see Q46).

Also: if you must use a front-channel response, use `response_mode=form_post`, not `fragment`. Microsoft recommends it both for security and reliability — a `fragment` response rides in the URL and is subject to a 2,048-character limit, so a fat token gets truncated and authentication mysteriously fails.

**If they push back — "so hybrid is deprecated?"** — Not deprecated, just superseded. RFC 9700 says SHOULD NOT for any response type that issues *access tokens* at the authorization endpoint, which condemns `code token` and `code id_token token`. `code id_token` is not forbidden, it is simply unnecessary now that code+PKCE is universally supported. New builds: `response_type=code`, PKCE, `response_mode=form_post` for web apps.

---

## 7. Microsoft Entra ID Specifics

*EY GDS runs on Microsoft. Everything in this section is answerable with the exact object names and claim names, and interviewers in a Microsoft shop notice when you use them.*

### Q42. Explain app registrations, enterprise applications and service principals.
`[MEDIUM — the highest-frequency Entra question in an integration interview]`

> An app registration creates an **application object** — the global blueprint, which lives only in the home tenant and defines redirect URIs, credentials, exposed scopes and app roles. A **service principal** is the local instance of that application in a tenant: it is what gets permissions granted to it, gets users and groups assigned, gets role assignments in Azure RBAC, and shows up in sign-in logs. **Enterprise applications** is just the portal blade that lists service principals. One application object, one service principal per tenant that consents to it.

| | App registration (application object) | Enterprise app (service principal) |
|---|---|---|
| Graph resource | `/applications` | `/servicePrincipals` |
| Scope | Global, home tenant only | Per tenant |
| Holds | Redirect URIs, credentials, `identifierUris`, exposed scopes, app-role *definitions*, `requestedAccessTokenVersion` | Consent grants, app-role *assignments*, user/group assignment, CA policy targeting, provisioning config |
| "Object ID" | The app object's id | **A different GUID** — the SP object id |

The object-ID trap is worth stating because it wastes an afternoon in real life: to scope a Conditional Access policy to a workload identity you need the **Object ID from Enterprise applications**; the Object ID shown in App registrations is the application object's and will not work. Same shape of trap in Azure RBAC — `az role assignment create --assignee` wants the principal, not the app object.

Service principal types you will see in a real tenant: `Application` (from an app registration), `ManagedIdentity` (created automatically with a managed identity, and *not* backed by an app registration you can edit), and `Legacy`. Multitenant apps create a service principal in each consenting tenant — which is why a single Microsoft app like Graph appears as an enterprise app in every tenant on earth.

```bash
# The three views of one identity, in the order you will need them in a runbook
az ad app show --id 11112222-bbbb-3333-cccc-4444dddd5555 \
  --query "{appId:appId, appObjectId:id, uris:identifierUris, tokenVer:api.requestedAccessTokenVersion}"

az ad sp show --id 11112222-bbbb-3333-cccc-4444dddd5555 \
  --query "{spObjectId:id, type:servicePrincipalType, enabled:accountEnabled}"

az role assignment list --assignee 11112222-bbbb-3333-cccc-4444dddd5555 --all -o table
```

**If they push back — "when do you create an app registration versus a managed identity?"** — Managed identity whenever the workload runs in Azure, does not sign users in, is not itself a protected API, and does not need to work across tenants — that is Microsoft's own decision list, and it removes credential management entirely. App registration when you need to expose an API, sign users in, run multitenant, or run outside Azure (and then pair it with workload identity federation rather than a secret, see Q49).

---

### Q43. Delegated versus application permissions, and when is admin consent required?
`[HARD — this is the one that determines whether your integration works in production]`

> Delegated permissions are used when the app acts *on behalf of a signed-in user*: the effective permission is the intersection of what the app was granted and what the user themselves can do, and it surfaces as the `scp` claim. Application permissions are app-only — no user in the flow, no intersection, the app gets the full breadth of the permission — they surface as the `roles` claim and **always** require admin consent. Every unattended integration on this platform uses application permissions.

| | Delegated | Application (app-only) |
|---|---|---|
| Flow | auth code, OBO, device code | client credentials |
| Token claim | `scp` (space-separated string) | `roles` (array) |
| Ceiling | min(app grant, user's own rights) | the full permission, tenant-wide |
| Consent | User can self-consent unless admin-restricted | Admin consent, always |
| `idtyp` claim | absent by default | `app` |

Admin-restricted delegated permissions — `User.Read.All`, `Directory.ReadWrite.All`, `Group.Read.All` — a normal user cannot consent to; they get an error, and you need either an admin consent grant or the admin consent workflow.

The `/.default` mechanics you must get right, because they are counter-intuitive:

- Client credentials requests **must** use `scope={resource}/.default`. Requesting an individual application permission by name in a client-credentials flow is not supported; all granted app roles for that resource come back in the token regardless.
- `/.default` is also required by the On-Behalf-Of flow.
- You cannot mix static and dynamic consent: `scope=https://graph.microsoft.com/.default Mail.Read` is an error.
- Trailing-slash gotcha: because the ARM resource URI is `https://management.azure.com/`, the correct scope is `https://management.azure.com//.default` — **two** slashes. This is a genuine, documented, half-day-losing bug.
- Admin consent URL: `https://login.microsoftonline.com/{tenant}/adminconsent?client_id={client-id}`.

Platform-engineer framing: in a paved-road setup, application permissions and role assignments are declared in Terraform/Bicep next to the workload and reviewed in the PR, never clicked in the portal. That gives you a diffable, auditable answer to "which service principals can read the fund master data" — which in an FS tenant is an audit question, not a curiosity ([FS](12-financial-services-integration.md)).

**If they push back — "the user is signed in but the integration runs hours later, delegated or app-only?"** — App-only, or On-Behalf-Of with a persisted refresh token, and I would push hard for app-only. Delegated access to a batch job means the job dies when the employee leaves or changes password, and it launders a machine's actions under a human's identity, which is exactly what an FS auditor objects to. If per-user context is genuinely required, capture the *user's* identity as data in the message and let the daemon act under its own app identity ([Messaging](03-messaging-and-event-streaming.md)).

---

### Q44. What is the difference between the v1.0 and v2.0 Entra endpoints?
`[MEDIUM]`

> v1.0 is the original Azure AD endpoint — work and school accounts only, and it uses a `resource` parameter to name the target API. v2.0 is the Microsoft identity platform endpoint — it also supports personal Microsoft accounts and external identities, and it replaces `resource` with resource-qualified scopes such as `api://orders-api/.default`. The critical operational point is that endpoint version and *token* version are independent: which token you get is controlled by the resource app's `requestedAccessTokenVersion`, not by which endpoint the client called.

| | v1.0 | v2.0 |
|---|---|---|
| Authorize | `/{tenant}/oauth2/authorize` | `/{tenant}/oauth2/v2.0/authorize` |
| Target API named by | `resource=https://graph.microsoft.com` | `scope=https://graph.microsoft.com/.default` |
| Accounts | Work/school | Work/school + personal MSA + external |
| `iss` | `https://sts.windows.net/{tid}/` | `https://login.microsoftonline.com/{tid}/v2.0` |
| Client-id claim | `appid` / `appidacr` | `azp` / `azpacr` |
| Client-auth-method claim values | `0` = public client, `1` = client secret, `2` = client certificate | same values, `azpacr` |
| Library | ADAL (retired) | MSAL |
| `aud` in access tokens | client ID **or** any App ID URI, request-dependent | **always** the API's client ID |

Setting the token version: the app manifest property is `requestedAccessTokenVersion` — `null` or `1` yields v1.0 tokens, `2` yields v2.0. And `scope={resource}/.default` on v2.0 is functionally the same as `resource={resource}` on v1.0, which is the sentence that makes the migration click.

One claim-set difference that bites: several claims present by default in v1.0 tokens are **not** in v2.0 tokens — `family_name`, `given_name`, `upn`, `ipaddr`, `onprem_sid`, `amr` — because v2.0 keeps tokens small. You request them back with optional claims on the app registration, or via the `profile` scope. A "migration" that flips the token version without adding optional claims silently drops the claims your authorization code depends on.

**If they push back — "we still have v1.0 apps, is that a problem?"** — Not inherently; v1.0 endpoints are supported and plenty of production Azure services still issue v1 tokens. The problems are practical: ADAL is retired so client libraries need to move to MSAL anyway, and v1's floating `aud` makes strict audience validation harder (Q45). I would treat token version as a per-API decision with a documented validation contract, not a big-bang migration.

---

### Q45. My API's audience — is it the `api://` URI or the client ID GUID?
`[HARD — a precision question, and the answer is version-dependent]`

> It depends on the token version, and that is exactly why it burns people. In **v2.0** access tokens the `aud` is **always the API's client ID GUID**. In **v1.0** access tokens `aud` can be the client ID *or* whichever App ID URI form the client used in the request — with or without a trailing slash. So an API validating v1 tokens must allow-list every identifier it owns, or set the `use_guid` optional claim to force the GUID.

The documented behaviour, verbatim in substance: in v2.0 tokens the `aud` value is always the client ID of the API; in v1.0 tokens it can be the client ID or the resource URI used in the request, and the value can depend on how the client requested the token. Without `use_guid`, an API can receive `api://MyApi.com`, `api://MyApi.com/`, `api://myapi.com/AdditionalRegisteredField`, or the client ID — for the same logical API.

Force determinism on v1 with an optional claim on the **resource** app registration (the resource owns its access token, so the client cannot set this):

```json
{
  "optionalClaims": {
    "accessToken": [
      { "name": "aud", "essential": false, "additionalProperties": ["use_guid"] },
      { "name": "idtyp", "essential": false, "additionalProperties": ["include_user_token"] }
    ]
  }
}
```

Supported App ID URI formats — worth knowing because Entra rejects anything else, and the value must not end in `/`:

| Format | Example |
|---|---|
| `api://<appId>` | `api://aaaabbbb-0000-cccc-1111-dddd2222eeee` |
| `api://<tenantId>/<appId>` | `api://aaaabbbb-…-eeee/00001111-aaaa-2222-bbbb-3333cccc4444` |
| `api://<tenantId>/<string>` | `api://aaaabbbb-…-eeee/api` |
| `https://<tenantInitialDomain>.onmicrosoft.com/<string>` | `https://contoso.onmicrosoft.com/productsapi` |
| `https://<verifiedCustomDomain>/<string>` | `https://contoso.com/productsapi` |

For apps issued **v1.0** tokens, Microsoft's guidance is to use only the default URIs `api://<appId>` or `api://<tenantId>/<appId>` — and their own recommendation overall is `api://<appId>`. For apps issued v2.0 tokens, once you have flipped the version, the guidance is explicit: modify the audience validation logic to accept **only** the `appId`.

```python
# One API, both token versions, no substring matching, no wildcards.
API_CLIENT_ID = "22223333-cccc-4444-dddd-5555eeee6666"
ALLOWED_AUD_BY_VER = {
    "2.0": frozenset({API_CLIENT_ID}),
    "1.0": frozenset({API_CLIENT_ID, "api://orders-api", "api://orders-api/"}),
}


def check_audience(claims: dict) -> None:
    allowed = ALLOWED_AUD_BY_VER.get(claims.get("ver", ""))
    if allowed is None or claims.get("aud") not in allowed:
        raise PermissionError(f"bad aud/ver: {claims.get('aud')!r} ver={claims.get('ver')!r}")
```

**If they push back — "APIM sits in front, can it just do this?"** — Yes, and it should be the paved-road default, but only if the `<audiences>` element is actually populated — see §8. A `validate-jwt` with only `<openid-config>` verifies signature and expiry and admits every token in the tenant.

---

### Q46. App roles versus groups versus the `scp` and `roles` claims — how do you model authorization?
`[HARD]`

> App roles, in almost every case. An app role is defined by the API, assigned to users, groups or service principals, and lands in the `roles` claim — so the API checks `roles == "Orders.Approver"` and never has to know that this maps to the `AM-Ops-Approvers` AD group. Group claims put raw directory GUIDs in the token, couple your API to directory structure, and blow the overage limit in any real enterprise tenant.

The four-way disambiguation, which is the actual question:

| Claim | Means | Set by |
|---|---|---|
| `scp` | delegated scopes the *client* was consented for a user | user or admin consent |
| `roles` (app+user token) | app roles assigned to the *user* on this application | admin assignment |
| `roles` (app-only token) | application permissions granted to the *service principal* | admin consent |
| `groups` | directory group object IDs | `groupMembershipClaims` on the manifest |

**The group overage numbers — quote them exactly, they are impressive and they are real:**

- **200** groups for JWTs
- **150** groups for SAML tokens
- **6** groups when the token comes through the implicit part of a hybrid flow

Past the limit, Entra omits `groups` entirely and emits an overage indicator instead: `_claim_names` / `_claim_sources` in JWTs (or `hasgroups: true` in the implicit case). Two hard-won details: **do not rely on the value** of `_claim_sources.endpoint` — it may still point at the retired Azure AD Graph host, which breaks if legacy endpoints are blocked — only on its *presence*; and then call Microsoft Graph yourself, `GET /v1.0/users/{id}/transitiveMemberOf` or `getMemberObjects`.

```python
def resolve_groups(claims: dict, graph_lookup) -> set[str]:
    """Group membership that survives overage. graph_lookup(oid) -> set[str]."""
    if "groups" in claims:
        return set(claims["groups"])
    overage = "groups" in claims.get("_claim_names", {}) or claims.get("hasgroups")
    if overage:
        # Ignore the endpoint in _claim_sources; construct the Graph call ourselves.
        return graph_lookup(claims["oid"])
    return set()
```

Mitigations, in the order I would apply them: (1) define **app roles** and assign groups to them — the token then carries a handful of role strings instead of hundreds of GUIDs; (2) if you must use groups, set the claim to *Groups assigned to the application* rather than *All groups* — note this requires at least a P1 licence, does not include indirect membership, and a free tenant cannot assign groups to an application at all; (3) always define a baseline low-privilege role, otherwise every assigned user lands on your only defined role, which is usually `admin`.

And the ceiling on all of it: none of these claims does object-level authorization. `roles: ["Orders.Approver"]` does not say the caller may approve *order 4711* for *fund F-12*. That check is yours, in code, against your own data — see BOLA in §11.

**If they push back — "group membership changed but the token still says otherwise"** — Correct and expected: claims are a snapshot from token-issuance time. If you need real-time membership you must call Graph, not read the token. For managed identities there is a harder version of this: the managed-identity back end caches per resource URI for **around 24 hours**, so a role or group change on a managed identity can take up to a day to take effect, and you cannot force a refresh. That is a design constraint, not a bug — it is a reason to prefer direct Azure RBAC role assignments over group-mediated ones for managed identities.

---

### Q47. Managed identity: system-assigned versus user-assigned, and how does a Function App get a token with zero secrets?
`[HARD — the flagship "no credentials in the pipeline" answer for this JD]`

> A system-assigned identity is created with the resource, shares its lifecycle, and dies with it — one per resource. A user-assigned identity is a standalone Azure resource you create ahead of time, attach to many resources, and grant permissions to once. On a platform team I default to **user-assigned**, because it lets me create the identity and its role assignments in Terraform *before* the workload exists, so there is no chicken-and-egg on first deploy and no re-granting every time an app is recreated.

| | System-assigned | User-assigned |
|---|---|---|
| Lifecycle | Tied to the resource; deleted with it | Independent Azure resource |
| Cardinality | One per resource | Many resources : one identity |
| Grant permissions | After the resource exists | Before — great for IaC ordering |
| Blast radius | Smallest | Shared — a compromise is wider |
| Terraform ergonomics | Two-phase apply | Single clean graph |

**How the token actually arrives — no secrets anywhere.** The platform injects two environment variables into the app and runs a local token service:

```http
GET /MSI/token?resource=https://vault.azure.net&api-version=2019-08-01 HTTP/1.1
Host: <ip-address-:-port-in-IDENTITY_ENDPOINT>
X-IDENTITY-HEADER: <value-of-IDENTITY_HEADER>
```

- `IDENTITY_ENDPOINT` — the local token service URL. `IDENTITY_HEADER` — an SSRF mitigation whose value the platform rotates; you send it as `X-IDENTITY-HEADER`.
- `api-version=2019-08-01` for App Service / Functions / Container Apps.
- On a plain VM or VMSS it is IMDS instead: `GET http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=…` with the header `Metadata: true` (lower-case `true`, also an SSRF mitigation).
- **If more than one user-assigned identity is attached you must disambiguate** with `client_id`, `principal_id`/`object_id`, or `mi_res_id`. Omit them all and the service tries the *system-assigned* identity, which may not exist — that is the classic "works in dev, 400 in prod" managed-identity bug.

Raw HTTP, for when you are debugging inside the container:

```python
import os

import httpx


def managed_identity_token(resource: str, client_id: str | None = None) -> str:
    """App Service / Functions / Container Apps local token service."""
    params = {"resource": resource, "api-version": "2019-08-01"}
    if client_id:                      # required when several UAMIs are attached
        params["client_id"] = client_id
    resp = httpx.get(
        os.environ["IDENTITY_ENDPOINT"],
        params=params,
        headers={"X-IDENTITY-HEADER": os.environ["IDENTITY_HEADER"]},
        timeout=10.0,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]
```

Retry policy for the IMDS variant, straight from the docs: retry on 404, 429 and 5xx with exponential backoff; a **410** means IMDS is updating and will be back within a maximum of 70 seconds. The documented backoff is 5 attempts with delays of roughly 0s, 2s, 6s, 14s, 30s.

Bicep for the paved-road shape — identity first, role assignment second, app third:

```bicep
param location string = resourceGroup().location
param keyVaultName string

resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-orders-sync'
  location: location
}

resource kv 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

// Key Vault Secrets User
resource kvRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: kv
  name: guid(kv.id, uami.id, '4633458b-17de-408a-b874-0445c86b69e6')
  properties: {
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '4633458b-17de-408a-b874-0445c86b69e6'
    )
  }
}

resource farm 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: 'plan-integration'
  location: location
  sku: { name: 'EP1', tier: 'ElasticPremium' }
  kind: 'elastic'
  properties: { reserved: true }
}

resource fn 'Microsoft.Web/sites@2023-12-01' = {
  name: 'func-orders-sync'
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${uami.id}': {} }
  }
  properties: {
    serverFarmId: farm.id
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      appSettings: [
        // no secrets - just tell the SDK which identity to use
        { name: 'AZURE_CLIENT_ID', value: uami.properties.clientId }
      ]
    }
  }
}
```

Two limits to state before they ask: managed identities **do not work cross-tenant**, and configurable token-lifetime policies are **not supported** for managed identity service principals.

**If they push back — "why not just put the secret in Key Vault?"** — Because that only moves the problem: something still has to authenticate to Key Vault. Managed identity is the bottom turtle — the platform proves the workload's identity, so there is no secret to rotate, leak, or commit. Key Vault then holds the things that genuinely cannot be managed identities: partner API keys, SFTP keys, legacy SOAP credentials.

---

### Q48. Show me real Python that calls a protected internal API from a container, with no secrets.
`[HARD — expect to type this in a coding round]`

> I use `azure-identity`. In production the credential resolves to the managed identity or the workload identity; on my laptop the same code resolves to my `az login` session, so there is no `if local:` branch anywhere. I ask for the API's `.default` scope, put the token in the `Authorization` header, and let the credential handle caching and refresh — the one thing you must not do is construct a new credential per request.

```python
"""Call an Entra-protected internal API with zero secrets.

pip install azure-identity httpx
"""
from __future__ import annotations

import logging
import os

import httpx
from azure.core.credentials import TokenCredential
from azure.core.exceptions import ClientAuthenticationError
from azure.identity import (
    AzureCliCredential,
    ChainedTokenCredential,
    DefaultAzureCredential,
    ManagedIdentityCredential,
    WorkloadIdentityCredential,
)

log = logging.getLogger(__name__)

ORDERS_SCOPE = "api://orders-api/.default"          # resource + /.default
ORDERS_BASE = os.environ.get("ORDERS_API_BASE", "https://orders.internal.contoso.com")


def build_credential() -> TokenCredential:
    """Explicit chain in prod, DefaultAzureCredential only for local dev.

    DefaultAzureCredential probes many sources; in production that is wasted
    latency and a surprising failure mode. Name what you expect.
    """
    env = os.environ.get("APP_ENV", "local")
    if env == "local":
        return DefaultAzureCredential(exclude_interactive_browser_credential=True)
    if os.environ.get("AZURE_FEDERATED_TOKEN_FILE"):
        return WorkloadIdentityCredential(          # AKS workload identity
            tenant_id=os.environ["AZURE_TENANT_ID"],
            client_id=os.environ["AZURE_CLIENT_ID"],
            token_file_path=os.environ["AZURE_FEDERATED_TOKEN_FILE"],
        )
    return ChainedTokenCredential(
        ManagedIdentityCredential(client_id=os.environ.get("AZURE_CLIENT_ID")),
        AzureCliCredential(),                       # break-glass for a debug pod
    )


# Module-level: the credential caches tokens in memory and refreshes them.
# Creating one per request means a token request per call - a real prod incident.
CREDENTIAL: TokenCredential = build_credential()


class OrdersClient:
    def __init__(self, credential: TokenCredential = CREDENTIAL) -> None:
        self._credential = credential
        self._http = httpx.Client(base_url=ORDERS_BASE, timeout=httpx.Timeout(10.0, connect=3.0))

    def _auth_header(self) -> dict[str, str]:
        try:
            token = self._credential.get_token(ORDERS_SCOPE)
        except ClientAuthenticationError:
            log.exception("token acquisition failed for scope=%s", ORDERS_SCOPE)
            raise
        return {"Authorization": f"Bearer {token.token}"}

    def get_order(self, order_id: str) -> dict:
        resp = self._http.get(
            f"/v1/orders/{order_id}",
            headers={**self._auth_header(), "Accept": "application/json"},
        )
        if resp.status_code == 401:
            # Stale cached token or a revoked grant: log the WWW-Authenticate
            # challenge, which carries the reason (claims challenge, bad aud, ...).
            log.warning("401 from orders-api: %s", resp.headers.get("WWW-Authenticate"))
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self._http.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = OrdersClient()
    try:
        print(client.get_order("4711"))
    finally:
        client.close()
```

Points to say while the interviewer reads it:

- **`get_token()` is cheap to call per request** — the library caches in memory and only hits Entra on a miss or expiry. The anti-pattern is a fresh credential object per request, not a fresh `get_token` call.
- **Scope, not resource.** v2.0 wants `api://orders-api/.default`. With `WorkloadIdentityCredential` you *must* use the `<resource>/.default` form — a bare resource URI can fail, because workload identity goes through the v2 token endpoint rather than the IMDS `resource` flow.
- `AZURE_CLIENT_ID` is how you point `ManagedIdentityCredential` at the right user-assigned identity — the same variable AKS's webhook injects.
- **CAE:** `get_token(..., enable_cae=True)` exists, but CAE is not supported for developer and managed identity credentials, so do not promise near-real-time revocation on a managed-identity path.
- Async variant is `azure.identity.aio`, and those credentials must be closed — they are async context managers. Relevant if the caller is FastAPI.

**If they push back — "why not `DefaultAzureCredential` everywhere?"** — Because in production it is non-deterministic. It walks a chain and, since 1.14, continues past failing developer credentials; a misconfigured pod can silently authenticate as a leftover CLI session or an environment-variable service principal instead of the identity you intended. Explicit chains fail fast and log clearly, which is what you want at 3am.

---

### Q49. Explain workload identity federation. How do GitHub Actions and AKS get Azure tokens with no secret?
`[HARD — directly on the JD's CI/CD + GitOps + security axis]`

> Workload identity federation replaces a client secret with a trust relationship. You register a federated identity credential on an app registration or user-assigned managed identity that says "trust tokens from this issuer, with this subject, for this audience". The external platform — GitHub, Azure DevOps, an AKS cluster — mints a short-lived OIDC token, the workload presents it to Entra as a client assertion, and Entra swaps it for an Azure access token. Nothing long-lived is ever stored.

The exchange itself is RFC 7523-shaped: `grant_type=client_credentials` with `client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer` and `client_assertion` set to the external OIDC token.

The numbers and constraints, all documented:

- **Maximum 20 federated identity credentials** per application or per user-assigned managed identity.
- `issuer`, `subject` and `name` are capped at **600 characters** (`name` is 3–120, URL-friendly, immutable).
- Exactly **one** audience, and the value is `api://AzureADTokenExchange`.
- **No wildcards** in any property. The `issuer` + `subject` pair must be unique on the app and must match the incoming token exactly — a mismatch produces no configuration error, it just fails at exchange time.
- Only issuers signing with **RS256** are supported.
- Propagation delay: a token request made minutes after creating the credential can fail with `AADSTS70021: No matching federated identity record found for presented assertion` — so add retries and do not create-and-immediately-use in a pipeline.
- Create FICs under the same identity **sequentially**, not concurrently — parallel creates return HTTP 409. The AzureRM Terraform provider does this serially from v3.40.0 onward.

GitHub Actions end to end:

```hcl
# azuread provider >= 3.0
resource "azuread_application" "deployer" {
  display_name     = "gha-integration-platform-deployer"
  sign_in_audience = "AzureADMyOrg"
}

resource "azuread_service_principal" "deployer" {
  client_id = azuread_application.deployer.client_id
}

resource "azuread_application_federated_identity_credential" "gha_main" {
  application_id = azuread_application.deployer.id
  display_name   = "gha-main"
  description    = "GitHub Actions, main branch only"
  audiences      = ["api://AzureADTokenExchange"]
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = "repo:contoso-platform/integration-paved-road:ref:refs/heads/main"
}

resource "azuread_application_federated_identity_credential" "gha_prod_env" {
  application_id = azuread_application.deployer.id
  display_name   = "gha-env-prod"
  audiences      = ["api://AzureADTokenExchange"]
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = "repo:contoso-platform/integration-paved-road:environment:prod"
}
```

```yaml
# .github/workflows/deploy.yml
permissions:
  id-token: write        # REQUIRED - without it there is no OIDC token to exchange
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: prod    # makes the subject 'environment:prod' - see the FIC above
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - run: az account show
```

The `subject` is the whole security control. `repo:org/repo:ref:refs/heads/main` means only that branch; `…:environment:prod` means only jobs targeting the protected `prod` environment, so GitHub's environment approvals become the gate. `…:pull_request` would let any fork PR assume the identity — never register that against a privileged app. See [CI/CD & GitOps](05-cicd-iac-and-gitops.md).

AKS side — the same primitive, different issuer:

```bash
az identity federated-credential create \
  --name orders-sync-aks \
  --identity-name id-orders-sync \
  --resource-group rg-integration \
  --issuer "$(az aks show -g rg-platform -n aks-platform --query oidcIssuerProfile.issuerUrl -o tsv)" \
  --subject "system:serviceaccount:integration:orders-sync" \
  --audience api://AzureADTokenExchange
```

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: orders-sync
  namespace: integration
  annotations:
    azure.workload.identity/client-id: "11112222-bbbb-3333-cccc-4444dddd5555"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders-sync
  namespace: integration
spec:
  replicas: 2
  selector:
    matchLabels: { app: orders-sync }
  template:
    metadata:
      labels:
        app: orders-sync
        azure.workload.identity/use: "true"   # REQUIRED - the webhook only mutates labelled pods
      annotations:
        azure.workload.identity/service-account-token-expiration: "3600"
    spec:
      serviceAccountName: orders-sync
      containers:
        - name: app
          image: acrplatform.azurecr.io/orders-sync:1.4.2
```

The mutating webhook injects `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_AUTHORITY_HOST` and `AZURE_FEDERATED_TOKEN_FILE`, plus a projected service-account token volume — which is why the Python in Q48 needs no configuration. The projected token's `expirationSeconds` defaults to **3600** with a supported range of **3600–86400**. The cluster publishes `{IssuerURL}/.well-known/openid-configuration` and `{IssuerURL}/openid/v1/jwks` so Entra can verify the SA token's signature. Minimum `azure-identity` for Python is **1.13.0**. Note the label is required: without it, pods fail after restart rather than degrading quietly. See [K8s](04-microservices-containers-kubernetes.md).

**If they push back — "how is this better than a certificate in Key Vault?"** — No credential exists to steal, expire, or rotate; the trust is a policy statement, not a secret. And the subject gives you branch- and environment-level authorization that a certificate cannot: one leaked cert authorizes every workflow in the repo, whereas a FIC scoped to `environment:prod` requires GitHub to have approved that deployment first.

---

### Q50. What does Conditional Access do to a service principal?
`[HARD — the question that separates people who have shipped in an enterprise tenant]`

> Conditional Access for workload identities lets you block a service principal's token requests based on network location, Entra ID Protection service-principal risk, or authentication context. Three constraints matter operationally: it only applies to **single-tenant service principals registered in your tenant**, **managed identities are not covered**, and the only available grant control is **Block**. It also requires Workload Identities Premium licensing to create or modify those policies.

What it cannot do, and why: a service principal cannot perform MFA and has no device, so the user-oriented controls are meaningless. The available conditions are locations, service-principal risk, and authentication context; the grant is Block only.

**The trap that causes outages:** *"While service principals can be added to groups, Conditional Access policies assigned to a group that contains a service principal are not enforced for that service principal."* The SP must be assigned **directly** to the policy as a workload identity. Teams routinely assume group-based targeting works, ship the policy, and believe they have a control they do not have.

For an integration platform the practical translation is a network-egress dependency:

- If you scope a location-based policy to your integration service principals, allowed named locations must contain the **egress** IPs of everything that authenticates — the AKS outbound NAT IPs, the Function App's outbound addresses, the self-hosted runner subnet, the APIM subnet.
- Scale out, add an AZ, swap to a new NAT gateway, or move region, and you break your own integrations with an `AADSTS53003`-style block. This belongs in the runbook and in the IaC as a dependency between the NAT public IP and the named location — otherwise the platform team's Terraform run silently disarms the security team's policy or vice versa.
- Diagnosis lives in **Entra ID → Sign-in logs → Service principal sign-ins**, Conditional Access tab. The failure text is "Access has been blocked due to Conditional Access policies."
- Roll out in **Report-only** first. On a workload-identity policy that is not optional — there is no user to phone when a batch job starts failing at 2am.

Also worth one sentence: because managed identities are out of scope for CA, the governance lever for them is access reviews plus tight Azure RBAC, not CA.

**If they push back — "so how do you restrict a managed identity's network access?"** — At the resource, not at Entra: private endpoints, service/subnet firewall rules on the target (Key Vault, Storage, Service Bus, SQL), and NSGs. That gives you network-layer restriction on the *data plane* while Entra RBAC restricts the *control plane*. Zero-trust in this estate is the combination, not CA alone — see §13.

---

### Q51. What is configurable about Entra token lifetimes, and what is not?
`[MEDIUM-HARD]`

> Access tokens default to a **randomised 60–90 minutes**, averaging 75, and ID and SAML2 tokens default to **one hour**. All three are governed by one policy property, `AccessTokenLifetime`, configurable from a minimum of 10 minutes to a maximum of 23:59:59 — Graph or PowerShell only, there is no portal UI. Refresh and session token lifetimes have **not** been configurable since 30 January 2021; the modern control for "how often must the user re-authenticate" is Conditional Access sign-in frequency.

| Token | Default | Configurable? |
|---|---|---|
| Access token | 60–90 min, randomised (75 avg) | Yes — `AccessTokenLifetime`, 00:10:00 → 23:59:59 |
| ID token | 1 hour | Yes — same property, despite the name |
| SAML2 token | 1 hour (+5 min clock-skew factor on `NotOnOrAfter`) | Yes — same property |
| Refresh token max inactive time | 90 days | **No** |
| Refresh token max age (SF and MF) | Until-revoked | **No** |
| Session token max age | Until-revoked | **No** |
| CAE long-lived access token | 20–28 hours | Effectively no — negotiated by CAE-capable client+resource |
| Managed identity | — | **Not supported** for MI service principals |

Details worth having ready:

- The randomisation is deliberate: it spreads token demand so tenants do not create hourly thundering-herd spikes against Entra.
- **An organisation-level policy beats an application-level policy.** If your app-level policy "isn't working", look for a tenant-wide one — that is called out explicitly in the docs.
- CAE long-lived tokens are not a weakening: they are revoked in near-real-time on critical events such as account disablement and password change.
- Non-persistent SSO session tokens have a 24-hour max inactive time; persistent ones 90 days, sliding on use.

Design implications for the integration platform, which is what they are really probing:

1. **Never hardcode an assumed lifetime.** Use `expires_in` / `expires_on` from the token response and refresh at ~80% of remaining life. Code that assumes "tokens last an hour" breaks the day CAE hands it a 28-hour token or an admin sets a 10-minute policy.
2. **Do not shorten access-token lifetimes as a security theatre gesture.** It multiplies token-endpoint traffic across every connector and gains you little without CAE.
3. **Cache tokens in APIM/backend by `(client, resource)` and never past `exp`.** A shared token cache across tenants is a cross-tenant data leak.

**If they push back — "the customer wants 15-minute tokens for compliance"** — Technically possible (minimum 10 minutes) and I would push back with the trade-off in writing: 4–6× the token-endpoint calls per integration, more throttling exposure, and no meaningful gain over CAE, which revokes in near-real-time instead of merely expiring sooner. If it is a hard regulatory line, I would set it on the specific high-sensitivity resource app via a policy assigned to that app, not tenant-wide.

---

### Q52. A Function App gets 401 from our internal API in production but works in UAT. Walk me through the diagnosis.
`[HARD — the runbook question; the JD explicitly asks for operational runbooks]`

> I work outward from the token, because a 401 is almost always the token being wrong rather than the code being wrong. Decode the token the caller actually sent and check `aud`, `iss`, `ver`, `tid`, `appid`/`azp` and `roles`; then check whether the token was even issued; then check whether the API is validating what it thinks it is. Every step has a command, and the whole thing is about ten minutes.

**Step 1 — get the actual token, not the intended one.** From the caller, log the token's claims (never the raw token) at a debug level:

```python
import jwt  # PyJWT

claims = jwt.decode(token, options={"verify_signature": False})  # INSPECTION ONLY
print({k: claims.get(k) for k in ("aud", "iss", "ver", "tid", "appid", "azp", "idtyp", "scp", "roles", "exp")})
```

Say out loud that `verify_signature: False` is for inspection only and never appears in a validation path — interviewers listen for that.

**Step 2 — the six checks, in the order they fail in real life:**

| Symptom in the claims | Cause | Fix |
|---|---|---|
| `aud` is `api://…` but the API expects a GUID (or vice versa) | Token version mismatch — v1 vs v2 `aud` semantics | Align `requestedAccessTokenVersion` and the API's allow-list (Q45) |
| `roles` absent on an app-only token | Application permission granted in UAT, never admin-consented in prod | Grant + admin consent; re-request the token |
| `scp` present where `roles` expected | The caller is using a delegated flow, not client credentials | Fix the scope to `{resource}/.default` (Q43) |
| `tid` is the UAT tenant | Wrong authority baked into config | Fix `AZURE_TENANT_ID` |
| `appid`/`azp` is not the identity you expect | `DefaultAzureCredential` picked up a stray credential, or the wrong UAMI (no `client_id` with several attached) | Pin `ManagedIdentityCredential(client_id=…)` (Q47/Q48) |
| Token acquisition itself fails | CA block, or role assignment not yet effective | Sign-in logs; MI role changes take up to ~24h |

**Step 3 — was the token even issued?** Entra ID → **Sign-in logs → Service principal sign-ins**, filter on the app ID, open the Conditional Access tab. If CA blocked it you will see "Access has been blocked due to Conditional Access policies" — likely the prod egress IP is missing from the named location (Q50). In KQL:

```kusto
AADServicePrincipalSignInLogs
| where TimeGenerated > ago(1h)
| where AppId == "11112222-bbbb-3333-cccc-4444dddd5555"
| where ResultType != "0"
| project TimeGenerated, ResultType, ResultDescription, IPAddress, ResourceDisplayName
| order by TimeGenerated desc
```

**Step 4 — is the resource side configured as you think?**

```bash
az ad app show --id "$API_CLIENT_ID" \
  --query "{tokenVer:api.requestedAccessTokenVersion, uris:identifierUris, appRoles:appRoles[].value}"

az ad app permission list-grants --id "$CALLER_CLIENT_ID" -o table   # delegated grants
az role assignment list --assignee "$CALLER_CLIENT_ID" --all -o table  # Azure RBAC
```

**Step 5 — is APIM in the path?** If APIM fronts the API, a 401 may be APIM's `validate-jwt`, not the backend's. The response header `WWW-Authenticate` and the APIM trace tell you which. Check `<audiences>`, `<issuers>` and the `<openid-config>` URL version — a policy pointing at the v2 metadata while the app issues v1 tokens fails on the issuer check (§8).

**Step 6 — the two boring ones.** Clock skew on the host (`nbf`/`exp` fail if the container drifts) and an expired secret if the caller was never migrated to managed identity — which is the argument for Q47 and Q49 all over again.

**If they push back — "what goes in the runbook?"** — The decode snippet, the six-row symptom table, the KQL, and the two escalation paths (identity team for consent/CA, platform team for role assignments and egress IPs), plus the note that managed-identity role changes can take up to ~24 hours to take effect so "I just granted it" is not proof. A runbook that says "check the token is valid" is not a runbook; a runbook that says "run this, compare `aud` to this allow-list" is.

## 8. Enforcing It All in Azure APIM

JD responsibility 3 is *"build and manage API gateways including authentication, throttling, versioning and monitoring."* This section is the one where you sound like the person who owns the gateway rather than someone who consumes it.

### Q53. Show me the exact policy you would write to validate an Entra ID token at the gateway.
`[MEDIUM — near-certain question. Have the XML in muscle memory.]`

> Inbound `validate-jwt`, pointed at the tenant's OpenID Connect metadata document, with an explicit `<audiences>` list, an explicit `<issuers>` list, and a `<required-claims>` check on `roles` or `scp`. Signature plus expiry is not validation — without `<audiences>` you accept every token that tenant ever issued. On Entra specifically I'd reach for `validate-azure-ad-token`, which is the same check with the metadata URL built in and client app IDs as first-class config.

```xml
<policies>
  <inbound>
    <base />
    <validate-jwt header-name="Authorization"
                  require-scheme="Bearer"
                  require-expiration-time="true"
                  require-signed-tokens="true"
                  clock-skew="30"
                  failed-validation-httpcode="401"
                  failed-validation-error-message="Unauthorized. Access token is missing or invalid."
                  output-token-variable-name="jwt">
      <openid-config url="https://login.microsoftonline.com/{{entra-tenant-id}}/v2.0/.well-known/openid-configuration" />
      <audiences>
        <audience>api://payments-api</audience>
        <audience>{{payments-api-client-id}}</audience>
      </audiences>
      <issuers>
        <issuer>https://login.microsoftonline.com/{{entra-tenant-id}}/v2.0</issuer>
      </issuers>
      <required-claims>
        <claim name="roles" match="any" separator=" ">
          <value>Payments.Read</value>
          <value>Payments.Write</value>
        </claim>
      </required-claims>
    </validate-jwt>
    <choose>
      <when condition="@(context.Request.Method == &quot;POST&quot; &amp;&amp; !((Jwt)context.Variables[&quot;jwt&quot;]).Claims[&quot;roles&quot;].Contains(&quot;Payments.Write&quot;))">
        <return-response>
          <set-status code="403" reason="Forbidden" />
          <set-header name="Content-Type" exists-action="override">
            <value>application/problem+json</value>
          </set-header>
          <set-body>{"type":"https://httpstatuses.io/403","title":"Insufficient role","detail":"Payments.Write required"}</set-body>
        </return-response>
      </when>
    </choose>
  </inbound>
  <backend><base /></backend>
  <outbound><base /></outbound>
  <on-error><base /></on-error>
</policies>
```

Facts behind that XML, all from the policy reference:

| Thing | Value |
|---|---|
| `failed-validation-httpcode` default | `401` |
| `clock-skew` default | `0 seconds` — set it explicitly if issuer and gateway clocks drift |
| `require-expiration-time` / `require-signed-tokens` defaults | `true` / `true` |
| OIDC metadata + JWKS refresh | pulled and cached **every 1 hour**; on an unknown `kid`, re-pulled **at most once per 5 minutes** |
| Supported asymmetric algorithms | PS256, RS256, RS512, ES256 |
| `claim match` default | `all` (every listed value must be present) — use `match="any"` for "one of these roles" |
| Scopes / sections | inbound only; global, workspace, product, API, operation |
| Element order | fixed — `openid-config`, `issuer-signing-keys`, `decryption-keys`, `audiences`, `issuers`, `required-claims`. Out of order = deploy failure |

Entra-native form, shorter and harder to get wrong:

```xml
<validate-azure-ad-token tenant-id="{{entra-tenant-id}}" output-token-variable-name="jwt">
  <client-application-ids>
    <application-id>{{partner-a-client-id}}</application-id>
    <application-id>{{partner-b-client-id}}</application-id>
  </client-application-ids>
  <audiences>
    <audience>api://payments-api</audience>
  </audiences>
  <required-claims>
    <claim name="roles" match="any">
      <value>Payments.Read</value>
    </claim>
  </required-claims>
</validate-azure-ad-token>
```

**Escaping note that matters for a platform engineer:** the portal editor tolerates raw `"` inside a policy expression, but the moment that policy lives in an ARM/Bicep template or a Terraform `azurerm_api_management_policy` resource it is XML being parsed by a machine — escape `"` as `&quot;` and `&&` as `&amp;&amp;` or the deployment fails. Everything in this file is written the way it must look in source control.

**If they push back — "what if the IdP isn't Entra?"** — Same `validate-jwt`, different `<openid-config url>`; any OP that publishes a spec-compliant discovery document and JWKS works. For an IdP with no discovery endpoint you inline the key with `<issuer-signing-keys><key certificate-id="partner-signing-cert" /></issuer-signing-keys>` and you now own the rotation problem manually — which is a reason to push the partner onto discovery.

---

### Q54. Should token validation happen at the gateway, at the backend, or both?
`[MEDIUM — the answer that separates platform thinking from app thinking]`

> Both, and Microsoft's own guidance says so — the docs describe gateway validation as "a defense in depth approach" even when the token's audience is the backend. The gateway does the cheap uniform checks so that garbage never reaches compute: signature, issuer, audience, expiry, scope or role. The backend re-validates because the gateway is not the only network path to it, and because object-level authorization — may *this* principal see *this* account — can only be answered where the data is.

Division of labour I'd write into the platform standard:

| Check | Gateway (APIM) | Backend (FastAPI/Function/Logic App) |
|---|---|---|
| Signature, `exp`, `nbf`, `iss`, `aud` | Yes — rejects at the edge, one config, one place to audit | Yes — cheap, cached JWKS, and it is the last line |
| Scope / role coarse check | Yes, per product and per operation | Yes, at the route |
| Object-level authorization (BOLA) | No — gateway has no idea which records the caller owns | **Only here.** See §11 |
| Rate limit / quota | Yes | No (except a crude self-defence limiter) |
| Schema / payload validation | Yes (`validate-content` against the OpenAPI schema) | Yes |
| Business rules | No | Yes |

The network half of the answer is what makes it real: validating at the gateway means nothing if the backend is reachable directly. So the backend App Service gets access restrictions or a private endpoint that only accepts the APIM subnet, or the AKS ingress only accepts the gateway's identity via mTLS. **Never trust a header the gateway injected** (`X-Authenticated-User`, tenant id, roles) unless the gateway-to-backend hop is itself authenticated — otherwise anyone who reaches the backend directly forges it. Either re-validate the original token at the backend, or authenticate the hop with mTLS (§9) or managed identity (Q56).

Two APIM specifics worth naming: APIM forwards the subscription key to the backend by default unless you strip it, and a token whose `aud` is the backend passes straight through APIM untouched (the "transparent proxy" scenario) — which is fine, but only if you added `validate-jwt` deliberately.

**If they push back — "isn't validating twice wasted latency?"** — An RS256 verify against a cached JWKS is tens of microseconds; the JWKS fetch happens once an hour. The cost is noise. The cost of *not* doing it is a bypassed gateway becoming an unauthenticated API.

---

### Q55. A consumer is hammering the API. How do you throttle per consumer, and what do you key the counter on?
`[MEDIUM-HARD — the throttling half of JD responsibility 3]`

> Two different controls with different jobs. A **rate limit** protects the backend from bursts — short window, `429`, retryable. A **quota** enforces a commercial volume commitment — long window, `403`, not retryable until the window rolls. I key both on the subscription when the contract is per subscription key, and on a JWT claim — tenant id or app id — when the business identity isn't one-to-one with the key.

Per subscription, the built-ins, applied at product scope:

```xml
<policies>
  <inbound>
    <base />
    <rate-limit calls="100" renewal-period="60"
                remaining-calls-header-name="X-RateLimit-Remaining"
                total-calls-header-name="X-RateLimit-Limit" />
    <quota calls="1000000" renewal-period="2592000" />
  </inbound>
  <backend><base /></backend>
  <outbound><base /></outbound>
  <on-error><base /></on-error>
</policies>
```

Keyed on a claim instead, so one partner with three subscription keys still shares one budget:

```xml
<validate-azure-ad-token tenant-id="{{entra-tenant-id}}" output-token-variable-name="jwt">
  <audiences>
    <audience>api://payments-api</audience>
  </audiences>
</validate-azure-ad-token>
<set-variable name="callerTenant"
              value="@(((Jwt)context.Variables[&quot;jwt&quot;]).Claims.GetValueOrDefault(&quot;tid&quot;, &quot;anon&quot;))" />
<rate-limit-by-key calls="600"
                   renewal-period="60"
                   counter-key="@((string)context.Variables[&quot;callerTenant&quot;] + &quot;|&quot; + context.Api.Id)"
                   remaining-calls-header-name="X-RateLimit-Remaining"
                   retry-after-header-name="Retry-After" />
<quota-by-key calls="1000000"
              renewal-period="2592000"
              first-period-start="2026-01-01T00:00:00Z"
              increment-condition="@(context.Response.StatusCode &lt; 500)"
              counter-key="@((string)context.Variables[&quot;callerTenant&quot;])" />
```

The numbers and gotchas you must have straight:

| | keyed on | breach code | window |
|---|---|---|---|
| `rate-limit` | subscription | `429 Too Many Requests` | max **300 s** |
| `rate-limit-by-key` | any expression | `429` | max **300 s** |
| `quota` | subscription, **product scope only** | `403 Forbidden` + `Retry-After` | `0` = infinite (lifetime quota) |
| `quota-by-key` | any expression | `403` + `Retry-After` | minimum **300 s**, `0` = infinite |

- `rate-limit` and `quota` **only apply when the API is called with a subscription key.** Anonymous or pure-OAuth traffic sails past them — that is when you need the `-by-key` variants.
- Counters are tracked **independently at each gateway**, including each region in a multi-region deployment and each workspace gateway. Two regions means roughly twice the configured limit in aggregate. Size for that, or accept it.
- One counter exists per `counter-key` **value**, shared across every scope that uses that value. If you want a separate counter at product and at API scope, append the scope to the key — which is why the example concatenates `context.Api.Id`.
- Microsoft's own caution: "rate limiting is never completely accurate" because the architecture is distributed. Never bill from it; bill from logs.
- `rate-limit-by-key` is **not available in the Consumption tier**; classic tiers use a sliding window while the v2 tiers use a token bucket.
- `increment-condition` referencing the response postpones the counter increment to the end of the outbound pipeline, so the `429` can arrive one call later than you'd expect.

**If they push back — "the partner says they got throttled but our dashboard says they were under the limit."** — Almost always one of three things: counters are per-gateway and they hit a second region; the `counter-key` collided with another scope's counter; or `increment-condition` deferred the increment. Return `Retry-After` and `X-RateLimit-Remaining` on every response so the conversation starts with data instead of opinion. Backoff behaviour on the consumer side is in [Messaging](03-messaging-and-event-streaming.md).

---

### Q56. The backend needs its own token. How do you get one at the gateway without calling the token endpoint on every request?
`[HARD — real integration-platform question]`

> If the backend is protected by Entra, `authentication-managed-identity` — APIM asks Entra for a token as its own managed identity, sets the `Authorization` header, and caches the token until it expires. No secret anywhere. If the backend's IdP isn't Entra, I do it by hand: `cache-lookup-value`, and on a miss a `send-request` to the token endpoint followed by `cache-store-value` with a duration derived from `expires_in` minus a safety margin.

Managed identity — the answer you give first:

```xml
<inbound>
  <base />
  <validate-azure-ad-token tenant-id="{{entra-tenant-id}}">
    <audiences>
      <audience>api://payments-api</audience>
    </audiences>
  </validate-azure-ad-token>
  <authentication-managed-identity resource="api://payments-backend"
                                   client-id="{{apim-uami-client-id}}"
                                   output-token-variable-name="msiToken"
                                   ignore-error="false" />
  <set-header name="Authorization" exists-action="override">
    <value>@(&quot;Bearer &quot; + (string)context.Variables[&quot;msiToken&quot;])</value>
  </set-header>
</inbound>
```

Omit `client-id` and the system-assigned identity is used. The docs state plainly: *"API Management caches the token until it expires."* Two cautions from the same page: anyone who can edit a policy can mint a token as that identity, so policy authoring is a privileged operation and belongs behind PR review in [CI/CD & GitOps](05-cicd-iac-and-gitops.md); and APIM does not check where the token is forwarded, so scope the policy to the API, not globally.

Non-Entra partner IdP, with caching done properly:

```xml
<inbound>
  <base />
  <cache-lookup-value key="@(&quot;partner-token-&quot; + context.Api.Id)"
                      variable-name="partnerToken"
                      caching-type="prefer-external" />
  <choose>
    <when condition="@(!context.Variables.ContainsKey(&quot;partnerToken&quot;))">
      <send-request mode="new" response-variable-name="tokenResponse" timeout="20" ignore-error="false">
        <set-url>https://partner.example.com/oauth2/v2/token</set-url>
        <set-method>POST</set-method>
        <set-header name="Content-Type" exists-action="override">
          <value>application/x-www-form-urlencoded</value>
        </set-header>
        <set-body>@($"grant_type=client_credentials&amp;client_id={{{{partner-client-id}}}}&amp;client_secret={{{{partner-client-secret}}}}&amp;scope=payments.write")</set-body>
      </send-request>
      <set-variable name="partnerToken"
                    value="@((string)((IResponse)context.Variables[&quot;tokenResponse&quot;]).Body.As&lt;JObject&gt;()[&quot;access_token&quot;])" />
      <set-variable name="tokenTtl"
                    value="@((int)((IResponse)context.Variables[&quot;tokenResponse&quot;]).Body.As&lt;JObject&gt;()[&quot;expires_in&quot;] - 300)" />
      <cache-store-value key="@(&quot;partner-token-&quot; + context.Api.Id)"
                         value="@((string)context.Variables[&quot;partnerToken&quot;])"
                         duration="@((int)context.Variables[&quot;tokenTtl&quot;])"
                         caching-type="prefer-external" />
    </when>
  </choose>
  <set-header name="Authorization" exists-action="override">
    <value>@(&quot;Bearer &quot; + (string)context.Variables[&quot;partnerToken&quot;])</value>
  </set-header>
</inbound>
```

Details that make this correct rather than merely plausible:

- **`expires_in` minus 300 seconds.** Cache slightly shorter than the token's life so a request that gets a cache hit at the very edge of the window still has a usable token when it reaches the partner.
- `send-request` `timeout` defaults to **60 seconds** — far too long to hold a client request hostage; 20 is deliberate. `ignore-error="false"` so a token failure surfaces in `on-error` instead of silently sending an unauthenticated request.
- `caching-type` defaults to `prefer-external` — external Redis if you configured one, internal otherwise. **The internal cache is volatile and shared by all units in the same region**, so a multi-region gateway keeps one cached token per region. Fine for tokens; not fine for anything requiring a single global value.
- `cache-store-value` is **asynchronous**, so a burst at expiry can produce a handful of duplicate token calls. Tokens are not single-use, so that is a non-event — say so before they ask.
- Never `<set-body>` a secret literal: `{{partner-client-secret}}` is a named value backed by Key Vault.

**If they push back — "how do you handle the partner rotating that client secret?"** — Named value bound to a Key Vault secret without a version in the URI, so APIM picks up the rotated value automatically; APIM refreshes a Key Vault-backed value **within 4 hours** of the update, or immediately if you refresh it explicitly via portal or REST. Pair it with the dual-credential overlap pattern from Q69.

---

### Q57. A partner connects over the internet. Restrict the API to their certificate and their IP ranges at the gateway.
`[MEDIUM]`

> Two declarative policies at product scope so every API in that product inherits them: `validate-client-certificate` pinned to the partner's issuing CA and subject, and `ip-filter` allowing only their egress ranges. The certificate answers "who"; the IP filter shrinks the attack surface to something a scanner never sees. Neither replaces the token check — all three stack.

```xml
<policies>
  <inbound>
    <base />
    <ip-filter action="allow">
      <address>203.0.113.17</address>
      <address-range from="198.51.100.0" to="198.51.100.31" />
    </ip-filter>
    <validate-client-certificate validate-revocation="true"
                                 validate-trust="true"
                                 validate-not-before="true"
                                 validate-not-after="true"
                                 ignore-error="false">
      <identities>
        <identity subject="CN=partner-a.payments.example.com, O=Partner A Bank, C=GB"
                  issuer-subject="CN=Contoso Partner Issuing CA, O=Contoso, C=GB" />
        <identity thumbprint="AA11BB22CC33DD44EE55FF66AA77BB88CC99DD00" />
      </identities>
    </validate-client-certificate>
    <validate-jwt header-name="Authorization" require-scheme="Bearer">
      <openid-config url="https://partner-a.example.com/.well-known/openid-configuration" />
      <audiences>
        <audience>api://payments-api</audience>
      </audiences>
    </validate-jwt>
  </inbound>
  <backend><base /></backend>
  <outbound><base /></outbound>
  <on-error><base /></on-error>
</policies>
```

Semantics people get wrong: within **one** `<identity>` every attribute listed must match; **any one** identity matching is enough (max 10). So the block above means "issued by our partner CA to that subject, **or** exactly this pinned certificate" — which is precisely the shape you want mid-rotation. All four `validate-*` attributes default to `true`; setting them explicitly is documentation for the next engineer.

The operational trap: **the gateway will not have a certificate to validate unless the hostname is configured to ask for one.** Developer/Basic/Standard/Premium need **Negotiate client certificate** on the custom domain; Consumption and the v2 tiers need **Request client certificate**. Without it `context.Request.Certificate` is `null` and every call 403s with no obvious cause. Related documented symptom: without *Negotiate client certificate*, `POST`/`PUT` bodies around 60 KB and larger can freeze or 403 due to the classic client-certificate renegotiation deadlock. And certificate renegotiation isn't supported in the v2 tiers at all.

`ip-filter` semantics: `action="allow"` denies everything unmatched; `action="forbid"` allows everything unmatched. If it's configured at more than one scope it applies in `<base />` order, so a global "corporate ranges only" filter plus a product filter can silently lock everyone out — calculate the effective policy before shipping.

**If they push back — "why not just check the thumbprint in a policy expression?"** — You can: `context.Request.Certificate.Thumbprint`, with `Verify()` or `VerifyNoRevocation()`, and `context.Deployment.Certificates.Any(...)` to compare against certificates uploaded to APIM. But `validate-client-certificate` does chain, validity, revocation and identity matching in one declarative block that a reviewer can read. Drop to expressions only for what the policy can't express — mapping a certificate subject to a tenant id, for example, then stashing it in a variable for downstream policies.

---

### Q58. How do policy scopes work in APIM, and where does `<base />` go?
`[MEDIUM — asked constantly, answered badly]`

> Five scopes: global (All APIs), workspace, product, API, operation. Each scope holds its own document with `inbound`, `backend`, `outbound` and `on-error` sections, and each section contains a `<base />` element that splices in the parent scope's version of that same section. Evaluation order is decided by nothing except where you put `<base />` — there is no hidden ordering rule.

```xml
<!-- API scope. Parent (product, then global) policies run first, then ours. -->
<policies>
  <inbound>
    <base />
    <ip-filter action="allow">
      <address>10.100.7.1</address>
    </ip-filter>
  </inbound>
  <backend><base /></backend>
  <outbound>
    <set-header name="X-Powered-By" exists-action="delete" />
    <base />
  </outbound>
  <on-error><base /></on-error>
</policies>
```

Points that score:

- `<base />` at the **top** of `inbound` gives the familiar global → product → API → operation order. Move it to the bottom and your policy runs *before* the parent's — legitimate when an operation must short-circuit before an expensive global policy.
- The widespread belief that `outbound` automatically runs inside-out is **false**. It is only true if you place `<base />` at the **end** of the outbound section, which is exactly what a good platform template does so response headers set by the narrow scope survive.
- **Removing `<base />` disconnects that section from the parent entirely** — your global security headers, correlation id and diagnostics vanish for that API. The docs call this "not recommended in most cases". Treat a missing `<base />` as a review blocker in the policy repo.
- `<base />` in a global policy is a no-op; global has no parent.
- The `backend` section holds exactly one element. Global scope has `forward-request` there by default; every other scope has `<base />`.
- The portal's **Calculate effective policy** button renders the fully-merged document. Use it before you argue with anyone about ordering.

The platform-engineer answer to "how do you avoid copy-paste across fifty APIs": **policy fragments**. Author the shared block once, include it everywhere.

```xml
<!-- Policy fragment: security-baseline -->
<fragment>
  <set-header name="X-Correlation-Id" exists-action="skip">
    <value>@(context.RequestId.ToString())</value>
  </set-header>
  <set-header name="Server" exists-action="delete" />
  <set-header name="X-Powered-By" exists-action="delete" />
  <set-header name="Ocp-Apim-Subscription-Key" exists-action="delete" />
  <set-query-parameter name="subscription-key" exists-action="delete" />
</fragment>
```

```xml
<inbound>
  <base />
  <include-fragment fragment-id="security-baseline" />
</inbound>
```

Fragments live in git alongside the API definitions, deploy through the pipeline, and are the closest thing APIM has to a golden Helm chart. Same paved-road argument as [CI/CD & GitOps](05-cicd-iac-and-gitops.md).

**If they push back — "a product policy has to run before the global one, is that possible?"** — Yes: in the product's section, put your policy above `<base />`. That is the whole mechanism. It is also why an unreviewed policy edit can quietly reorder security controls, which is why policy XML belongs in source control with the same PR gates as code.

---

### Q59. Three consumer classes with different security and throttling need the same API. How do you structure this without duplicating policy?
`[HARD — the design question that proves you've operated a gateway]`

> One API definition, three **products**. The API carries the contract and the behaviour that's true for everyone; each product carries only that consumer class's security and throttling profile; anything shared sits in a global policy or a policy fragment that each product includes. Subscriptions are issued per product, so the same backend is published three ways without forking the API or the OpenAPI document.

| Consumer class | Product | Client auth | Throttle | Extra |
|---|---|---|---|---|
| Internal services, same tenant | `internal` | `validate-azure-ad-token`, app-only `roles` | `rate-limit-by-key` 600/60 keyed on `appid` | Full data, private endpoint only |
| Partner banks | `partner` | mTLS + `validate-jwt` against partner IdP + `ip-filter` | `rate-limit` 100/60, `quota` 1,000,000 / 30 d | Contractual SLA, per-partner subscription |
| Public sandbox | `sandbox` | Subscription key only | `rate-limit` 10/60, `quota` 10,000 / 30 d | `set-backend-service` to a synthetic-data backend |

```xml
<!-- Product: partner -->
<policies>
  <inbound>
    <base />
    <include-fragment fragment-id="security-baseline" />
    <ip-filter action="allow">
      <address-range from="198.51.100.0" to="198.51.100.31" />
    </ip-filter>
    <validate-client-certificate>
      <identities>
        <identity issuer-subject="CN=Contoso Partner Issuing CA, O=Contoso, C=GB" />
      </identities>
    </validate-client-certificate>
    <rate-limit calls="100" renewal-period="60" retry-after-header-name="Retry-After" />
    <quota calls="1000000" renewal-period="2592000" />
  </inbound>
  <backend><base /></backend>
  <outbound><base /></outbound>
  <on-error><base /></on-error>
</policies>
```

```xml
<!-- Product: sandbox -->
<policies>
  <inbound>
    <base />
    <include-fragment fragment-id="security-baseline" />
    <rate-limit calls="10" renewal-period="60" />
    <quota calls="10000" renewal-period="2592000" />
    <set-backend-service base-url="https://sandbox-payments.internal.example.com" />
  </inbound>
  <backend><base /></backend>
  <outbound><base /></outbound>
  <on-error><base /></on-error>
</policies>
```

Two facts that decide this design for you:

1. **`quota` can only be applied at product scope.** The volume commitment therefore *has* to live on the product — which is convenient, because the volume commitment is a commercial artefact and products are the commercial unit.
2. **An API-scoped subscription, an all-APIs subscription or the built-in all-access subscription bypasses product-scope policies entirely.** Hand a developer an all-access key to "make testing easier" and your partner throttle, quota and IP filter silently stop applying to them. The docs warn explicitly: never use the all-access subscription for routine access or embed it in a client. Audit for it.

Versioning fits the same shape: one version set, `v1` and `v2` as versions (path segment is easiest for consumers to reason about), revisions for non-breaking change you want to smoke-test on a revision URL before making it current. Products are attached per version, so you can retire `v1` for the sandbox before you retire it for the partner.

**If they push back — "why not three APIs pointing at one backend?"** — Because then you have three OpenAPI documents drifting, three sets of operation-level policies, three things to change when the contract changes, and no single place to see who consumes what. Products exist precisely to separate *what the API is* from *who is allowed to call it and how hard*. Full end-to-end version of this design in [System Design](08-system-design-integration.md).

---

## 9. mTLS

### Q60. What actually changes in the TLS handshake when you turn on mTLS?
`[MEDIUM]`

> Ordinary TLS authenticates only the server. In mutual TLS the server additionally sends a `CertificateRequest`, and the client answers with its own `Certificate` message plus a `CertificateVerify` — a signature over the handshake transcript made with the client's private key. That signature is the actual proof; the certificate on its own proves nothing, because certificates are public. The server then builds a chain to a CA it trusts, checks validity dates and revocation, and applies its own identity policy to the subject or issuer.

What the server checks, in order, and what you configure at each step:

| Step | Checked | Where you configure it |
|---|---|---|
| Chain builds to a trusted root | Yes | Trust store: CA certs uploaded to APIM, `ca.crt` in the ingress secret, mesh root CA |
| `notBefore` / `notAfter` | Yes | `validate-not-before` / `validate-not-after` |
| Revocation (CRL / OCSP) | Optional but you want it | `validate-revocation="true"`, or `ca.crl` in the ingress secret |
| Extended Key Usage = `clientAuth` | By the TLS stack | Issued by the CA — get this right at issuance |
| Which identity is acceptable | **Your policy, not TLS** | `<identities>`, `auth-tls-match-cn`, mesh `AuthorizationPolicy` |

Version differences worth a sentence: in **TLS 1.3 (RFC 8446)** the client certificate is sent after the handshake is already encrypted, so it isn't visible to a passive observer — in TLS 1.2 it is sent in the clear. TLS 1.2 also needed *renegotiation* to request a certificate late, which is the root of APIM's documented warnings: clients with renegotiation disabled see TLS errors, and certificate renegotiation isn't supported in the v2 tiers.

And the bridge back to §1–§7: **RFC 8705** binds an OAuth access token to the client certificate that requested it, putting the certificate's SHA-256 thumbprint in the token's `cnf` / `x5t#S256` claim. The resource server then rejects a stolen bearer token presented over a different TLS connection. That is the standards-track answer to "how do I stop token replay", and it's mandated in FAPI-grade profiles — relevant in [FS](12-financial-services-integration.md).

**If they push back — "does mTLS replace OAuth?"** — No. mTLS authenticates the *channel and the client machine*; OAuth carries *what that client is allowed to do*, scoped and expiring in minutes. A certificate is valid for a year and says nothing about permissions. Regulated partner flows normally run both, and RFC 8705 is how you make them one system rather than two.

---

### Q61. How do you validate the client certificate — thumbprint, or issuer plus subject?
`[MEDIUM-HARD]`

> Thumbprint pinning is the strongest identity statement and the worst operational one: it means "exactly this certificate", so it breaks on every renewal. Issuer plus subject means "any certificate our CA issued to this name", which survives renewal and scales. For a handful of fixed partners with a written rotation runbook I pin thumbprints; for anything that has to scale I stand up an internal issuing CA and validate issuer plus subject, with revocation on.

| Approach | Survives renewal | Revocation story | Blast radius if the CA is compromised |
|---|---|---|---|
| `thumbprint` | No — must be updated in lockstep | Delete the identity, instant | None (no CA trusted) |
| `serial-number` | No | Same as thumbprint | None |
| `subject` + `issuer-subject` | Yes | CRL/OCSP, or remove the identity | Anything that CA issues |
| `issuer-certificate-id` | Yes | CRL/OCSP | Anything that CA issues |
| `issuer-subject` alone | Yes | CRL/OCSP | **Every** cert from that CA — too broad on its own |

The rotation-safe pattern, and the reason `<identities>` accepts up to ten entries: during the overlap window you list **both** the outgoing and incoming thumbprint, the partner switches whenever they're ready, and you delete the old entry afterwards. Zero-downtime pinning without a scheduled call.

```xml
<validate-client-certificate validate-revocation="true" validate-trust="true">
  <identities>
    <identity thumbprint="AA11BB22CC33DD44EE55FF66AA77BB88CC99DD00" />  <!-- outgoing, expires 2026-11-30 -->
    <identity thumbprint="BB22CC33DD44EE55FF66AA77BB88CC99DD00EE11" />  <!-- incoming -->
  </identities>
</validate-client-certificate>
```

APIM specifics: the thumbprint is **SHA-1** (that's the certificate thumbprint format, not a signature algorithm choice); `subject` and `issuer-subject` must be full Distinguished Names, comma-separated, and they are compared exactly — one different `O=` and it fails; `issuer-certificate-id` is mutually exclusive with the other issuer attributes.

**If they push back — "what do you log so you can debug a rejection at 2 a.m.?"** — Subject DN, issuer DN, thumbprint, `notAfter`, and the decision, on every request, into App Insights. Then a rejection is a one-query answer instead of a partner conference call. Also emit a metric for "certificate expires in N days" per identity, which is what makes Q65's alerting possible.

---

### Q62. Where do you terminate mTLS — APIM, Application Gateway, ingress, or a mesh sidecar?
`[HARD — architecture question, and there's a real Azure trap in it]`

> Terminate it at whatever needs the identity. For north-south partner traffic that's the API gateway: APIM validates the certificate and maps it to a consumer. For east-west traffic inside the cluster, never do it in application code — let the mesh sidecar terminate it, because then certificates are short-lived and rotate automatically. The trap is stacking a Layer-7 device in front: Application Gateway terminates TLS and opens a *new* connection to APIM, so the client certificate does not reach APIM at all.

| Termination point | Use when | Watch out for |
|---|---|---|
| **APIM** | Partner-facing REST/SOAP, per-consumer identity, policy-driven | Requires *Negotiate client certificate* (Developer/Basic/Standard/Premium) or *Request client certificate* (Consumption, v2). CA certs for validation are **not supported in Consumption** |
| **Application Gateway (WAF)** | You need OWASP WAF rules before the gateway | mTLS to APIM behind it **breaks** — the docs say so. Terminate mTLS at App Gateway and forward the certificate via mutual-authentication server variables into a header |
| **nginx ingress (AKS)** | Cluster-hosted APIs, no APIM in the path | Per-Ingress trust store; `auth-tls-verify-depth` defaults to **1**, which rejects certs issued by an intermediate |
| **Service mesh sidecar** | East-west, workload-to-workload | Identity becomes the workload, not the hostname; sidecar upgrade cadence is now your problem |

Ordering rule for a partner API in a bank: WAF (App Gateway or Front Door) → APIM → private endpoint/VNet → backend. If the WAF must be first and mTLS is contractual, terminate mTLS at the WAF, rewrite the certificate details into headers, and have APIM verify those headers over a connection that only the WAF can make. Verify current Front Door mTLS support before designing on it — it has changed more than once.

**If they push back — "why not terminate mTLS at the backend service directly?"** — Then every backend ships certificate loading, trust store management, revocation checking and rotation code, in whatever language it happens to be, and you learn about expiry from a customer. Centralising it at the gateway or sidecar makes it one config surface with one runbook. That is the same paved-road argument as golden Helm charts in [K8s](04-microservices-containers-kubernetes.md).

---

### Q63. Show me mTLS on an nginx ingress in AKS.
`[MEDIUM — real config, easy to get wrong]`

> A Kubernetes secret in the same namespace holding the partner CA chain (and optionally a CRL), then five annotations on the Ingress. The two people always miss: `auth-tls-verify-depth` defaults to 1, so an intermediate-issued certificate is rejected until you raise it, and `auth-tls-pass-certificate-to-upstream` is off by default, so the app can't see who called unless you turn it on.

```bash
kubectl create secret generic partner-ca \
  --namespace payments \
  --from-file=ca.crt=/etc/pki/partner-root-and-intermediate.pem \
  --from-file=ca.crl=/etc/pki/partner.crl
```

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: payments-partner
  namespace: payments
  annotations:
    nginx.ingress.kubernetes.io/auth-tls-secret: "payments/partner-ca"
    nginx.ingress.kubernetes.io/auth-tls-verify-client: "on"
    nginx.ingress.kubernetes.io/auth-tls-verify-depth: "2"
    nginx.ingress.kubernetes.io/auth-tls-pass-certificate-to-upstream: "true"
    nginx.ingress.kubernetes.io/auth-tls-match-cn: "CN=(partner-a|partner-b)\\.payments\\.example\\.com"
    nginx.ingress.kubernetes.io/auth-tls-error-page: "https://status.example.com/mtls-error"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - payments.example.com
      secretName: payments-server-tls
  rules:
    - host: payments.example.com
      http:
        paths:
          - path: /v1
            pathType: Prefix
            backend:
              service:
                name: payments-api
                port:
                  number: 8080
```

- `auth-tls-secret` value is `namespace/secretName`; the secret must contain a `ca.crt` key with the **full** CA chain. Adding `ca.crl` in the same secret enables CRL verification.
- `auth-tls-verify-client` accepts `on`, `off`, `optional`, `optional_no_ca`; default `on`. Use `optional` only during a migration where you still accept plaintext clients — and log which is which.
- With `pass-certificate-to-upstream: "true"` the app receives the PEM, URL-encoded, in the `ssl-client-cert` header.

Reading it in FastAPI, which is what you'd actually own:

```python
from urllib.parse import unquote

from cryptography import x509
from cryptography.x509.oid import NameOID
from fastapi import FastAPI, Header, HTTPException

app = FastAPI()

ALLOWED_CNS = frozenset({"partner-a.payments.example.com", "partner-b.payments.example.com"})


def caller_cn(ssl_client_cert: str | None) -> str:
    if not ssl_client_cert:
        raise HTTPException(status_code=401, detail="client certificate required")
    cert = x509.load_pem_x509_certificate(unquote(ssl_client_cert).encode())
    cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    if cn not in ALLOWED_CNS:
        raise HTTPException(status_code=403, detail="unknown client certificate")
    return cn


@app.get("/v1/payments")
def list_payments(ssl_client_cert: str | None = Header(default=None, alias="ssl-client-cert")):
    return {"caller": caller_cn(ssl_client_cert)}
```

**If they push back — "isn't trusting a header dangerous?"** — Yes, and that is exactly why the pod must be unreachable except through the ingress: a NetworkPolicy that only admits the ingress controller namespace, and no Service of type LoadBalancer on the pod. The header is trustworthy only because the network path is. Say that unprompted — it is the difference between configuring mTLS and understanding it.

---

### Q64. Self-signed, internal CA, or public CA for client certificates?
`[MEDIUM]`

> The choice is really about how you distribute trust and how you revoke. A self-signed client certificate means pinning that exact certificate — no CA, no revocation, fine for two or three fixed partners with a rotation runbook. An internal issuing CA gives you one trust anchor, CRL/OCSP revocation, and issuance you can automate — that's what I standardise on. A public CA is for *server* certificates; trusting one for client auth means anyone who can buy a certificate from that CA is inside your trust boundary unless you also pin the subject.

| | Trust distribution | Revocation | Scales to | Typical use |
|---|---|---|---|---|
| Self-signed | Pin each cert (thumbprint) | Delete the pin | ~5 partners | Small fixed partner set, PoC |
| Internal CA (AD CS, Key Vault, cert-manager) | One root in the trust store | CRL / OCSP | Hundreds | The default for an enterprise integration platform |
| Public CA | Already trusted everywhere | CRL / OCSP | Anything | Server certs; client auth only with strict subject pinning |
| Mesh CA (istiod / SPIRE) | Automatic, in-cluster | Short TTL makes revocation nearly moot | Every workload | East-west only |

APIM specifics: to validate self-signed client certificates you must upload the root or intermediate CA to APIM, or `Verify()` fails — and **CA certificates for validation aren't supported in the Consumption tier**, which quietly rules Consumption out of most partner-mTLS designs. Store certificates as Key Vault-referenced certificates rather than uploaded PFX files: they're reusable, access-controlled, and rotate automatically.

**If they push back — "the partner wants to send us a self-signed cert they generated on a laptop."** — Acceptable only with a pin, a documented expiry, a named owner on their side and a rotation date in the contract. What is not acceptable is trusting their self-signed cert *as a CA*, because then anything they sign is trusted by you.

---

### Q65. Certificate rotation is the part everyone underestimates. How do you actually run it?
`[HARD — and it doubles as the "operational runbook" the JD asks for]`

> Assume every certificate expires at the worst possible moment, because that's what they do. The three controls are: an overlap window where both the old and new identities are trusted simultaneously, automation that renews before expiry, and an alert on days-to-expiry that fires weeks out with a named owner attached. If a rotation requires a synchronised phone call with a partner, the design is wrong.

The runbook, which is what I'd hand to the on-call rota:

1. **Inventory.** One table: certificate, purpose, where the private key lives (Key Vault name and secret), which policies or secrets reference it, `notAfter`, owning team, partner contact. If it isn't in the table it will expire.
2. **Alert at T-60 and T-30 days.** Key Vault raises near-expiry events through Event Grid based on the certificate policy's lifetime action; route them to a ticket queue, not an inbox. Additionally alert on the *observed* `notAfter` from request logs (Q61), which catches certificates nobody registered.
3. **Issue the new certificate.** Same CA, same subject where possible; renewal then changes only the thumbprint.
4. **Widen trust before anything switches.** Add the new thumbprint as a second `<identity>` (APIM), or append the new CA to the `ca.crt` bundle (ingress). Both old and new now pass.
5. **Partner switches when ready.** Confirm from logs that you are seeing the new thumbprint — don't take their word for it.
6. **Narrow trust.** Remove the old identity, revoke the old certificate, update the inventory.

Numbers to quote: APIM refreshes a Key Vault-referenced certificate **within 4 hours** of an update in the vault, and you can force it from the portal or the management REST API. **The Key Vault certificate identifier must be stored without a version** — include a version and it never auto-rotates, which is the single most common cause of "we rotated it in the vault but production still serves the old one."

Automation that removes steps 3–4 entirely: `cert-manager` in AKS issuing from an internal CA with automatic renewal, and a mesh CA for east-west where certificate lifetime is hours and rotation is invisible. The rule of thumb: **the shorter the certificate's life, the less rotation costs you**, because the mechanism is exercised constantly instead of annually.

**If they push back — "what's your control for a certificate that expires anyway?"** — Detection before the customer: a synthetic mTLS probe per partner endpoint running on a schedule, alerting on handshake failure, plus the days-to-expiry metric. And an emergency path in the runbook: re-issue from the internal CA, add the identity, notify. Documented flows, contracts, pipelines and runbooks are literally JD responsibility 9 — say the word "runbook" out loud.

---

### Q66. How does mTLS work in a service mesh for east-west traffic?
`[HARD — expect it if they mention AKS or zero trust]`

> In a mesh the application does nothing. The sidecar terminates mTLS on both ends. In Istio every workload gets a SPIFFE identity derived from its Kubernetes service account — `spiffe://cluster.local/ns/payments/sa/payments-api` — the node agent generates a key and CSR, istiod signs it, Envoy picks it up over the SDS API, and the agent rotates it automatically well before expiry. I turn it on with `PeerAuthentication` in `PERMISSIVE` first, watch telemetry until no plaintext remains, then flip to `STRICT`.

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: payments
spec:
  mtls:
    mode: STRICT
---
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: payments-api-callers
  namespace: payments
spec:
  selector:
    matchLabels:
      app: payments-api
  action: ALLOW
  rules:
    - from:
        - source:
            principals:
              - "cluster.local/ns/orders/sa/orders-api"
              - "cluster.local/ns/settlement/sa/settlement-worker"
      to:
        - operation:
            methods: ["GET", "POST"]
            paths: ["/v1/payments*"]
```

- Modes are `STRICT`, `PERMISSIVE`, `DISABLE` and `UNSET` (inherit). Scope is mesh-wide (root namespace), namespace, or workload by selector, and it can be set per port — which is how you exempt a scrape endpoint without weakening the namespace.
- Istio extracts the peer identity from mTLS into `source.principal`, which is what `principals:` matches. Note the format in `AuthorizationPolicy` drops the `spiffe://` prefix.
- `PeerAuthentication` says *the channel must be mutually authenticated*. `AuthorizationPolicy` says *which identities may call what*. Enabling STRICT without authorization policies gives you encryption and identity but still allows any workload to call any other — a half-finished zero-trust story.
- Migration order matters: label namespaces for injection → restart workloads → `PERMISSIVE` → verify no plaintext in telemetry → `STRICT`. Going straight to STRICT breaks every workload without a sidecar, including jobs and anything in another namespace.

**If they push back — "why not just do TLS in the application?"** — Then certificate loading, rotation, trust distribution and pinning ship in every service in every language, and identity is a hostname rather than a workload. The mesh centralises it and gives you the identity for free in authorization policy and telemetry. The cost is honest: a sidecar per pod (latency, memory, an upgrade cadence), which is why ambient mode exists as the sidecar-less option. More on the cluster mechanics in [K8s](04-microservices-containers-kubernetes.md).

---

## 10. API Keys

### Q67. What is an API key actually for?
`[EASY — and a trap, because the right answer is a correction]`

> An API key identifies the calling *application* so you can meter it, throttle it and revoke it. It is not authentication of a user and it is not authorization. It's a long-lived bearer string with no signature, no expiry, no audience and no proof of possession — whoever holds it is it. So I use keys for identification and quota, and OAuth or mTLS for authentication.

| | API key | JWT access token | Client certificate (mTLS) |
|---|---|---|---|
| Proves | Possession of a string | Issuance by a trusted AS, to an audience, with scopes | Possession of a private key |
| Expires | Never, until revoked | Minutes to an hour | Months to a year |
| Audience-bound | No — replayable anywhere it's accepted | Yes (`aud`) | The TLS connection |
| Revocation | Immediate (regenerate) | Wait for expiry, or introspect | CRL/OCSP, or remove the pin |
| Typical leak path | Query strings, proxy logs, browser history, mobile binaries, git | Short life limits damage | Private key must be extracted first |
| Good for | Metering, quota, per-consumer analytics, revoking one consumer | Authentication + authorization | Channel authentication, non-repudiation-ish |

**If they push back — "so why do we still use them?"** — Because the operational value is real: they tell you which consumer generated which traffic, they're the throttling key, and they let you cut off one partner in seconds without touching anyone else. That's an *identification* job, and keys are good at it.

---

### Q68. How do APIM subscription keys work, and what are their scopes?
`[MEDIUM]`

> A subscription is a named container for a **pair** of keys. The caller sends it as the `Ocp-Apim-Subscription-Key` header, or as a `subscription-key` query parameter — the query parameter is only checked when the header is absent. A subscription can be scoped to a product, to a single API, to all APIs, or it can be the built-in all-access subscription. Requests with no valid key, where a key is required, get a `401`.

The gotchas that separate someone who has run APIM from someone who has read about it:

- **API-scoped, all-APIs and all-access subscriptions bypass product-scope policies.** Your product's throttle, quota, IP filter and mTLS check simply don't run for those callers. This is documented and it surprises people in production.
- **`rate-limit` and `quota` only apply when the API is called with a subscription key.** Pure-OAuth traffic with `Subscription required` turned off is unthrottled unless you use the `-by-key` variants.
- **The subscription key is forwarded to the backend by default** and will land in backend logs. Strip it at the end of `inbound`:

```xml
<set-header name="Ocp-Apim-Subscription-Key" exists-action="delete" />
<set-query-parameter name="subscription-key" exists-action="delete" />
```

- Turning off **Requires subscription** on an API or product makes it anonymous. An "open" product — subscription requirement disabled — swallows keyless requests into that product's policy context, and an API can be associated with at most one open product. If you disable the subscription requirement, you must configure another mechanism, or you have just published an unauthenticated API.
- The header and query parameter names are per-API settings and can be renamed.
- **Standalone subscriptions** (no owner) are how you give a team a shared key; you cannot assign a subscription to an Entra security group.
- Never put the key in a query string in production. It ends up in every proxy log, CDN log and browser history along the path.

**If they push back — "how do you tie a subscription to a business consumer for billing?"** — One subscription per consuming application, never per human; name it after the consumer and the environment; and reconcile billing from the request logs, not from the quota counter, because throttling counters are per-gateway and explicitly not exact.

---

### Q69. How do you rotate API keys with no downtime, and how do you store them?
`[MEDIUM-HARD]`

> Two keys exist precisely so rotation is a rolling operation: the consumer switches to the secondary, you regenerate the primary, they switch back to the new primary, you regenerate the secondary. Nobody has downtime and nobody needs a change window. For a key system I build myself, I store only a SHA-256 hash with a short lookup prefix and compare in constant time — the plaintext key exists exactly once, at issuance.

Regenerating an APIM subscription key from a pipeline:

```bash
#!/usr/bin/env bash
set -euo pipefail

SUB_ID="00000000-0000-0000-0000-000000000000"
RG="rg-integration-prod"
APIM="apim-integration-prod"
SID="partner-bank-a"

# 204 No Content on success.
az rest --method post \
  --url "https://management.azure.com/subscriptions/${SUB_ID}/resourceGroups/${RG}/providers/Microsoft.ApiManagement/service/${APIM}/subscriptions/${SID}/regeneratePrimaryKey?api-version=2024-05-01"

# Read the current pair back (this is the point: APIM keys are retrievable).
az rest --method post \
  --url "https://management.azure.com/subscriptions/${SUB_ID}/resourceGroups/${RG}/providers/Microsoft.ApiManagement/service/${APIM}/subscriptions/${SID}/listSecrets?api-version=2024-05-01"
```

`regenerateSecondaryKey` is the sibling operation. Note what `listSecrets` implies: APIM subscription keys are **recoverable plaintext**, which is exactly why they are an identification mechanism and not a credential you could build non-repudiation on. Also note the docs' own admission — APIM has **no built-in key lifecycle management**: no expiry, no automatic rotation. If you want either, you build it, which is a genuine platform-engineering deliverable: a scheduled pipeline that rotates every subscription on a cadence, publishes the new key to the consumer's Key Vault, and alerts on keys older than N days.

Your own key store, done correctly:

```python
import hashlib
import hmac
import secrets
from dataclasses import dataclass

KEY_PREFIX = "eyg"
LOOKUP_LEN = 12


@dataclass(frozen=True)
class IssuedKey:
    plaintext: str   # shown to the consumer once, never stored
    lookup: str      # indexed column
    digest: str      # stored


def issue_key() -> IssuedKey:
    raw = secrets.token_urlsafe(32)          # 256 bits of entropy
    plaintext = f"{KEY_PREFIX}_{raw}"
    return IssuedKey(
        plaintext=plaintext,
        lookup=plaintext[:LOOKUP_LEN],
        digest=hashlib.sha256(plaintext.encode("utf-8")).hexdigest(),
    )


def verify(presented: str, stored_digest: str) -> bool:
    candidate = hashlib.sha256(presented.encode("utf-8")).hexdigest()
    return hmac.compare_digest(candidate, stored_digest)
```

Three deliberate choices to defend if asked:

1. **Plain SHA-256, not bcrypt/argon2.** Password hashes are slow on purpose because passwords are low-entropy and guessable. A 256-bit random key is not brute-forceable, and putting a 100 ms KDF on every API request is a self-inflicted denial of service. (Use argon2 for *passwords*, always.)
2. **A lookup prefix** so verification is an indexed point read rather than a table scan of hashes.
3. **`hmac.compare_digest`** for constant-time comparison — timing side channels on `==` are a real finding in a security review even if hard to exploit.

Add to that: a visible prefix so secret scanners can detect the key in git, per-consumer keys (never one shared key), key age and last-used timestamps, and a revoke path that takes effect in seconds.

**If they push back — "how do you get the new key to the partner?"** — Never by email. Write it into a Key Vault they have read access to, or expose a rotation endpoint they call with their existing credential, or hand it over through the developer portal. The rotation is only as secure as the distribution channel.

---

### Q70. Is an API key secure enough?
`[MEDIUM — the closing question of this section, and the one with a scripted answer]`

> For identifying an application and metering it, yes, that's what it's for. As the only thing between the internet and a payments API, no. Microsoft's own guidance is explicit: use a subscription key **in addition to** another method of authentication or authorization — "on its own, a subscription key isn't a strong form of authentication." So my answer to a consumer who only wants a key is: key for identity and quota, plus OAuth client credentials, or mTLS if they can't do OAuth, plus an IP allow-list.

Why it fails as sole authentication, in the order a security reviewer will raise them:

- **No expiry.** A leaked key is valid until somebody notices. Tokens expire in minutes.
- **No audience.** The same string works at every endpoint that accepts it. A JWT's `aud` scopes the damage — see §3.
- **Leaks through channels you don't control.** Query strings land in proxy, CDN and web-server logs; keys get committed to git and baked into mobile apps.
- **No proof of possession.** Anyone replaying the string is indistinguishable from the real consumer, so there is no non-repudiation — which is the exact property a financial-services control review asks for.
- **Shared keys destroy attribution.** If three teams use one key you cannot revoke one of them, and your audit trail says nothing useful.

If a legacy partner genuinely cannot do better, the compensating controls I'd write into the design and the risk acceptance: short-lived keys rotated by automation; a tight `ip-filter`; a deliberately low `quota`; anomaly alerting on per-key call rate and source geography; TLS-only with the key in the header, never the query string; and a contractual rotation obligation with a named owner. That's a documented, time-boxed exception, not a default.

**If they push back — "our client says the key is inside their firewall so it's fine."** — Perimeter is not a control for a bearer secret; it is an assumption about where the attacker is. In a regulated flow — payment instruction, client data, anything that moves money or PII — you will be asked for strong authentication and traceability of the acting principal, and a key alone provides neither. Full treatment of what regulated integrations require in [FS](12-financial-services-integration.md); the zero-trust framing in §13.

## 11. OWASP API Security Top 10 (2023)

### Q71. Name the OWASP API Security Top 10 and give me one concrete fix for each.
`[MEDIUM — pure recall, but it comes up in almost every senior API interview]`

> **Spoken:** The 2023 edition is API1 Broken Object Level Authorization, API2 Broken Authentication, API3 Broken Object Property Level Authorization, API4 Unrestricted Resource Consumption, API5 Broken Function Level Authorization, API6 Unrestricted Access to Sensitive Business Flows, API7 Server Side Request Forgery, API8 Security Misconfiguration, API9 Improper Inventory Management, API10 Unsafe Consumption of APIs. The thing worth saying out loud is that three of the top five — API1, API3 and API5 — are all authorization. That tells you where the risk actually lives: not in issuing the token, but in what you do in the 5 milliseconds after you've validated it.

| # | Name | One concrete fix | Enforced where |
|---|------|------------------|----------------|
| **API1:2023** | Broken Object Level Authorization | Every read/write is scoped by the caller's identity *in the query itself* — `WHERE id = $1 AND owner_party_id = $2` — and returns 404, not 403, on a miss | Service (gateway cannot) |
| **API2:2023** | Broken Authentication | `validate-azure-ad-token` with `<audiences>` and `require-expiration-time="true"`; no ROPC; rate-limit login/reset/OTP endpoints hard | Gateway + IdP |
| **API3:2023** | Broken Object Property Level Authorization | Explicit request DTO with `extra="forbid"` and an explicit response DTO; never `Model(**request.json())` | Service (+ gateway `validate-content`) |
| **API4:2023** | Unrestricted Resource Consumption | `rate-limit-by-key` + `quota-by-key` + `validate-content max-size` + `limit-concurrency` + `forward-request timeout` | Gateway |
| **API5:2023** | Broken Function Level Authorization | No wildcard operations; every operation carries a required scope/role claim check; admin routes on a separate product | Gateway + service |
| **API6:2023** | Unrestricted Access to Sensitive Business Flows | Identify the flow with business value (bulk statement export, payee add), then throttle *that flow* per party plus bot ruleset `Microsoft_BotManagerRuleSet_1.0` | Gateway + WAF |
| **API7:2023** | Server Side Request Forgery | Never fetch a URL the caller supplied; if you must, host allow-list + resolve-then-pin the IP + block RFC 1918 and 169.254.169.254 | Service |
| **API8:2023** | Security Misconfiguration | TLS 1.2 minimum, no wildcard CORS, no open products, `<base />` inherited everywhere, secrets in Key Vault named values, IaC-only changes | Platform |
| **API9:2023** | Improper Inventory Management | OpenAPI in git is the source of truth, CI publishes to the gateway, deprecation policy of N-2 versions, one gateway per environment | Platform |
| **API10:2023** | Unsafe Consumption of APIs | Validate and schema-check what the *third party* returns, not just what the client sends; timeouts and circuit breakers on every outbound | Service |

Three merges worth knowing because interviewers who learned the 2019 list will test you on them: 2023's **API3** absorbed 2019's *Excessive Data Exposure* **and** *Mass Assignment* into one entry; 2023's **API4** absorbed *Lack of Resources & Rate Limiting*; **API6** and **API10** are genuinely new in 2023.

**If they push back — "which one causes the most real breaches?"** — BOLA, by a wide margin, and it is the one a WAF, a gateway and a JWT library can do nothing about. Every other item has a product you can buy. BOLA has only code and tests.

---

### Q72. Explain Broken Object Level Authorization. Show me the vulnerable code and the fix.
`[HARD — the single most-asked API security question. Have the code memorised.]`

> **Spoken:** BOLA is when the API validates *who you are* and *that you may use this endpoint*, but never checks *whether this particular object is yours*. The token is perfect, the scope is present, and the caller just increments an identifier in the path. The fix is not obfuscating identifiers — it is making the ownership predicate part of the data access itself, so there is no code path that can read the object without it, and returning 404 rather than 403 so you don't leak that the object exists.

**Vulnerable — and this is what real code looks like, which is why it survives review:**

```python
from fastapi import Depends, FastAPI
from app.security import verify_token  # returns validated JWT claims

app = FastAPI()


@app.get("/v1/accounts/{account_id}/statements")
async def get_statements(account_id: str, claims: dict = Depends(verify_token)):
    # Token is valid. Signature, iss, aud, exp all checked.
    # Scope "Statements.Read" is present.
    # And any authenticated client can read ANY account's statements.
    return await db.fetch_statements(account_id)
```

**Fixed — the ownership check is in the query, not in an `if`:**

```python
from fastapi import Depends, FastAPI, HTTPException
from app.security import verify_token, require_scope

app = FastAPI()


async def resolve_party(claims: dict) -> str:
    """Map the token subject to the business identity. Never trust a party id
    supplied by the caller in a header or query string."""
    return await db.party_id_for_subject(claims["oid"], claims["tid"])


@app.get("/v1/accounts/{account_id}/statements")
async def get_statements(
    account_id: str,
    claims: dict = Depends(require_scope("Statements.Read")),
):
    party_id = await resolve_party(claims)

    # The authorization predicate IS the query. There is no path to the rows
    # that skips it, and no second developer can forget it later.
    account = await db.fetchrow(
        """
        SELECT a.id
          FROM accounts a
          JOIN account_access ac ON ac.account_id = a.id
         WHERE a.id = $1 AND ac.party_id = $2 AND ac.revoked_at IS NULL
        """,
        account_id,
        party_id,
    )
    if account is None:
        # 404, not 403: 403 confirms the account exists.
        raise HTTPException(status_code=404, detail="Account not found")

    return await db.fetch_statements(account_id)
```

Four things a senior answer adds that a mid-level one doesn't:

1. **Push it below the handler.** A repository method `statements_for(account_id, party_id)` that has no overload without `party_id` is stronger than a check in every route. Best of all is Postgres row-level security so the database refuses even if the ORM is wrong.
2. **404 over 403.** Otherwise the error code is an object-existence oracle, and an attacker enumerates your customer base without ever reading a statement.
3. **Test per endpoint, not per app.** The paved-road contract test: for every operation that takes an object id, issue a token for party A, request party B's object, assert 404. Generate it from the OpenAPI path parameters so nobody has to remember.
4. **UUIDv4 or opaque ids are hardening, not authorization.** They raise the cost of enumeration; they do not stop a partner who legitimately learned one id from using it forever.

**If they push back — "can API Management enforce BOLA for us?"** — Not properly, and Microsoft's own guidance says the same: the right place is the backend, because only the backend knows the domain. APIM is a *fallback* for a legacy backend you cannot change — a `send-request` to an authorization service, or a lookup that maps external to internal identifiers. That is a compensating control you document as technical debt, not a design.

---

### Q73. What is API3 — Broken Object Property Level Authorization — and what exactly is mass assignment?
`[HARD]`

> **Spoken:** API3 is BOLA one level down: the caller is allowed to touch the object, but not every *property* of it. It has two directions. Outbound is excessive data exposure — the API returns the whole row and the frontend hides the fields it doesn't want, so the data is one curl away. Inbound is mass assignment — you bind the request body straight onto your model, and the caller sets `role`, `credit_limit` or `kyc_status` because those columns exist. The fix in both directions is the same: an explicit contract. An input DTO that forbids unknown fields, and an output DTO that lists exactly what leaves.

**Vulnerable — mass assignment, the classic three lines:**

```python
@app.patch("/v1/parties/{party_id}")
async def update_party(party_id: str, body: dict, claims: dict = Depends(verify_token)):
    # body = {"display_name": "...", "kyc_status": "VERIFIED", "risk_tier": "LOW"}
    await db.update_party(party_id, **body)   # every column is writable
    return await db.get_party(party_id)       # every column is readable
```

**Fixed — two explicit models, and the framework enforces both:**

```python
from typing import Literal

from fastapi import Depends, FastAPI
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI()


class PartyUpdateRequest(BaseModel):
    # extra="forbid" -> unknown properties are a 422, not a silent write.
    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=140)
    preferred_language: Literal["en", "ta", "hi"] = "en"
    # kyc_status and risk_tier are deliberately absent: they are set by the
    # KYC workflow, never by the party.


class PartyResponse(BaseModel):
    party_id: str
    display_name: str
    preferred_language: str
    # No internal_score, no onboarding_notes, no source_system_row_id.


@app.patch("/v1/parties/{party_id}", response_model=PartyResponse)
async def update_party(
    party_id: str,
    body: PartyUpdateRequest,
    claims: dict = Depends(verify_token),
) -> PartyResponse:
    row = await db.update_party(
        party_id,
        display_name=body.display_name,
        preferred_language=body.preferred_language,
    )
    # response_model re-serialises through PartyResponse, so a new column added
    # to the table tomorrow does not silently appear in the API.
    return PartyResponse(**row)
```

`extra="forbid"` is the whole game on the inbound side and `response_model=` is the whole game on the outbound side. In an integration platform there is a third rule: **never let the API contract be generated from the persistence model.** The moment `PartyResponse` is `orm_mode` over the table, a DBA adding a column ships a data leak.

Belt and braces at the gateway, which is where the platform team can enforce it for teams that haven't adopted the pattern yet — this blocks undocumented properties on the way *in* and on the way *out*:

```xml
<inbound>
    <base />
    <validate-content unspecified-content-type-action="prevent" max-size="102400" size-exceeded-action="prevent" errors-variable-name="reqValidation">
        <content type="application/json" validate-as="json" schema-id="party-update-schema" action="prevent" allow-additional-properties="false" />
    </validate-content>
</inbound>
<outbound>
    <base />
    <validate-content unspecified-content-type-action="detect" max-size="1048576" size-exceeded-action="detect" errors-variable-name="respValidation">
        <content type="application/json" validate-as="json" schema-id="party-response-schema" action="prevent" allow-additional-properties="false" />
    </validate-content>
</outbound>
```

`max-size` is in bytes and the maximum accepted value is **4 MB**; the schema itself is also capped at **4 MB**.

**If they push back — "isn't blocking responses paranoid?"** — It is the cheapest reverse-engineering defence you have. Blocking *requests* with undocumented properties stops the attack; blocking *responses* with undocumented properties stops the attacker learning what to attack. Run the outbound one in `detect` for a sprint, look at the log, then flip it to `prevent`.

---

### Q74. What's the difference between API1 and API5 — object level versus function level authorization?
`[MEDIUM]`

> **Spoken:** API5 is "may this principal call this operation at all" — can a retail user hit `DELETE /v1/admin/parties/{id}`. API1 is "may this principal touch this specific object" — can user A read account B. API5 is enforceable at the gateway, because it depends only on the route plus the claims. API1 is not, because the gateway doesn't know who owns object 4711. So on my platform the gateway owns function-level and the service owns object-level, and neither pretends to do the other's job.

The failure mode for API5 is almost always structural rather than a missing `if`: an admin controller that inherits a permissive base route, a `*` wildcard operation in the gateway that forwards everything, an HTTP method nobody thought about (`PUT` allowed where only `GET` was designed), or a v1 of the API still published with the old, laxer checks.

The paved-road controls:

- **No wildcard operations.** Every operation is declared in the OpenAPI, imported into APIM, and anything undefined returns 404 at the edge. This alone kills a large fraction of API5.
- **Required claims per operation**, not per API:

```xml
<validate-azure-ad-token tenant-id="aaaabbbb-0000-cccc-1111-dddd2222eeee"
                         header-name="Authorization"
                         failed-validation-httpcode="403"
                         failed-validation-error-message="Forbidden">
    <audiences>
        <audience>api://party-api</audience>
    </audiences>
    <required-claims>
        <claim name="roles" match="any">
            <value>Party.Admin</value>
        </claim>
    </required-claims>
</validate-azure-ad-token>
```

- **Admin surface on its own product** with its own subscription, its own IP allow-list, and ideally its own hostname so it can be network-restricted.
- **Monitor 401/403 by operation.** A spike of 403s on one operation from one subscription is either a broken partner or an enumeration attempt, and you want to know which within minutes.

**If they push back — "why 403 for a failed token here but 404 for BOLA?"** — Different information. A missing role is information the caller already has (they know what they registered for), so 403 is honest and debuggable. Object existence is information the caller does *not* have, so it must not leak. Consistency is not the goal; not leaking is.

---

### Q75. How do you stop a single consumer from eating the platform — API4, Unrestricted Resource Consumption?
`[MEDIUM — very likely for a platform role]`

> **Spoken:** Five controls, layered, all of them at the gateway so no team has to reimplement them. Rate limit on a short window to absorb spikes, quota on a long window to enforce the commercial contract, a maximum body size so nobody posts a 200 MB payload, a concurrency limit so one slow partner can't occupy every connection, and a hard timeout on the backend call. Then a WAF bot ruleset in front for the traffic that isn't a legitimate partner at all. The important design decision is what you key on: subscription for commercial limits, but party or IP for abuse limits, because one subscription can be shared by many end users.

The reusable policy fragment — this is a *paved road* artefact, defined once and included by every API:

```xml
<!-- policy fragment: standard-consumption-guardrails -->
<fragment>
    <rate-limit-by-key calls="600"
                       renewal-period="60"
                       counter-key="@(context.Subscription?.Id ?? context.Request.IpAddress)"
                       retry-after-header-name="Retry-After"
                       remaining-calls-header-name="X-RateLimit-Remaining" />
    <quota-by-key calls="500000"
                  renewal-period="86400"
                  counter-key="@(context.Subscription.Id)" />
    <validate-content unspecified-content-type-action="prevent"
                      max-size="262144"
                      size-exceeded-action="prevent"
                      errors-variable-name="sizeValidation">
        <content type="application/json" validate-as="json" action="detect" />
    </validate-content>
    <limit-concurrency key="@(context.Api.Id)" max-count="200">
        <forward-request timeout="20" />
    </limit-concurrency>
</fragment>
```

Included in every API's inbound section with `<include-fragment fragment-id="standard-consumption-guardrails" />`. Note the details: `rate-limit-by-key` falls back to IP when there is no subscription (anonymous or certificate-authenticated callers), `Retry-After` is emitted so a well-behaved client backs off instead of hammering, and `forward-request timeout` is the control that actually protects the gateway — a 20-second backend is 20 seconds of a gateway connection you can't use for anyone else.

Sensitive operations get *stricter* limits, not the same limits: sign-in, password reset, OTP send, bulk export. That is the overlap between API4 and API6.

**If they push back — "rate-limit versus quota, why both?"** — Different jobs. `rate-limit` is a burst control measured in seconds and protects *infrastructure*; `quota` is a volume control measured in days or months and protects the *commercial contract*. A partner on 500k calls/day can still take you down with 500k calls in one minute, which is why the short window exists. Also worth flagging: in APIM, `rate-limit` and `quota` (the by-subscription variants) require a subscription key; `rate-limit-by-key` and `quota-by-key` don't, which is why the fragment uses the by-key forms.

---

### Q76. API9 is Improper Inventory Management. What does that mean for a platform team?
`[MEDIUM — this is the one that sounds boring and scores highest for a platform role]`

> **Spoken:** It means shadow APIs and zombie APIs. Shadow is an endpoint running in production that isn't in any catalogue, so it never got a security review and nobody patches it. Zombie is v1 still answering traffic two years after v3 shipped, running the old, laxer authorization. Both are inventory problems, not code problems, so the fix is a process the platform owns: the OpenAPI spec in git is the only source of truth, CI is the only thing that publishes to the gateway, and there is a written deprecation policy — we support current plus two, and older versions are removed, not just undocumented.

Concretely, what I'd put in place:

| Control | Mechanism |
|---|---|
| One catalogue | Azure API Center as the org-wide inventory, including APIs *not* in APIM (Logic Apps, Functions, legacy IIS) |
| Spec-first | OpenAPI/WSDL lives in the repo; the pipeline imports it; nobody edits an API in the portal — see [CI/CD & GitOps](05-cicd-iac-and-gitops.md) |
| No undocumented surface | No wildcard operations, so an undeclared path 404s at the edge |
| Version discipline | APIM **versions** for breaking changes, **revisions** for non-breaking; N-2 supported; `Sunset` and `Deprecation` headers on the way out — see [API Design](01-api-design-rest-soap-graphql-openapi.md) |
| Environment isolation | Separate APIM instance per environment, each wired to its own Key Vault and backends; never a "test" product on the prod gateway |
| Discovery | Defender for APIs to surface endpoints receiving traffic that aren't in the catalogue |
| Ownership | Every API in the catalogue has an owning team, an on-call rotation and a runbook link, or it doesn't get published |

**If they push back — "how do you find shadow APIs that were never registered?"** — Three sources that don't rely on anyone volunteering information: traffic (WAF/Front Door and NSG flow logs show hostnames and paths nobody declared), DNS (audit every A/CNAME record in the zone against the catalogue), and certificates (certificate transparency logs list every public hostname anyone issued a cert for). Anything in those three that isn't in API Center is shadow by definition.

---

## 12. Platform Security — TLS, CORS, WAF, Secrets, Webhooks, Privacy

### Q77. How do you configure TLS for a public API? What's the minimum, and what do you do about ciphers?
`[MEDIUM — EY-logged style infra question]`

> **Spoken:** TLS 1.2 as the hard floor, TLS 1.3 enabled and preferred, everything below 1.2 off — that's RFC 9325, the current TLS BCP from November 2022, which says implementations MUST NOT negotiate TLS 1.0 or 1.1, MUST support 1.2 and SHOULD support and prefer 1.3. On ciphers, only AEAD suites with ECDHE for forward secrecy: ECDHE-ECDSA or ECDHE-RSA with AES-GCM. No CBC, no 3DES, no static RSA key exchange. And I set it in IaC, not in the portal, so it can't drift.

RFC 9325's four recommended TLS 1.2 suites, which is what you name if they push:

```
TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
```

TLS 1.3 removes the problem entirely — it has five cipher suites, all AEAD, and forward secrecy is mandatory, so there is nothing to misconfigure.

In APIM this is `properties.customProperties` on the service resource, front and back:

```bicep
resource apim 'Microsoft.ApiManagement/service@2024-05-01' = {
  name: apimName
  location: location
  sku: {
    name: 'Premium'
    capacity: 2
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publisherName: 'EY GDS Integration Platform'
    publisherEmail: 'integration-platform@example.com'
    customProperties: {
      // client side
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Ssl30': 'false'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls10': 'false'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls11': 'false'
      // backend side
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Ssl30': 'false'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls10': 'false'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls11': 'false'
      // weak cipher
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Ciphers.TripleDes168': 'false'
    }
  }
}
```

Facts worth having straight: APIM supports **TLS up to 1.3** on both client and backend sides, TLS 1.3 is on by default for client connections in most instances, and backend-side TLS 1.3 is opt-in. The **Consumption, Basic v2, Standard v2 and Premium v2** tiers do **not** allow changing the default cipher configuration — if an interviewer asks "how do you harden ciphers on Standard v2", the correct answer is "you don't; that's a reason to be on Premium classic, or to put Front Door in front." Microsoft retired TLS 1.0/1.1 in APIM in **October 2025**, so on a new instance those toggles are historical anyway.

One caution that catches people out: **TLS 1.3 does not support certificate renegotiation.** If any of your clients renegotiate mid-session for a client certificate, enabling client-side TLS 1.3 breaks them. APIM detects instances that rely on renegotiation and leaves 1.3 off there. Check before you flip it.

Verify from the outside rather than trusting the portal:

```bash
# should FAIL
openssl s_client -connect api.contoso.com:443 -tls1_1 </dev/null

# should SUCCEED and print "Protocol : TLSv1.3"
openssl s_client -connect api.contoso.com:443 -tls1_3 </dev/null 2>/dev/null \
  | grep -E 'Protocol|Cipher'

# full external grade, including chain and HSTS
nmap --script ssl-enum-ciphers -p 443 api.contoso.com
```

**If they push back — "clients still on TLS 1.0, what do you do?"** — Never weaken the shared gateway. Give them a dedicated, time-boxed ingress with its own hostname, its own WAF policy and an agreed sunset date in the contract, log every request that lands on it, and report the list to the risk owner monthly so the migration has a name against it. A financial-services client will already have this as a PCI DSS finding, which is the lever to get it fixed.

---

### Q78. What is HSTS and how do you manage certificates so nothing expires at 2am?
`[MEDIUM]`

> **Spoken:** HSTS is RFC 6797 — a response header that tells the browser "for the next N seconds, never speak to this host over plain HTTP, and don't let the user click through a certificate warning." It closes the gap where the very first request goes out over HTTP and can be stripped. For certificates, the rule is that nothing renews by hand: certificates live in Key Vault, the gateway and Front Door reference the Key Vault secret rather than holding a copy, renewal is automated, and there's an alert on days-to-expiry so a failed renewal is a ticket three weeks early, not an outage.

The header, and the exact preload requirements:

```
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
```

To be accepted on the browser preload list, `max-age` must be **at least 31536000** (one year), `includeSubDomains` must be present, `preload` must be present, and if you listen on port 80 you must redirect to HTTPS on the same host. Do not add `preload` casually — it is slow to reverse and it commits **every** subdomain, including the internal-looking one someone runs over HTTP.

In APIM, set it as a global outbound policy so no team can forget:

```xml
<outbound>
    <base />
    <set-header name="Strict-Transport-Security" exists-action="override">
        <value>max-age=63072000; includeSubDomains</value>
    </set-header>
    <set-header name="X-Content-Type-Options" exists-action="override">
        <value>nosniff</value>
    </set-header>
    <set-header name="Content-Security-Policy" exists-action="override">
        <value>default-src 'none'; frame-ancestors 'none'</value>
    </set-header>
    <set-header name="X-Powered-By" exists-action="delete" />
    <set-header name="Server" exists-action="delete" />
</outbound>
```

Certificate management, the platform version:

- **Store, don't copy.** Certificates are Key Vault certificate objects. APIM, Front Door and App Gateway reference the Key Vault secret ID with a **versionless** URI so the rotated version is picked up automatically, and they read it with a **managed identity**, not a secret.
- **Automate issuance.** Key Vault integrated with a CA (DigiCert/GlobalSign) for auto-renewal, or App Service managed certificates, or an internal ACME issuer. Manual PFX uploads are a future incident.
- **Alert on expiry, not on failure.** An Azure Monitor alert on Key Vault's certificate near-expiry event at 30/14/7 days. Renewal failures are silent; expiry is not.
- **Two clocks to watch.** The public server certificate *and* the client certificates you and your partners present for mTLS. The second one is what actually causes outages, because the partner owns it and doesn't tell you.
- **Cover the internal leg too.** Gateway-to-backend TLS has certificates as well, and a self-signed cert with validation disabled "temporarily" is how internal traffic ends up unauthenticated.

**If they push back — "what breaks when a certificate expires and how fast can you recover?"** — Recovery is only fast if the private key is already in Key Vault and the platform references it by version-less URI: you import the renewed cert and every consumer picks it up without a deployment. If the cert was baked into a container image or an App Service upload, recovery is a full release cycle, in the middle of an incident. That difference is why the rule exists.

---

### Q79. Explain CORS properly. Why can't you use a wildcard origin with credentials?
`[MEDIUM — and the wildcard part is a genuine discriminator]`

> **Spoken:** CORS is a browser-enforced relaxation of the same-origin policy. The browser sends an `Origin` header, and for anything beyond a simple GET or POST it first sends an `OPTIONS` preflight; the server answers with `Access-Control-Allow-Origin` and friends, and the browser decides whether to hand the response to the JavaScript. Two things people get wrong: it is not a server-side security control — curl ignores it entirely — and you cannot combine `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true`. The browser rejects that combination outright, with the error "Credential is not supported if the CORS header 'Access-Control-Allow-Origin' is '*'".

The reason the combination is forbidden is the whole point of CORS. `*` means "any website may read this response." Credentials means "and the browser will attach this user's cookies or Authorization header automatically." Together that is: any site on the internet can make authenticated requests as your logged-in user and read the answers — universal CSRF with read access. So the spec makes it impossible rather than merely discouraged. The same restriction applies to the wildcard in `Access-Control-Allow-Headers`, `Access-Control-Allow-Methods` and `Access-Control-Expose-Headers` when credentials are included: with credentials, `*` is treated as the literal string `*`, not as a wildcard.

Done correctly at the gateway — explicit origins, explicit methods, explicit headers:

```xml
<inbound>
    <cors allow-credentials="true" terminate-unmatched-request="true">
        <allowed-origins>
            <origin>https://portal.contoso.com</origin>
            <origin>https://admin.contoso.com</origin>
        </allowed-origins>
        <allowed-methods preflight-result-max-age="600">
            <method>GET</method>
            <method>POST</method>
            <method>PATCH</method>
            <method>DELETE</method>
        </allowed-methods>
        <allowed-headers>
            <header>authorization</header>
            <header>content-type</header>
            <header>x-correlation-id</header>
        </allowed-headers>
        <expose-headers>
            <header>x-correlation-id</header>
            <header>retry-after</header>
        </expose-headers>
    </cors>
    <base />
</inbound>
```

Three APIM-specific gotchas that are real interview material: the `cors` policy **must be first** in the inbound section or behaviour is undefined (only the first `cors` policy is applied); only `cors` is evaluated on the preflight `OPTIONS`, so your `validate-jwt` doesn't run on preflight and shouldn't need to; and if you set `cors` at *product* scope while the API authenticates by subscription key in a header, it won't work, because the preflight carries no such header.

The equivalent in FastAPI, for a service that isn't behind the gateway:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://portal.contoso.com"],  # never ["*"] with credentials
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["authorization", "content-type", "x-correlation-id"],
    expose_headers=["x-correlation-id"],
    max_age=600,
)
```

If you must support a dynamic list of tenant origins, **reflect** the origin after checking it against an allow-list, and emit `Vary: Origin` so a shared cache never serves tenant A's `Access-Control-Allow-Origin` to tenant B. Reflecting without checking is equivalent to `*` with credentials, only harder to spot in review.

**If they push back — "if CORS is browser-only, why bother?"** — Because the threat it addresses is browser-only: a malicious page abusing a *user's* ambient credentials. It does nothing about a server-to-server attacker, and it is not a substitute for authentication — but it is the only thing standing between your API and a hostile tab the user has open. Server-to-server callers are handled by tokens, mTLS and IP allow-lists, which is why partner APIs usually set no CORS headers at all.

---

### Q80. How do you use a WAF in front of these APIs? Front Door or Application Gateway?
`[MEDIUM — and the false-positive part is what a senior answer contains]`

> **Spoken:** Front Door WAF is global and sits at the Azure edge, so it stops volumetric and geographic attacks before they enter the network — that's my default for anything internet-facing. Application Gateway WAF is regional and lives inside the VNet, so it's what I use in front of an internal-mode APIM or a backend that must not have a public route at all. Plenty of estates run both: Front Door at the edge, App Gateway as the regional entry, with the backends locked to the Front Door service tag and the `X-Azure-FDID` header so nobody can bypass the edge.

The managed ruleset facts, which is where interviewers probe:

| | Front Door WAF | Application Gateway WAF v2 |
|---|---|---|
| Ruleset | Azure **DRS** (2.2, 2.1, 2.0, 1.x) + Bot Manager | OWASP **CRS** 3.0 / 3.1 / 3.2 and DRS |
| Baseline | DRS 2.2 is baselined on **OWASP CRS 3.3.4**; DRS 2.1 on **CRS 3.3.2** | CRS as published |
| Scoring | DRS 2.0+ uses **anomaly scoring** | CRS 3.x anomaly scoring |
| Body inspection | **128 KB** HTTP request body and file upload inspection limit | `max_request_body_size_in_kb` default **128**, `file_upload_limit_in_mb` default **100**, and with CRS 3.2+ the inspection limit is configurable independently and enforcement can be turned off |
| Rate limiting | Yes (native custom rules) | No — rate limiting is a Front Door feature |
| Scope | Global resource, one config across all edge locations | Regional, in-VNet |

**Anomaly scoring**, which is the concept to name: with DRS 2.0 and later a rule match doesn't block on its own. Each rule has a severity that contributes to a score — Critical 5, Error 4, Warning 3, Notice 2 — and the WAF acts when the request reaches **5 or more**. So one Critical match blocks; one Warning match (3) does not. DRS 2.2 runs at **Paranoia Level 1** by default with all PL2 rules disabled; PL2 catches more and false-positives more, and Azure doesn't support PL3/PL4 at all.

**The false-positive reality**, and this is the part that scores:

1. Deploy in **Detection** mode first. Never straight to Prevention on an existing API unless you are actively under attack.
2. Turn on diagnostic logging and read `AzureDiagnostics` / `FrontDoorWebApplicationFirewallLog` daily.
3. Tune with **exclusions scoped as narrowly as possible** — per-rule, not global; by value, not by disabling the rule. The canonical false positive is a JWT in a header tripping SQLi rule 942xxx because of characters in the base64, and the correct fix is an exclusion on `RequestHeaderValues` selector `Authorization` for that rule group, not disabling `REQUEST-942`.
4. Repeat for **weeks**, not days. Microsoft's own guidance says the tuning cycle can take several weeks.
5. Only then switch to **Prevention**, and keep reading the logs.

A per-rule exclusion in Bicep, the shape you'd actually commit:

```bicep
resource wafPolicy 'Microsoft.Network/ApplicationGatewayWebApplicationFirewallPolicies@2023-11-01' = {
  name: 'waf-partner-api-prod'
  location: location
  properties: {
    policySettings: {
      state: 'Enabled'
      mode: 'Prevention'
      requestBodyCheck: true
      maxRequestBodySizeInKb: 128
      fileUploadLimitInMb: 100
    }
    managedRules: {
      managedRuleSets: [
        {
          ruleSetType: 'OWASP'
          ruleSetVersion: '3.2'
        }
      ]
      exclusions: [
        {
          matchVariable: 'RequestHeaderValues'
          selectorMatchOperator: 'Equals'
          selector: 'Authorization'
          exclusionManagedRuleSets: [
            {
              ruleSetType: 'OWASP'
              ruleSetVersion: '3.2'
              ruleGroups: [
                {
                  ruleGroupName: 'REQUEST-942-APPLICATION-ATTACK-SQLI'
                  rules: [
                    { ruleId: '942430' }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  }
}
```

Two limits that bite in real integrations: Front Door WAF inspects only the **first 128 KB** of a body — a large SOAP envelope or a bulk JSON batch passes through mostly uninspected, which is an argument for schema validation at the gateway rather than relying on the WAF. And Front Door WAF **does not decompress** content-encoded bodies, so a gzipped payload isn't inspected at all.

**If they push back — "a WAF blocked a legitimate partner in production at 3am, what do you do?"** — Identify the rule from the `trackingReference` in the 403 response body and the WAF log, put a narrowly-scoped exclusion in place for that rule and that field only, and record it as a temporary change with an expiry. What you do **not** do is flip the whole policy to Detection, because that removes protection for every API on the gateway to fix one partner's payload. Then the follow-up is a schema fix so the payload stops looking like an attack.

---

### Q81. How do you handle secrets? Key Vault access policies or RBAC?
`[MEDIUM — EY-logged style]`

> **Spoken:** RBAC, always, for anything new. Access policies are the legacy model — Microsoft labels them legacy in the docs, and from API version 2026-02-01 Azure RBAC is the default for newly created vaults. RBAC gives you one permission system across the whole estate, assignment at management group down to individual secret, and clean separation between who administers the vault and who can read its data. The bigger point though is that the best secret is the one that doesn't exist: managed identity for anything Azure-to-Azure, so there's no credential to store, rotate or leak.

Why RBAC beats access policies, specifically:

| | Access policies (legacy) | Azure RBAC |
|---|---|---|
| Granularity | Vault-wide per principal | Management group / subscription / RG / vault / individual object |
| Assignment cap | **1024 access policy entries** per vault | Standard role-assignment limits |
| Who can grant | Anyone with `Microsoft.KeyVault/vaults/write` — including `Contributor` — can grant *themselves* data access | Only `Owner` and `User Access Administrator` |
| Auditing | Vault property diff | Central role-assignment history |
| Conditions | None | ABAC conditions (secret name patterns) |

That third row is the security argument to make out loud: with access policies, a `Contributor` on the resource group can silently add themselves an access policy and read every secret. That is a privilege-escalation path that RBAC closes.

The roles you name: **Key Vault Secrets User** (`4633458b-17de-408a-b874-0445c86b69e6`) for read-only runtime access — this is what your app's managed identity gets; **Key Vault Secrets Officer** for the pipeline that writes secrets; **Key Vault Administrator** for break-glass; **Key Vault Reader** for metadata only. Note that **Key Vault Contributor** is control-plane only and grants no access to secret values, which is a favourite trick question.

Terraform for the paved-road vault:

```hcl
resource "azurerm_key_vault" "platform" {
  name                       = "kv-intplat-prod-sin"
  location                   = azurerm_resource_group.platform.location
  resource_group_name        = azurerm_resource_group.platform.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "premium"

  enable_rbac_authorization  = true
  purge_protection_enabled   = true
  soft_delete_retention_days = 90

  public_network_access_enabled = false

  network_acls {
    bypass         = "AzureServices"
    default_action = "Deny"
  }
}

resource "azurerm_role_assignment" "api_reads_secrets" {
  scope                = azurerm_key_vault.platform.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.orders_api.principal_id
}
```

`purge_protection_enabled = true` is not optional in a regulated estate — without it, someone with delete rights can permanently destroy a vault and every key that encrypts your data at rest.

Operational rules I'd state as platform standards:

- **Managed identity first.** A Function reading Service Bus, APIM calling a backend, AKS pulling from ACR — none of these need a secret. See [Azure Integration](02-azure-integration-services.md).
- **Reference, don't copy.** APIM **named values** backed by Key Vault, App Service `@Microsoft.KeyVault(SecretUri=...)` references, AKS via the Secrets Store CSI driver with workload identity. The secret's value never enters a config file or a pipeline variable.
- **Rotate on a schedule and on every leaver.** Two-secret rotation so there is never a gap: publish the new secret, let consumers pick it up (versionless URI or a short cache TTL), then disable the old one, then delete it. Entra app registrations support two client secrets at once precisely for this.
- **Expiry as a tripwire.** Set `exp` on secrets even though Key Vault treats it as informational — then alert on `SecretNearExpiry` events. A secret with no expiry is a secret nobody owns.
- **Vault per app per environment.** Microsoft's own recommendation, and it means a compromised app identity reaches one blast radius, not all of them.

Hard numbers worth knowing: a secret's value is capped at **25 KB**; a vault allows **300 CREATE-secret / IMPORT-certificate / IMPORT-key operations per 10 seconds** collectively and **4,000 other transactions per 10 seconds** per vault per region. That second one is why you cache the secret in memory instead of calling `get_secret()` per request — an API doing 500 rps that fetches its DB password every call will throttle itself with 429s.

**If they push back — "how do you rotate a secret with zero downtime?"** — Overlap. Add the new credential while the old one is still valid, roll consumers, verify with telemetry that nothing is still using the old one (Entra sign-in logs show which key id was used), then revoke. The mistake is rotating first and rolling second, which is a self-inflicted outage.

---

### Q82. How do you make sure secrets never get into git — and what do you do when one does?
`[MEDIUM]`

> **Spoken:** Three layers: a pre-commit hook so it's caught on the developer's laptop, a CI job scanning the full history so a bypassed hook is caught at the PR, and push protection at the platform so it's blocked server-side. I use gitleaks for the first two. And the incident response has a fixed order that people get backwards: rotate the credential first, then clean the history. A secret that has touched a remote is compromised, whether or not you can still see it.

Pre-commit, in the repo template:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.24.2
    hooks:
      - id: gitleaks
```

CI, as a required check:

```yaml
name: security-scan
on:
  pull_request:
  push:
    branches: [main]
  schedule:
    - cron: "0 4 * * *"

permissions:
  contents: read

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0          # full history, or you only scan the tip
      - uses: gitleaks/gitleaks-action@v3
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}
```

`fetch-depth: 0` is the line people forget — without it you scan one commit and the scan is theatre. The gitleaks CLI is MIT-licensed; **gitleaks-action requires a `GITLEAKS_LICENSE` for organisations** (not for personal accounts), which is a procurement fact worth knowing before you propose it at EY. The current CLI verbs are `gitleaks git`, `gitleaks dir` and `gitleaks stdin` — `detect` and `protect` were deprecated in v8.19.0 and are now hidden aliases.

Locally, before you open the PR:

```bash
gitleaks git --redact --verbose /home/nova/work/prep/ey
gitleaks dir  --redact --no-git /path/to/build/output
```

This slots into the JD's "**security scanning**" requirement alongside SAST (CodeQL), dependency scanning (Dependabot / `pip-audit`), container scanning (Trivy) and IaC scanning (Checkov / `tfsec`) — see [CI/CD & GitOps](05-cicd-iac-and-gitops.md). Secret scanning is the one that is cheapest to add and catches the highest-severity class.

**The leak runbook, in order:**

1. **Rotate.** New secret issued, consumers moved, old secret revoked at the issuer. Minutes, not hours.
2. **Assess exposure.** Public repo or private? How long? Fork count? Check the provider's access logs for use of that credential from unexpected IPs — this is the step that tells you whether it's a hygiene issue or an incident.
3. **Then** rewrite history with `git filter-repo` or BFG, force-push, and ask GitHub Support to expire cached views of the old objects. Note that forks and anyone's local clone keep the object, which is exactly why step 1 comes first.
4. **Post-incident:** why did the hook not fire, why did CI not block, and add a rule for that credential shape.

**If they push back — "the secret was only in a private repo, is that really an incident?"** — Treat it as one. Every developer with read access, every CI runner, every laptop backup and every third-party app with repo scope now has it, and none of that is logged. The rotation cost is an hour; the assumption that private equals safe is what turns a hygiene issue into a breach notification.

---

### Q83. A partner wants to register a webhook URL that we call. How do you stop that becoming SSRF?
`[HARD — API7, and a realistic platform scenario]`

> **Spoken:** A user-supplied URL that my server then fetches is the definition of SSRF, and in Azure the prize is the instance metadata endpoint at 169.254.169.254, which will hand out a managed identity token. So: HTTPS only, a host allow-list where the partner registers a domain that we verify out of band, resolve the hostname myself and reject any private, loopback, link-local or metadata address, and then **connect to the IP I validated** rather than re-resolving — otherwise DNS rebinding walks straight through my check. Plus egress through a proxy or a subnet whose NSG can't reach anything internal, so even a bug is contained.

The DNS rebinding point is the one that separates a real answer from a checklist. If you validate `evil.com` (which resolves to a public IP) and then hand the *hostname* to your HTTP client, the attacker's DNS server can return `10.0.0.5` on the second lookup, a second or two later. The check passed; the connection went somewhere else. This is **time-of-check to time-of-use**, and the fix is to pin the address.

```python
import ipaddress
import socket
from urllib.parse import urlsplit

import httpx

ALLOWED_HOSTS = frozenset({
    "hooks.partner-a.example",
    "events.partner-b.example",
})

BLOCKED_NETS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),   # incl. 169.254.169.254 (IMDS)
    ipaddress.ip_network("100.64.0.0/10"),    # CGNAT
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),         # unique local
    ipaddress.ip_network("fe80::/10"),        # link local
]


class SsrfBlocked(Exception):
    pass


def _assert_public(ip: str) -> None:
    addr = ipaddress.ip_address(ip)
    if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
        raise SsrfBlocked(f"non-public address {ip}")
    for net in BLOCKED_NETS:
        if addr.version == net.version and addr in net:
            raise SsrfBlocked(f"blocked network {ip}")


def resolve_and_validate(url: str) -> tuple[str, str, int]:
    """Return (host, pinned_ip, port) or raise. Every A/AAAA record must pass."""
    parts = urlsplit(url)
    if parts.scheme != "https":
        raise SsrfBlocked("https required")
    host = parts.hostname or ""
    if host.lower() not in ALLOWED_HOSTS:
        raise SsrfBlocked(f"host {host!r} not registered")
    port = parts.port or 443
    if port != 443:
        raise SsrfBlocked("port 443 only")

    infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    ips = {info[4][0] for info in infos}
    if not ips:
        raise SsrfBlocked("no address")
    for ip in ips:
        _assert_public(ip)          # ALL records must pass, not just the first
    return host, sorted(ips)[0], port


async def post_webhook(url: str, body: bytes, headers: dict[str, str]) -> int:
    host, pinned_ip, port = resolve_and_validate(url)

    # Connect to the validated IP; keep the Host header and TLS SNI/cert
    # validation on the real hostname. This is what defeats DNS rebinding.
    transport = httpx.AsyncHTTPTransport(retries=0)
    async with httpx.AsyncClient(
        transport=transport,
        timeout=httpx.Timeout(connect=3.0, read=10.0, write=10.0, pool=3.0),
        follow_redirects=False,          # a 302 to 169.254.169.254 undoes everything
        verify=True,
    ) as client:
        request = client.build_request(
            "POST",
            f"https://{pinned_ip}:{port}{urlsplit(url).path or '/'}",
            content=body,
            headers={**headers, "Host": host},
            extensions={"sni_hostname": host},
        )
        response = await client.send(request)
        return response.status_code
```

The controls in that code, named:

| Control | Why |
|---|---|
| `https` only, port 443 only | No `file://`, `gopher://`, no internal service on 8080 |
| Registered host allow-list | The strongest control; verified out of band at onboarding (DNS TXT record or a signed email from the partner's security contact) |
| Every resolved record checked | A hostname with two A records where one is private otherwise slips through |
| Pin the IP, keep Host + SNI | Closes DNS rebinding while keeping certificate validation honest |
| `follow_redirects=False` | A 302 is a second, unvalidated fetch — this is the most common bypass |
| Tight connect/read timeouts | Stops SSRF being used as a port scanner via timing, and protects your own thread pool |

And two things code can't do, so infrastructure must: send this traffic **from a dedicated egress subnet** whose NSG and route table allow only outbound 443 to the internet and nothing to your VNets, and prefer **IMDS-free compute** or block 169.254.169.254 at the host firewall for the process doing the fetching. Defence in depth, because someone will eventually add a "just fetch this URL" feature without reading this function.

**If they push back — "why not just block private IPs and be done?"** — Because a blocklist loses to encodings, redirects, IPv6-mapped IPv4 (`::ffff:10.0.0.1`), decimal IP notation, and DNS you don't control. An **allow-list of registered hostnames plus IP pinning** is a positive security model; the blocklist is the last line, not the first.

---

### Q84. How do you secure a webhook that a third party sends *to* us?
`[HARD — the mirror image of Q83, and just as likely]`

> **Spoken:** HMAC signature over the exact raw body, plus a timestamp inside the signed material, plus a replay window, plus an idempotency key. Signature verified with a constant-time comparison. The two things people get wrong are signing the parsed-and-re-serialised JSON instead of the raw bytes — which fails as soon as key ordering or whitespace changes — and using `==` to compare digests, which leaks the correct signature byte by byte through timing. Everything else, like IP allow-listing the sender, is a useful extra but not the control.

This is exactly how Stripe does it and it's worth citing because it's the reference implementation: the `Stripe-Signature` header carries `t=<unix timestamp>` and one or more `v1=<hex hmac>` values; the signed payload is `f"{t}.{raw_body}"`; the MAC is HMAC-SHA256 with the endpoint's signing secret; you ignore any scheme that isn't `v1`; you compare in constant time; and the libraries default to a **5-minute (300 second) tolerance** on the timestamp. GitHub does the same thing with `X-Hub-Signature-256: sha256=<hex>` over the raw body.

Real, complete verification in FastAPI:

```python
import hashlib
import hmac
import os
import time

from fastapi import APIRouter, Header, HTTPException, Request, status

router = APIRouter()

SIGNING_SECRETS: dict[str, bytes] = {
    # keyed by secret id so you can rotate with an overlap window
    "v2026-01": os.environ["WEBHOOK_SECRET_V2026_01"].encode(),
    "v2025-07": os.environ["WEBHOOK_SECRET_V2025_07"].encode(),
}
TOLERANCE_SECONDS = 300          # 5 minutes, same as Stripe's default
MAX_BODY_BYTES = 1 * 1024 * 1024  # 1 MiB


def _parse_signature_header(header: str) -> tuple[int, list[str]]:
    """Parse 't=1492774577,v1=abc...,v1=def...' -> (timestamp, [signatures])."""
    timestamp = -1
    signatures: list[str] = []
    for element in header.split(","):
        key, _, value = element.strip().partition("=")
        if key == "t":
            timestamp = int(value)
        elif key == "v1":              # ignore v0 and any future scheme
            signatures.append(value)
    if timestamp < 0 or not signatures:
        raise ValueError("malformed signature header")
    return timestamp, signatures


def verify(raw_body: bytes, signature_header: str, secret: bytes) -> None:
    timestamp, signatures = _parse_signature_header(signature_header)

    # 1. Replay window. The timestamp is INSIDE the signed payload, so an
    #    attacker cannot move it without invalidating the MAC.
    age = abs(time.time() - timestamp)
    if age > TOLERANCE_SECONDS:
        raise ValueError(f"timestamp outside tolerance ({age:.0f}s)")

    # 2. Signed payload is the timestamp, a dot, and the RAW body bytes.
    signed_payload = f"{timestamp}.".encode() + raw_body
    expected = hmac.new(secret, signed_payload, hashlib.sha256).hexdigest()

    # 3. Constant-time comparison against every offered v1 signature.
    if not any(hmac.compare_digest(expected, candidate) for candidate in signatures):
        raise ValueError("signature mismatch")


@router.post("/webhooks/partner-a", status_code=status.HTTP_202_ACCEPTED)
async def receive(
    request: Request,
    x_partner_signature: str = Header(...),
    x_partner_key_id: str = Header("v2026-01"),
    x_partner_event_id: str = Header(...),
):
    # Read the RAW body. Never re-serialise before verifying.
    raw = await request.body()
    if len(raw) > MAX_BODY_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "payload too large")

    secret = SIGNING_SECRETS.get(x_partner_key_id)
    if secret is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "unknown key id")

    try:
        verify(raw, x_partner_signature, secret)
    except ValueError:
        # Do not echo the reason: it tells an attacker whether the MAC or the
        # timestamp failed. Log the detail internally with the event id.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid signature")

    # 4. Idempotency. Signature valid does not mean "not already processed".
    if not await claim_event_id(x_partner_event_id, ttl_seconds=7 * 24 * 3600):
        return {"status": "duplicate"}

    # 5. Accept fast, process async. Enqueue and return 202 immediately.
    await enqueue(raw, event_id=x_partner_event_id)
    return {"status": "accepted"}
```

Why each numbered step exists:

1. **Timestamp + tolerance** turns "valid forever" into "valid for five minutes." Without it, a captured request can be replayed in a year. Never set the tolerance to zero — that disables the check entirely rather than tightening it.
2. **Raw bytes.** `json.dumps(await request.json())` will not round-trip: key order, unicode escaping, float formatting and whitespace all differ. In FastAPI/Starlette, read `await request.body()`; in Flask, `request.get_data()`; and make sure no middleware has consumed or rewritten the stream first.
3. **`hmac.compare_digest`**, never `==`. Python's `==` on strings short-circuits at the first differing byte, and that timing difference is enough to forge a signature over enough requests.
4. **Idempotency** because at-least-once delivery is the norm — Stripe retries with exponential backoff for up to three days and generates a *new* signature and timestamp per attempt, so signature uniqueness is not a dedupe key. Use the sender's event id. See [Messaging](03-messaging-and-event-streaming.md) for the dedupe-store pattern.
5. **202 then async**, because the sender's timeout is short and slow handlers cause retry storms that look exactly like an attack.

Rotation: the `key id` header is what lets you accept two secrets at once during a rollover, which is how you rotate a partner's signing secret without a coordinated outage. Stripe does the same by emitting one signature per active secret for up to 24 hours.

**If they push back — "why not just require mTLS or an API key on the webhook?"** — mTLS is stronger and I'll take it when the partner supports it, but many SaaS senders don't, and behind a TLS-terminating CDN the backend often can't see the client cert anyway. A shared API key in a header is weaker than HMAC because it's replayable and it's transmitted on every call, so anything that logs headers leaks it permanently. HMAC never transmits the secret. Best answer: mTLS for transport plus HMAC for message integrity, and IP allow-list as a third, low-cost layer.

---

### Q85. Where do you enforce input validation and request size limits?
`[MEDIUM]`

> **Spoken:** At every layer, because each one protects something different, and the outermost limit must be the largest. WAF caps what it can inspect, the gateway enforces the contract, the service enforces the domain rules, and the database enforces the invariants. The rule I apply is positive validation: declare what is allowed and reject everything else, rather than trying to enumerate what's malicious.

| Layer | Control | Real number to quote |
|---|---|---|
| Front Door WAF | Inspects the first 128 KB of body; blocks on anomaly score ≥ 5 | 128 KB, score 5 |
| App Gateway WAF | `maxRequestBodySizeInKb`, `fileUploadLimitInMb`, `requestBodyInspectLimitInKB` | defaults 128 KB / 100 MB / 128 KB, with a 4 KB buffer on the upload limit |
| APIM | `validate-content max-size` + `validate-parameters` + `validate-headers` | `max-size` max value 4 MB; schema max 4 MB |
| Service | Pydantic models with `extra="forbid"`, `Field(max_length=...)`, `Literal[...]` enums, and an explicit max array length | 422 on violation |
| Database | `NOT NULL`, `CHECK`, foreign keys, column widths | Last line, and the only one nobody can bypass |

The bit people miss: **size limits must be consistent and decreasing inward**. If APIM allows 4 MB but the Function App's host caps at 100 MB and the WAF inspects 128 KB, then a 1 MB malicious payload is uninspected by the WAF, accepted by the gateway, and lands on your code. Write the numbers down as one table per API and enforce them in IaC.

Also declare the constraints in the OpenAPI spec itself — `maxLength`, `pattern`, `minimum`, `maxItems`, `enum` — because then `validate-content` and `validate-parameters` enforce them for free at the gateway, and the generated client enforces them at the caller. One source of truth, three enforcement points. See [API Design](01-api-design-rest-soap-graphql-openapi.md).

**If they push back — "isn't validating at the gateway and the service duplication?"** — It's defence in depth with different failure modes. The gateway protects the backend from traffic that should never reach it and gives you one place to tighten a rule across every service in an incident. The service protects the domain and still works when someone calls it from inside the VNet, bypassing the gateway. Remove either and you have a gap.

---

### Q86. What does PII minimisation mean in an integration platform, and what about data residency?
`[MEDIUM — high value for a financial-services-led role]`

> **Spoken:** Minimisation means the pipeline carries the least data that satisfies the use case, for the shortest time. In an integration platform that's concrete: don't put PII in the message when a reference will do, don't log the payload, mask on the way out, and set retention on every store the data touches — including the ones nobody thinks of, like dead-letter queues and blob-based claim-check storage. Residency means knowing which region every hop physically lives in, including the DR pair and the log workspace, because a European client's data ending up in a Log Analytics workspace in another geography is a compliance finding even though nobody "moved" anything.

Concrete patterns for an integration layer:

- **Reference, don't carry.** The event says `{"party_id": "P-88213", "event": "kyc.verified"}`, not the PAN, the date of birth and the address. Consumers that need the detail call the API with their own token and get object-level authorization applied. This also fixes the "we can't delete it, it's in Kafka forever" problem.
- **Tokenise or mask at the edge.** Account numbers become last-4 plus a token; the mapping lives in one service with its own vault. See [FS](12-financial-services-integration.md) for the payments-specific version.
- **Never log the body by default.** In APIM, diagnostic settings let you log request/response bodies up to a byte limit — leave it at zero for any API touching PII and enable it per-incident, with an expiry, for one operation.
- **Dead-letter queues are a data store.** A DLQ full of unprocessable messages containing PII, with no retention policy, is a shadow database. Set TTL, and encrypt.
- **Claim-check blobs** need lifecycle rules, private endpoints and customer-managed keys if the client requires it.
- **Retention everywhere.** Log Analytics workspace retention, Application Insights retention, Service Bus message TTL, blob lifecycle, database archive. Each of them defaults to something that was chosen for convenience, not for compliance.

Residency, practically:

- Pin every resource's region in Terraform/Bicep and enforce it with **Azure Policy** (`allowedLocations`) at the management-group scope, so a well-meaning engineer cannot create a resource in the wrong geography.
- Check the **paired region** used for geo-redundancy — for India that's Central India ↔ South India, so data stays in-country; for a client requiring EU-only, the DR region must also be EU.
- Check **the services that are global by nature**: Entra ID, Front Door, Traffic Manager, and the metadata plane of many services. Know which of your data actually flows through them.
- Check **the log path**. Telemetry is data. A Log Analytics workspace in a different geography is the most common accidental transfer.

**If they push back — "the client asks whether their data leaves India."** — The honest answer is a data-flow diagram, not a yes. List every hop, its region, its retention and its encryption, including logs, backups, DR and any SaaS in the chain. Then name the controls that keep it that way: Azure Policy on allowed locations, private endpoints so traffic doesn't traverse the public internet, customer-managed keys if required, and an annual review. That answer is what a bank's risk team is actually asking for.

---

### Q87. What do GDPR and India's DPDP Act mean for you as an integration engineer?
`[MEDIUM — Chennai-based, financial-services client base; expect it]`

> **Spoken:** Both make design decisions I own. Data minimisation and purpose limitation mean the pipeline carries less; the right to erasure means I need to be able to find and delete one person's data across every store the integration touches, including queues and logs; and breach notification puts a clock on my observability. GDPR is 72 hours to the supervisory authority under Article 33. India's DPDP Act 2023 with the DPDP Rules notified in November 2025 is stricter in shape — notify the affected individual and the Data Protection Board without delay, then a detailed report to the Board within 72 hours — with penalties up to ₹250 crore for failing to have reasonable security safeguards and ₹200 crore for failing to notify.

| | GDPR | India DPDP Act 2023 + DPDP Rules 2025 |
|---|---|---|
| Roles | Controller / Processor | Data Fiduciary / Data Processor; individual is the **Data Principal** |
| Breach notification | Art. 33: without undue delay, **not later than 72 hours** to the supervisory authority; if later, give reasons. Processor tells controller without undue delay | Rule 7: intimate the affected Data Principal **and** the Board without delay; detailed report to the Board **within 72 hours** (extension on written request) |
| Individual notification | Art. 34: only where high risk to rights and freedoms | Required for every personal data breach |
| Erasure | Art. 17, right to erasure | Erasure on consent withdrawal / purpose completion |
| Penalties | Up to €20m or 4% of global turnover | Fixed rupee ceilings: up to **₹250 crore** (failure of reasonable security safeguards), up to **₹200 crore** (failure to notify) — no turnover formula |
| Timeline | In force since 2018 | Rules notified **13 Nov 2025**, phased compliance runway of about 18 months |

What that actually changes in my design:

1. **Erasure is an architecture problem, not a ticket.** If a party id fans out to six systems, a Kafka topic with infinite retention and a blob archive, "delete this person" is impossible. Reference-not-carry (Q86) makes it tractable: delete in the system of record, and the events referencing the id become meaningless rather than incriminating. Compacted topics with a tombstone are the Kafka answer — see [Messaging](03-messaging-and-event-streaming.md).
2. **Breach notification is an observability requirement.** A 72-hour clock that starts when you *become aware* means detection latency is compliance risk. Concretely: alerting on anomalous data egress, on 403 spikes, on unusual bulk-export volumes; audit logs retained long enough to answer "what did they access"; and a runbook with the notification template pre-written so the clock is spent investigating, not drafting.
3. **Processor obligations flow down.** Every SaaS in the integration chain is a sub-processor. That means a DPA, a residency commitment and a breach-notification SLA in *their* contract that is shorter than yours, or you cannot meet your own deadline.
4. **Consent and purpose become message metadata** in some designs: the event carries the purpose it was collected for, and a consumer outside that purpose refuses it.

**If they push back — "have you actually done this?"** — Be honest and specific: describe the controls you built (retention on queues, masked logging, an erasure path, egress alerting) and say that the legal determination sits with the client's DPO and EY's privacy team. Claiming you owned the legal interpretation is a bad answer; claiming you built the mechanisms that make it enforceable is the right one.

---

### Q88. What does good audit logging look like — and how do you guarantee a token never lands in a log?
`[MEDIUM]`

> **Spoken:** An audit event answers who, what, which object, when, from where and what the outcome was — and it never contains the credential. I get that guarantee structurally, not by discipline: a redacting log filter with an allow-list of loggable fields, `Authorization` and `Cookie` stripped at the gateway before diagnostics, request bodies off by default, and a CI test that asserts a known secret string never appears in output. Then a correlation id threaded end to end so an auditor can reconstruct one transaction across the gateway, the queue and three services.

The schema for an audit event:

```json
{
  "timestamp": "2026-08-25T09:14:22.481Z",
  "correlation_id": "7f3a1b9c-2e44-4a71-9d1f-8c0b6e5a3d21",
  "actor": {
    "subject": "oid:6f9b1c22-...", 
    "tenant": "aaaabbbb-0000-cccc-1111-dddd2222eeee",
    "client_id": "11112222-bbbb-3333-cccc-4444dddd5555",
    "party_id": "P-88213"
  },
  "action": "statements.read",
  "object": { "type": "account", "id": "ACC-4711" },
  "outcome": "denied",
  "reason_code": "not_owner",
  "source_ip": "203.0.113.44",
  "api": { "name": "party-api", "version": "v2", "operation": "getStatements" }
}
```

Note what is **not** there: no token, no token hash you could brute-force, no request body, no email address, no account number. The actor is an opaque subject id; the object is a type and an id. And `outcome: denied` is logged as loudly as `allowed` — a BOLA attempt is only visible if failures are audited.

Guaranteeing no tokens, mechanically:

```python
import logging
import re

REDACTIONS = [
    (re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._\-]+"), r"\1 [REDACTED]"),
    (re.compile(r"(?i)(\"?(authorization|cookie|set-cookie|x-api-key|"
                r"ocp-apim-subscription-key|client_secret|password|"
                r"refresh_token|id_token|access_token)\"?\s*[:=]\s*)"
                r"(\"[^\"]*\"|\S+)"), r"\1[REDACTED]"),
    (re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"), "[JWT]"),
]


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern, replacement in REDACTIONS:
            message = pattern.sub(replacement, message)
        record.msg = message
        record.args = ()
        return True


def install() -> None:
    handler = logging.StreamHandler()
    handler.addFilter(RedactingFilter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
```

Then the test that makes it real, in CI:

```python
def test_no_token_reaches_logs(client, caplog):
    token = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.c2lnbmF0dXJl"
    client.get("/v1/accounts/ACC-1/statements",
               headers={"Authorization": f"Bearer {token}"})
    assert token not in caplog.text
    assert "[REDACTED]" in caplog.text or "[JWT]" in caplog.text
```

At the gateway, strip before the log rather than after — an APIM diagnostic setting can be told which headers to log, and the safe default is a short allow-list:

```xml
<inbound>
    <base />
    <!-- Never forward the caller's credential material to the backend or the trace -->
    <set-header name="Ocp-Apim-Subscription-Key" exists-action="delete" />
    <set-variable name="correlationId"
                  value="@(context.Request.Headers.GetValueOrDefault("X-Correlation-Id", context.RequestId.ToString()))" />
    <set-header name="X-Correlation-Id" exists-action="override">
        <value>@((string)context.Variables["correlationId"])</value>
    </set-header>
</inbound>
```

Retention and integrity matter as much as content: audit logs go to an immutable store (Log Analytics with the required retention, or a storage account with an immutability policy), separate from application logs, with access restricted to the security team — because an attacker who can edit your audit log has erased the incident.

**If they push back — "how do you investigate an incident if you don't log bodies?"** — Correlation ids plus targeted, time-boxed enablement. The audit trail tells you *which* transactions to look at; then you enable body logging for one operation, for a defined window, with an approval, and turn it off. Always-on body logging is a permanent copy of every payload in a system with weaker access controls than the source — which is a bigger risk than slower forensics.

---

## 13. Zero Trust & The Partner-API Scenario

### Q89. What does "zero trust" actually mean for an integration platform?

> "It means you stop treating the network as a security boundary. There is no 'inside' — every call authenticates and authorises on its own merits, whether it came from the internet or from the pod next door. The three working principles are verify explicitly, least privilege, and assume breach.
>
> Concretely on an integration platform: every service-to-service hop carries a token or a client certificate, not an IP allowlist. Every identity is a managed identity with a scoped role assignment, not a shared service account with Contributor. Backends sit behind private endpoints so the gateway is the only reachable path — but the backend *still* validates the token, because 'it came through the gateway' is a network assumption and network assumptions are what zero trust removes."

**If they push back — "isn't validating twice wasteful?"** — It's a few hundred microseconds against the cost of a gateway misconfiguration exposing an unauthenticated backend. Defence in depth is cheap here. What I *wouldn't* do is duplicate business authorisation logic in both places — the gateway does coarse-grained checks (valid token, right audience, right scope, within quota), the backend does object-level authorisation, which only it can do.

### Q90. Walk me through securing an API that a client's partner consumes, end to end.

**This is the scenario question. Ninety seconds, no notes.**

> "Layered, outside in.
>
> **Edge** — Front Door or Application Gateway with a WAF on the OWASP Core Rule Set, TLS 1.2 minimum, DDoS protection. This absorbs the volumetric and generic-attack traffic before it reaches anything that costs money to run.
>
> **Gateway** — APIM. Partner authentication is mutual TLS, because for a partner integration the certificate is a contractual artefact and it's stronger than a shared secret. On top of that, `validate-jwt` if there's a token, and a subscription key so I know *which* partner is calling for metering. Then `quota-by-key` and `rate-limit-by-key` per partner, so one partner's runaway batch job can't starve the others.
>
> **Contract** — an OpenAPI spec with request validation enforced at the gateway, so a malformed or oversized payload never reaches the backend. Response validation too if the backend is legacy and might leak fields.
>
> **Backend** — a private endpoint, unreachable except through the gateway. APIM authenticates to it with its managed identity. Every secret in Key Vault, referenced as a named value, never inline. And the backend independently validates the token and enforces object-level authorisation — partner A must not be able to enumerate partner B's records by changing an ID.
>
> **Data** — tokenised identifiers rather than raw ones, field-level encryption for anything sensitive, and PII minimisation so we're not storing what we don't need.
>
> **Operations** — a correlation ID injected at the gateway and propagated through every hop. An audit log of every call with the partner identity, the operation and the outcome — and never the token itself. Alerts on 401/403 spikes, on quota exhaustion, and on a partner suddenly changing their traffic shape.
>
> **Lifecycle** — the part people forget: certificate expiry monitoring with enough lead time to actually rotate, a documented key-rotation procedure using primary/secondary, and a runbook for revoking a partner's access in minutes if their credentials are compromised."

**If they push back — "the partner says mTLS is too hard, can they just use an API key?"** — Then I'd want compensating controls and I'd want the risk written down and accepted by someone senior: IP allowlisting to their egress ranges, a short rotation period, request signing with HMAC over the body plus a timestamp so a stolen key alone isn't sufficient, and tighter rate limits. But I'd say plainly that an API key alone is identification, not authentication, and for a financial-services flow that's usually not defensible to an auditor. See [Financial Services Integration](12-financial-services-integration.md).

### Q91. How do you revoke a partner's access in an incident?

> "Fast path first: disable their APIM subscription — that kills the key immediately across every gateway instance. If they're on mTLS, revoke or remove the client certificate from the validation set. Both take effect at the gateway without a deployment.
>
> Then the token problem. If they hold JWTs, those stay valid until expiry because that's the trade-off of stateless validation. So the mitigation has to be designed in beforehand: short access-token lifetimes so the window is minutes, plus revoking the client's ability to get a *new* token by disabling the app registration or the credential.
>
> Then containment: check the audit log for what that identity did in the exposure window, and whether it accessed anything outside its normal pattern. That's why the audit log needs to carry the partner identity per call — without it you can't scope the incident."

**If they push back — "how fast?"** — Subscription disable and certificate removal are effectively immediate. Full token expiry is bounded by your access-token lifetime, which is why I argue for 5–15 minutes rather than an hour on partner-facing APIs.

### Q92. A client asks: how do we know an integration is secure? What do you show them?

> "I'd show evidence rather than assertions, in four parts.
>
> **Design** — a threat model for the flow: what the trust boundaries are, what an attacker would target, and the control at each boundary. One page, not a document nobody reads.
>
> **Build** — the pipeline output. SAST, dependency, container and IaC scan results, an SBOM per build, and signed images. That answers 'is the code safe' with artefacts rather than opinion.
>
> **Runtime** — the actual gateway policy, the RBAC assignments, the network topology showing private endpoints, and evidence that no secret exists outside Key Vault.
>
> **Operations** — the audit trail, the alerting, and the runbook for revocation and rotation. Plus a penetration test if the engagement warrants it.
>
> The thing I'd emphasise is that most of this should be a by-product of how the platform is built, not a document someone writes at the end. If producing the evidence is a project, the controls aren't real."

---

## Interviewer Traps

Twelve places candidates give a plausible answer that a security-literate interviewer marks down.

| # | Most candidates say | The correct answer |
|---|---|---|
| 1 | "I validate the JWT signature, so the token is good." | Signature validity is **authentication, not authorisation**. A perfectly valid token from the right issuer still doesn't mean this subject may read *this* record. Object-level authorisation lives in your code and is in no token. |
| 2 | "I use the id_token to call the API." | Never. The `id_token`'s audience is the **client**, it carries no scopes, and accepting it means anyone who can sign a user in to any app can call your API. Access tokens only. |
| 3 | "OAuth handles authentication." | OAuth 2.0 is an **authorisation** framework. Authentication is OIDC, layered on top. Getting this backwards in the first sentence is a fast way to lose a security interviewer. |
| 4 | "I check `exp` and the signature." | Incomplete. The checklist is signature via JWKS by `kid`, **pinned algorithms** (never trust the token's own `alg`), `iss`, `aud`, `exp`, `nbf`, scopes/roles — then object-level authz separately. Missing `aud` means a valid token minted for a different API is accepted at yours. |
| 5 | "We use the implicit flow for our SPA." | Deprecated. Tokens in the URL fragment leak via history, referrers and logs. `authorization_code` + **PKCE** is the answer for every client type now, confidential clients included. |
| 6 | "API keys are fine, they're secret." | An API key is a bearer secret with no expiry, no audience, no scopes and no user context. It's **identification and quota**, not authentication. If it's the only control, that's a finding. |
| 7 | "We store the refresh token in localStorage." | XSS-readable. Refresh tokens belong in an `HttpOnly`, `Secure`, `SameSite` cookie, or in a backend-for-frontend that holds them server-side. And they should **rotate**, so reuse detection can spot theft. |
| 8 | "`Access-Control-Allow-Origin: *` makes CORS work." | It's incompatible with `credentials: include` — the browser rejects the combination outright. Echo a validated origin from an allowlist. And CORS is a **browser** control; it protects nobody from a direct HTTP client. |
| 9 | "We verify the webhook HMAC against the parsed JSON." | Verify against the **raw body bytes** — reserialising changes whitespace and key order and the signature won't match. Also compare in constant time, and enforce a timestamp replay window, or a captured request is replayable forever. |
| 10 | "The backend is on a private endpoint, so it doesn't need to check the token." | That's a network assumption, which is exactly what zero trust removes. One gateway misconfiguration or one compromised pod in the VNet and the backend is wide open. Validate at both layers. |
| 11 | "We rotate the client secret every 90 days." | Better answer: have **no secret**. Managed identity for Azure-to-Azure, workload identity federation for CI, `private_key_jwt` or mTLS for external clients. A credential that doesn't exist can't leak or expire at 2am. |
| 12 | "We log the request including headers for debugging." | You just wrote bearer tokens and API keys into your log store, which usually has broader access than the API does. Redact `Authorization`, `Cookie` and any key header at the logging layer, and test that the redaction works. |

---

## 30-Second Whiteboard Versions

Three scripts to memorise verbatim.

**(a) "How do you secure a service-to-service call?"**

> "Client credentials with a managed identity — so there's no secret anywhere. The calling service asks the platform for a token scoped to the target API's audience. The target validates it at the gateway with `validate-jwt` against Entra: signature via JWKS, issuer, audience, and a required role claim. Then the service itself checks object-level authorisation, because the token says who's calling, not what they're allowed to touch. Token lifetime short, transport TLS 1.2 minimum, and the whole hop carries a correlation ID."

**(b) "Validate this JWT."**

> "Eight checks. Signature, using the public key from the JWKS endpoint selected by the `kid` header — cached, refreshed on an unknown `kid` so rotation doesn't page me. Algorithm pinned to what I accept, never read from the token. Issuer exact. Audience is my API. `exp` not passed, `nbf` reached, small clock skew only. Then scopes or roles authorise the operation. Then object-level authorisation in my code — may *this* subject touch *this* record. The last one is OWASP API #1 and it's the one that gets skipped."

**(c) "Why can't you just revoke a JWT?"**

> "Because stateless validation is the whole point — the API doesn't call the issuer, so it can't learn the token was revoked. That's a deliberate trade: throughput for immediacy. Three mitigations. Short lifetimes, five to fifteen minutes, so the window is small and revocation lands at refresh. A `jti` deny-list for the cases that genuinely need instant kill, sized by the remaining token lifetime. Or reference tokens with introspection, which gives real-time revocation at the cost of a call per request. I'd pick short lifetimes plus refresh-token rotation for most integrations."

---

## Rapid Fire

| # | Q | A |
|---|---|---|
| 1 | Four OAuth roles? | Resource owner, client, authorization server, resource server. |
| 2 | OAuth = authn or authz? | Authorisation. Authentication is OIDC on top. |
| 3 | Grant for service-to-service? | `client_credentials` — better still, managed identity. |
| 4 | Grant for a user-facing app? | `authorization_code` + PKCE. |
| 5 | Why is implicit dead? | Token in the URL fragment — leaks via history, referrer, logs. |
| 6 | Why is ROPC forbidden? | The app handles the user's actual password; breaks MFA and federation. |
| 7 | What does PKCE stop? | Authorization-code interception — the code is useless without the `code_verifier`. |
| 8 | `state` vs `nonce`? | `state` = CSRF on the redirect; `nonce` = replay of the `id_token`. |
| 9 | id_token vs access_token? | id_token is *about the user, for the client*. access_token is *for the API*. Never swap them. |
| 10 | What's in a JWT? | Header, payload, signature — base64url, dot-separated. Signed, **not encrypted**. |
| 11 | JWS vs JWE? | JWS = signed, readable. JWE = encrypted, opaque. |
| 12 | `alg: none` attack? | Attacker strips the signature; a naive library accepts it. Pin accepted algorithms. |
| 13 | HS256 confusion attack? | Attacker signs with your RSA public key as an HMAC secret. Same fix: pin the algorithm. |
| 14 | What is `kid` for? | Selects which JWKS key verifies this token — enables rotation. |
| 15 | JWKS caching rule? | Cache it; refresh on an unknown `kid`. Don't fetch per request, don't cache forever. |
| 16 | Why check `aud`? | Stops a valid token minted for another API being replayed at yours. |
| 17 | Can you revoke a JWT? | Not directly. Short TTL + refresh rotation, a `jti` deny-list, or reference tokens. |
| 18 | Introspection vs local validation? | Real-time revocation vs a network hop per request. |
| 19 | `private_key_jwt`? | Client authenticates with a signed assertion instead of a shared secret. |
| 20 | RFC 8705? | mTLS client authentication and certificate-bound access tokens. |
| 21 | DPoP (RFC 9449)? | Proof-of-possession — binds the token to a key so a stolen token alone is useless. |
| 22 | RFC 8693? | Token exchange — delegation and on-behalf-of. |
| 23 | RFC 8707? | Resource indicators — request a token for a specific target API. |
| 24 | Discovery document path? | `/.well-known/openid-configuration`. |
| 25 | System vs user-assigned MI? | System dies with the resource; user-assigned is independent and shareable across resources. |
| 26 | Delegated vs application permission? | Delegated acts *as a signed-in user*; application acts *as itself*, admin consent only. |
| 27 | `scp` vs `roles` claim? | `scp` = delegated scopes (user consented). `roles` = app roles or app-only permissions. |
| 28 | Entra `aud` gotcha? | v1 tokens may carry the `api://` URI, v2 the client ID — validate what your issuer actually mints. |
| 29 | Workload identity federation? | CI or a pod presents an OIDC token; Entra trusts it and issues a real token. No stored secret. |
| 30 | APIM policy that validates tokens? | `validate-jwt` — with `openid-config` URL, required claims, audiences, issuers. |
| 31 | Where do policies compose? | Global → product → API → operation, with `<base />` marking the parent. |
| 32 | APIM throttling policies? | `rate-limit-by-key` (short burst) and `quota-by-key` (long-window volume). |
| 33 | What is a subscription key for? | Identifying the calling app for metering and quota. Not authentication. |
| 34 | Key rotation mechanic? | Primary/secondary pair — issue the new one, migrate, retire the old. Zero downtime. |
| 35 | mTLS in one line? | Both sides present certificates; the server authenticates the client at the transport layer. |
| 36 | Real cost of mTLS? | Certificate lifecycle — distribution, expiry monitoring, rotation. Not the handshake. |
| 37 | Where do you terminate mTLS? | APIM or App Gateway for north-south; a mesh sidecar for east-west. |
| 38 | OWASP API #1? | Broken Object Level Authorization (BOLA) — the most-exploited API flaw. |
| 39 | Fix for BOLA? | Authorise against the *object*, per request, server-side. Never trust an ID from the client. |
| 40 | Mass assignment fix? | Explicit allowlist binding — never bind the request body straight onto your model. |
| 41 | SSRF via webhooks? | User supplies a URL, your server fetches it. Allowlist destinations; block link-local and internal ranges. |
| 42 | Webhook signature done right? | HMAC over the **raw body**, plus a timestamp and a replay window, compared in constant time. |
| 43 | Minimum TLS? | 1.2. Prefer 1.3. Add HSTS on browser-facing endpoints. |
| 44 | CORS wildcard + credentials? | Impossible — the browser rejects it. Echo a validated origin from an allowlist. |
| 45 | Is CORS a security control? | Only for browsers. It stops nobody using a direct HTTP client. |
| 46 | Where do secrets live? | Key Vault, referenced by managed identity. Ideally there is no secret at all. |
| 47 | Secret committed to git — now what? | Rotate first, *then* purge history. The rewrite doesn't un-leak it. |
| 48 | What must never be logged? | `Authorization`, `Cookie`, API keys, PII. Redact at the logging layer and test it. |
| 49 | 401 vs 403? | 401 = not authenticated. 403 = authenticated, not permitted. |
| 50 | Why 404 instead of 403 sometimes? | To avoid confirming a resource exists to a caller who shouldn't know. |

---

*Companions: [API Design](01-api-design-rest-soap-graphql-openapi.md) · [Azure Integration Services](02-azure-integration-services.md) · [CI/CD, IaC & GitOps](05-cicd-iac-and-gitops.md) · [Financial Services](12-financial-services-integration.md) · [PLAN.md](PLAN.md) · [ANSWERS.md](ANSWERS.md)*
