# CustomerSupportAgent — Complete 20 Production Queries & Answers

*Aarka AI Technical Reference Encyclopedia*

---

## [Q01] How do I reset my account password if I didn't receive the email reset link?

### Customer Support Runbook: Account Password Reset & Email Delivery Troubleshooting

#### 1. Immediate Self-Service Resolution Protocol
If an account password reset link has not arrived within 5 minutes of request:
1. **Spam & Security Filter Audit:** Check junk, spam, quarantine, and promotional folders for emails originating from `auth@aarka.ai` or your custom domain identity.
2. **Corporate Email Gateway Quarantine:** Institutional domains (e.g., hedge funds, banks) frequently quarantine automated transactional emails with password reset tokens. Check with your network security administrator to ensure SPF, DKIM, and DMARC passes for `aarka.ai`.
3. **SSO / Federated Identity Account Check:** If your organization provisioned your seat via SAML 2.0 or Google Workspace / Okta Single Sign-On (SSO), password management is handled directly by your enterprise Identity Provider (IdP), and local password reset will be disabled.

#### 2. Alternative Recovery Workflow: CLI / Organization Admin Reset
* **Organization Admin Override:** An organization administrator (Owner or Admin role) can navigate to **Settings > Team Management > Members**, locate the user profile, and trigger an **Admin-Assisted Password Reset Link** or issue a temporary 15-minute access token.
* **CLI Recovery (For Developer/API Accounts):**
  ```bash
  # Authenticate with account recovery key provided during account setup
  python -m aarka.cli auth recovery-session --email user@firm.com --recovery-key <RECOVERY_KEY>
  ```

#### 3. Escalation & Identity Verification Policy
If email delivery issues persist:
* Submit a ticket to `support@aarka.ai` with the subject `[URGENT] Password Reset Delivery Failure - <Account Email>`.
* *Security Protocol:* Support engineers **never** ask for your password or plaintext recovery keys. Password resets can only be dispatched to the verified domain administrator upon cryptographic confirmation of identity.

*Compliance Notice: All authentication events are logged with IP, user-agent, and timestamp for SOC2 Type II audit compliance.*

---

## [Q02] Where can I find my active portfolio holdings and watchlist on the platform?

### Platform Navigation Runbook: Portfolio Holdings, Watchlists & Execution States

#### 1. Active Portfolio Holdings Navigation
To inspect active positions, capital allocation, and real-time mark-to-market P&L:
1. **Web Dashboard:** Log in to the Aarka terminal at `https://app.aarka.ai` and select **Portfolio** from the left navigation rail.
2. **Key Metric Tiles:**
   * **Total Net Asset Value (NAV):** Cash equivalents + long equity market value - borrow obligations.
   * **Realized vs. Unrealized P&L:** Realized P&L tracks completed FIFO lot closures; Unrealized P&L reflects live tick mark-to-market against average weighted acquisition cost.
   * **Factor & Sector Exposures:** Automated decomposition across Nifty 50 sectors, market-cap buckets, and Beta sensitivity.

#### 2. Multi-Watchlist Configuration & Real-Time Streaming
1. Navigate to **Markets > Watchlists** (`/markets/watchlists`).
2. **Create New Watchlist:** Click `+ New Watchlist`, assign an institutional desk label (e.g., `High-Beta Momentum`, `Nifty IT Coverage`), and input ticker symbols (supporting both NSE ticker symbols like `RELIANCE.NS` and standard ISINs).
3. **Custom Column Layouts:** Configure column headers to display Bid-Ask Spread, 14-day RSI, 50/200 EMA distance, and implied volatility (IV) percentiles.

#### 3. Programmatic Access via Python SDK
```python
from aarka import AarkaClient

client = AarkaClient(api_key="your_api_key")
# Fetch current live portfolio positions
positions = client.portfolio.get_positions(status="ACTIVE")
print(f"Total Active Holdings: {len(positions)}")

# Stream live watchlist quotes via WebSocket
client.stream.subscribe_watchlist(watchlist_id="wl_nifty50_core")
```

*Disclaimer: Real-time tick feeds require active exchange market data subscription licenses (NSE Level 2).*

---

## [Q03] What are the subscription tiers available and how do I upgrade to Pro or Enterprise?

### Enterprise Subscription Tiers, Feature Matrix & Upgrade Protocol

#### 1. Tier Comparison Matrix
| Capability | Free Community Tier | Professional (Pro) | Enterprise Desk |
| :--- | :--- | :--- | :--- |
| **Market Data Latency** | 15-minute delayed EOD | Real-time NSE Level 1 / L2 streaming | Direct Ultra-Low Latency L3 / FIX Feed |
| **API Rate Limits** | 60 requests / minute | 1,200 requests / minute | Dedicated unmetered instance / VPC |
| **Multi-Agent Orchestration** | Up to 2 concurrent agents | 12 specialized agents concurrent | Custom swarm pipelines (SPARC / ruflo) |
| **Custom Sandbox / Code Mode** | 200MB memory, 1 vCPU | 2GB memory, 2 vCPUs | Dedicated Kubernetes Pods (GPU acceleration) |
| **SLA & Support** | Community Discord / Forum | 8-hour email SLA | 24/7 dedicated Slack / Teams desk, 1-hour SLA |

#### 2. How to Upgrade to Pro or Enterprise
1. **Self-Service Pro Upgrade:**
   * Navigate to **Settings > Billing & Subscriptions** (`/settings/billing`).
   * Select **Pro Tier**, choose monthly or discounted annual billing, and enter corporate card details via our PCI-DSS Level 1 compliant Stripe checkout.
   * Pro entitlements activate immediately without service restart or session revocation.
2. **Enterprise Contract Procurement:**
   * Enterprise tiers require custom Master Services Agreements (MSA), SOC2 / ISO 27001 compliance reviews, and optional on-premise air-gapped deployment configurations.
   * Contact `sales@aarka.ai` or your account executive to schedule an architectural sizing session.

*Billing Notice: Invoices are rendered in USD or INR with applicable statutory GST / VAT tax breakdowns.*

---

## [Q04] How do I set up a price alert notification for a specific stock ticker?

### Automated Market Alerts Runbook: Setting Up Price & Technical Indicator Triggers

#### 1. Setting Up Real-Time Price Alerts
To trigger real-time notifications when an asset reaches target valuation or price levels:
1. Navigate to **Markets > Alerts Engine** (`/markets/alerts`) or open any security terminal page.
2. Click the **Alert Bell Icon** in the top right header.
3. Configure trigger parameters:
   * **Target Asset:** Input ticker or ISIN (e.g., `TATAMOTORS` / `INE155A01022`).
   * **Condition:** Select trigger criteria (`Price >= Target`, `Price <= Target`, `Daily Change % >= +3.0%`).
   * **Execution Mode:** Choose `One-shot` (deactivates upon first fill) or `Persistent Recurring` (triggers on each breach with a 15-minute re-arm cooldown).

#### 2. Advanced Multi-Factor & Indicator Alerts
The Aarka Alert Engine supports composite quantitative conditions:
* **Moving Average Cross:** `50 EMA crosses above 200 EMA on 1D timeframe`.
* **Volatility Squeeze:** `Bollinger BandWidth <= 5.0% AND Volume >= 2.0x 20-day SMA`.
* **RSI Extreme:** `14-period RSI <= 30 on 1-hour bar`.

#### 3. Programmatic Alert Dispatch Configuration via Python SDK
```python
from aarka import AarkaClient

client = AarkaClient(api_key="your_api_key")
alert = client.alerts.create(
    symbol="INFY",
    condition="RSI_14 <= 32.0",
    timeframe="1D",
    channels=["WEBHOOK", "SLACK"],
    webhook_url="https://hooks.slack.com/services/T00/B00/X00"
)
print(f"Alert registered successfully with ID: {alert.id}")
```

*Disclaimer: Alert dispatch latency is typically under 150ms on real-time feeds, but network delivery over cellular/email may be subject to external carrier latencies.*

---

## [Q05] Why is my API rate limit being exceeded on the free tier plan?

### API Rate Limiting Diagnostics & HTTP 429 Optimization Runbook

#### 1. Understanding Platform Rate Limits
When the API gateway detects request velocity exceeding plan limits, it responds with **`HTTP 429 Too Many Requests`**.
Every API response headers includes rate-limit telemetry:
* `X-RateLimit-Limit`: Maximum allowable requests per sliding window.
* `X-RateLimit-Remaining`: Count of unused requests remaining in the current window.
* `X-RateLimit-Reset`: Unix epoch timestamp indicating when the current quota replenishes.
* `Retry-After`: Recommended backoff wait time in integer seconds.

#### 2. Client-Side Optimization: Exponential Backoff & Jitter
To prevent thundering-herd API starvation, implement an exponential backoff decorator with full jitter:
```python
import time
import random
import requests

def request_with_backoff(url, headers, max_retries=5):
    delay = 1.0  # Base delay 1 second
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        if response.status_code != 429:
            return response
        
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            sleep_time = float(retry_after)
        else:
            sleep_time = delay * (2 ** attempt) + random.uniform(0, 0.5)
        
        time.sleep(sleep_time)
    raise RuntimeError("Exceeded maximum API retries under rate limit.")
```

#### 3. Upgrading Quota & Batching Alternatives
* **Use Bulk Endpoints:** Instead of querying single tickers in a loop (`GET /quotes?ticker=TCS`, `GET /quotes?ticker=INFY`), use the batched endpoint: `POST /quotes/batch` accepting up to 100 tickers per call.
* **Request Quota Increase:** Pro and Enterprise accounts can request customized throughput limits by submitting an API quota request under **Settings > API Access > Request Limit Increase**.

---

## [Q06] How do I securely connect my GitHub account to enable automated PR reviews?

### GitHub Integration Runbook: Automated PR Code Reviews & Security Audits

#### 1. OAuth App Installation & Repository Permissions
1. Navigate to **Settings > Integrations > GitHub** (`/settings/integrations/github`).
2. Click **Connect GitHub Account**. You will be redirected to GitHub's authorization portal.
3. **Repository Selection:** Choose whether to grant access to:
   * *All Repositories:* Automatically detects any new repository created under your organization.
   * *Selected Repositories:* Grants read/write access strictly to designated repository paths.
4. **Mandatory Scopes:**
   * `repo` (Full control for private repositories) or `public_repo` (For open-source projects).
   * `pull_requests:write` (Allows Aarka agents to post inline comments and review approvals).
   * `checks:write` (Enables Aarka status badges in GitHub Checks API).

#### 2. Workflow Automation Configuration: `.github/workflows/aarka.yml`
For teams requiring headless CI/CD pipeline verification, add the official GitHub Action:
```yaml
name: Aarka Autonomous PR Review
on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  aarka-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Aarka Quantitative & Security Review
        uses: aarkaa-ai/pr-reviewer-action@v2
        with:
          api-key: ${{ secrets.AARKA_API_KEY }}
          fail-on-critical: true
          min-coverage-threshold: 85
```

#### 3. Security Boundary & Token Storage
* GitHub tokens are encrypted at rest using AES-256-GCM and never shared across organization tenants.
* Tokens can be revoked at any time either from the Aarka Integrations page or directly in GitHub via **Settings > Applications > Authorized OAuth Apps > Aarka AI > Revoke Access**.

---

## [Q07] Where can I download my generated PDF financial and compliance reports?

### Document Generation Runbook: Downloading PDF Financial & Compliance Reports

#### 1. Locating & Downloading Generated Documents
All reports generated by Aarka agents (Valuation Memorandums, Technical Screeners, Tax Lot Audits, and Strategy Backtests) are persisted in the user's sandboxed document store:
1. **Web Terminal Access:** Navigate to **Documents > Generated Reports** (`/documents/reports`).
2. **Filters:** Filter reports by generation date, document type (e.g., `Valuation DCF`, `Screener Export`, `Audit Memo`), or originating agent.
3. **Download:** Click the **Download PDF** icon. Files are transferred over TLS 1.3 via pre-signed, time-limited URLs (15-minute TTL).

#### 2. Automated Programmatic Retrieval via Python SDK
```python
from aarka import AarkaClient

client = AarkaClient(api_key="your_api_key")
# List recent financial documents
docs = client.documents.list(limit=5, doc_type="PDF")
for d in docs:
    print(f"ID: {d.id} | Title: {d.title} | Pages: {d.page_count}")
    # Download binary PDF bytes
    client.documents.download(d.id, destination_path=f"./{d.filename}")
```

#### 3. Document Integrity & Digital Signatures
* Every generated PDF report includes an embedded SHA-256 document checksum and generation timestamp in the metadata block.
* *Enterprise Feature:* Enterprise clients can enable cryptographic PDF watermarking and digital document signing conforming to PAdES (PDF Advanced Electronic Signatures) standards for regulatory filings.

---

## [Q08] What should I do if a paper trade order status remains in pending state?

### Order Execution Troubleshooting: Resolving Pending Paper Trade Order States

#### 1. Why Do Paper Trade Orders Remain in Pending State?
In Aarka's paper trading execution engine, orders simulate real-world exchange matching rules rather than executing instantly at fictitious mid-market prices.
Common causes of pending status:
1. **Limit Price Out of Market:** If you placed a **Limit Buy** at ₹2,800 for a stock currently trading at ₹2,850, the order will remain in `PENDING_OPEN` state until a tick trade occurs at or below ₹2,800.
2. **Outside Regular Exchange Hours:** Market and limit orders submitted outside official trading hours ($09:15 - 15:30	ext{ IST}$ for NSE) remain queued in `PENDING_EXCHANGE_OPEN` until the pre-open auction ($09:00 - 09:08$) completes.
3. **Simulated Order Book Depth & Liquidity Constraints:** For large orders, the execution simulator models real order book depth. If volume is insufficient at the limit level, orders enter `PARTIALLY_FILLED` state until sufficient tick volume accumulates.

#### 2. Cancelling or Modifying a Pending Order
* **Web UI:** Navigate to **Trading > Order Book > Open Orders**, locate the pending order ID, and click **Cancel** or **Modify Price/Qty**.
* **Python SDK:**
  ```python
  client.trading.cancel_order(order_id="ord_paper_98231")
  ```

#### 3. Simulating Immediate Fills in Testing
* When developing automated algorithms, toggle the order type to **Market Order** or enable the sandbox flag `immediate_fill_mode=True` to bypass exchange matching queue simulation.

---

## [Q09] How do I invite team members to my organization workspace?

### Organization & Team Management: Role-Based Access Control (RBAC) & Member Invitations

#### 1. Inviting Team Members
Organization Owners and Administrators can provision team seats:
1. Navigate to **Settings > Organization > Members** (`/settings/organization/members`).
2. Click **Invite Member**.
3. Input the user's corporate email address and assign an explicit RBAC role.
4. An encrypted invitation token will be dispatched via email. The recipient has 7 days to complete registration.

#### 2. Role-Based Access Control (RBAC) Permissions Matrix
| Role | Market Data & Terminal | Strategy & Trading | Code Mode / Sandbox | Billing & Invoicing | User Administration |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Owner** | Full Access | Full Access | Full Access | Full Access | Full Access |
| **Admin** | Full Access | Full Access | Full Access | View Only | Full Access |
| **Quant / Developer** | Full Access | Paper & Live Trading | Full Sandbox Access | No Access | No Access |
| **Analyst** | Full Access | View Only / Paper | Read-Only | No Access | No Access |
| **Compliance / Auditor** | Full Read-Only | Audit Log Access | Audit Log Access | Invoices View | No Access |

#### 3. SSO / SCIM Directory Synchronization
* Enterprise plans support **SCIM 2.0 (System for Cross-domain Identity Management)** with Okta, Microsoft Entra ID (Azure AD), and Google Workspace, allowing automated provisioning and de-provisioning based on corporate directory group memberships.

---

## [Q10] Is two-factor authentication (2FA) supported and how do I enable TOTP?

### Two-Factor Authentication (2FA) Implementation: TOTP Setup & Backup Recovery Codes

#### 1. Enabling Time-Based One-Time Password (TOTP) 2FA
1. Navigate to **Settings > Security > Two-Factor Authentication** (`/settings/security/2fa`).
2. Click **Enable 2FA**. Re-enter your account password to verify identity.
3. A QR code and alphanumeric secret key conforming to RFC 6238 (TOTP) will be displayed.
4. Open your preferred authenticator app (Google Authenticator, Microsoft Authenticator, 1Password, or YubiKey Authenticator) and scan the QR code.
5. Enter the 6-digit verification code generated by your app and click **Verify & Activate**.

#### 2. Secure Storage of Backup Recovery Codes
* Upon successful activation, the terminal displays **10 single-use emergency backup recovery codes**.
* *Crucial Protocol:* Copy and store these recovery codes in an encrypted password manager or secure vault. If your physical mobile device is lost or wiped, backup codes are the **only** automated mechanism to regain account access.

#### 3. Enterprise Enforcement
* Organization administrators can enforce mandatory 2FA across all workspace members under **Settings > Organization > Security Policies > Enforce Mandatory 2FA for All Members**.

---

## [Q11] Why is market data showing delayed prices outside active trading hours?

### Market Data Latency & Exchange Session Timings Diagnostics

#### 1. Delayed Prices vs. Real-Time Streaming Ticks
* **Free Community Tier:** Market data feeds for NSE and BSE equities are subject to a **15-minute statutory exchange delay** during active trading hours.
* **Pro & Enterprise Tiers:** Transmit real-time, zero-delay tick feeds directly via WebSocket streams connected to exchange colocation gateways.

#### 2. Exchange Session Schedule (National Stock Exchange of India - NSE)
All times are Indian Standard Time ($	ext{IST} = 	ext{UTC} + 5:30$):
* **09:00 - 09:08:** Order collection and modification window (Pre-open session).
* **09:08 - 09:12:** Order matching and discovery of opening equilibrium prices.
* **09:12 - 09:15:** Buffer period transitioning to regular trading.
* **09:15 - 15:30:** Continuous regular trading session.
* **15:30 - 15:40:** Closing price calculation (weighted average of trades between 15:00 and 15:30).
* **15:40 - 16:00:** Post-closing session (trades executed strictly at closing price).

#### 3. Off-Hours Behavior
Outside 09:15 - 15:30 IST and on declared exchange holidays, tickers display the official **End-of-Day (EOD) Closing Settlement Price**. Weekend or holiday order entries remain in queued state until the next trading day's pre-market session.

---

## [Q12] How do I export my historical trading performance data to CSV or Excel?

### Data Export Runbook: Extracting Historical Trading Performance to CSV and Excel

#### 1. Web Terminal Manual Export
1. Navigate to **Trading > Analytics > Performance Journal** (`/trading/analytics/journal`).
2. Set date range filter (e.g., `Current FY`, `Trailing 12 Months`, or custom date bounds).
3. Click **Export Data** in the upper right corner.
4. Select target format:
   * **CSV (Comma-Separated Values):** Raw, lightweight transaction records suitable for algorithmic backtesting and Python pandas analysis.
   * **Excel (.xlsx):** Structured workbook with pre-configured sheets: *Trade Journal*, *FIFO Lot P&L Realization*, *Capital Gains Tax Summary*, and *Equity Curve Data*.

#### 2. Programmatic Export via Python API
```python
from aarka import AarkaClient
import pandas as pd

client = AarkaClient(api_key="your_api_key")
raw_trades = client.portfolio.get_trade_history(
    start_date="2024-04-01",
    end_date="2025-03-31",
    format="records"
)
df = pd.DataFrame(raw_trades)
df.to_csv("fy24_25_trade_history.csv", index=False)
print(f"Exported {len(df)} transactions to CSV.")
```

#### 3. Audit Trail & Data Provenance
* Export files include comprehensive execution parameters: Execution Timestamp (UTC and IST), Ticker, ISIN, Order Side (BUY/SELL), Quantity, Fill Price, Gross Amount, Brokerage, Exchange Transaction Charges, STT, Stamp Duty, GST, and Net Settlement Amount.

---

## [Q13] What payment methods and invoicing currencies are supported for enterprise billing?

### Enterprise Billing, Currency Support & Payment Processing

#### 1. Supported Payment Rails & Currencies
* **Credit & Debit Cards:** Visa, MasterCard, American Express, and RuPay (processed via Stripe PCI-DSS Level 1 compliant gateway).
* **Direct Bank Transfer / Wire Rails:**
  * *Domestic India:* NEFT, RTGS, and IMPS in Indian Rupees (INR) with automated GST invoicing.
  * *International / US / EU:* Automated Clearing House (ACH) in USD, SEPA credit transfers in EUR, and global SWIFT wire transfers.

#### 2. Statutory Invoicing & Tax Documentation
* Monthly invoices are dispatched automatically on the 1st of each calendar month to your registered billing email.
* Invoices reflect statutory tax breakdowns:
  * For Indian Entities: Corporate GSTIN, State Code, and CGST/SGST/IGST breakdown.
  * For International Entities: Reverse-charge VAT / Tax Exemption Certificate IDs.
* Download invoices at **Settings > Billing > Invoice History**.

---

## [Q14] How do I revoke an API key that was accidentally exposed?

### Security Emergency Runbook: Revoking & Rotating Exposed API Keys

#### 1. Immediate Incident Response Protocol
If an API key is accidentally committed to a public GitHub repository, exposed in client-side code, or suspected of unauthorized use:
1. **Instant Revocation via Web Dashboard:**
   * Immediately navigate to **Settings > API Access** (`/settings/api`).
   * Locate the compromised API key card and click **Revoke Key Immediately**.
   * Confirmation terminates all active WebSocket connections and invalidates subsequent HTTP requests within **under 500 milliseconds**.
2. **Emergency Revocation via CLI (Without Browser):**
   ```bash
   python -m aarka.cli key revoke --key-id <KEY_ID> --master-secret <MASTER_SECRET>
   ```

#### 2. Zero-Downtime Rotation Procedure
1. Create a **New API Key** under **Settings > API Access > Generate Key**, assigning appropriate action-scoped permissions (e.g., Read-Only vs. Trading).
2. Deploy the new key to your production environment variables (e.g., AWS Secrets Manager, HashiCorp Vault, Kubernetes Secrets).
3. Verify that production telemetry reflects successful requests under the new Key ID.
4. Revoke the old API key.

*Security Best Practice: Never hardcode API keys in source files; inject keys strictly via environment variables (`AARKA_API_KEY`).*

---

## [Q15] Why am I getting a permission denied error when attempting to run code mode sandbox scripts?

### Sandbox & Code Mode Execution: Permission Denied Diagnostics & Containment Boundaries

#### 1. Understanding the Execution Sandbox
Aarka executes user code within hardened, unprivileged micro-containers designed to isolate compute environments:
* **User Identity:** Container runs as an unprivileged user (`appuser:appgroup` UID 10001), not root.
* **Filesystem Boundary:** Write access is strictly restricted to designated temporary workspaces (`/tmp/workspace` or `SAFE_WORK_DIR`). System directories (`/etc`, `/usr`, `/bin`, `C:\Windows`, `AppData`) are strictly read-only or masked.
* **Network Boundary:** Outbound network sockets to raw IPs are blocked by default to prevent data exfiltration. Only authorized API endpoints and approved market data webhooks are accessible.

#### 2. Resolving "Permission Denied" Errors
1. **Attempting to Write to Restricted Paths:** If your code writes output files to the current root directory (`open('output.csv', 'w')`), redirect the output to the sandboxed scratch workspace:
   ```python
   import os
   output_dir = os.environ.get("SAFE_WORK_DIR", "./scratch")
   with open(os.path.join(output_dir, "output.csv"), "w") as f:
       f.write(data)
   ```
2. **Subprocess Shell Spawning:** Calling `subprocess.Popen(..., shell=True)` is blocked by security policies. Use safe argument arrays without shell interpolation:
   ```python
   import subprocess
   subprocess.run(["python", "script.py"], shell=False)
   ```
3. **Elevated Capabilities:** Operations requiring `sudo`, raw packet capture (`AF_PACKET`), or kernel module loading are prohibited in multi-tenant environments.

---

## [Q16] How can I delete my personal account and request data erasure under GDPR?

### Data Privacy & Account Deletion Protocol: GDPR & Indian DPDP Act Compliance

#### 1. Submitting an Account Deletion & Data Erasure Request
Under the European General Data Protection Regulation (GDPR Article 17) and the Digital Personal Data Protection (DPDP) Act:
1. Log in to your account and navigate to **Settings > Privacy & Compliance** (`/settings/privacy`).
2. Scroll to the **Account Erasure** section and click **Request Permanent Deletion**.
3. Confirm identity by providing your account password and the 6-digit TOTP code.

#### 2. Data Erasure Timeline & Statutory Retention Requirements
* **30-Day Reversible Grace Period:** The account enters a suspended state for 30 calendar days, during which you can cancel deletion by contacting support.
* **Permanent Purge After 30 Days:** All personal identifiers, watchlists, custom strategies, API keys, and conversation transcripts are permanently purged from active production databases and vector stores.
* **Statutory Compliance Exception:** Financial trade execution records and tax invoices are retained for **7 years** pursuant to statutory mandates from securities regulators (SEBI, SEC) and anti-money laundering (PMLA) regulations.

---

## [Q17] Where can I check system health, uptime status, and scheduled maintenance windows?

### Platform Health, Status Monitoring & Scheduled Maintenance Windows

#### 1. Real-Time System Status & Component Uptime
* Check the public system status page at `https://status.aarka.ai` for live telemetry across all core services:
  * API Gateway & Authentication Service
  * Real-Time WebSocket Market Data Feeds (NSE Level 1 / L2)
  * Multi-Agent Orchestration Engine
  * Autonomous Code Sandbox Runners
* Historical 90-day uptime and incident post-mortems are publicly disclosed.

#### 2. Automated Programmatic Health Check Endpoint
To integrate health checks into your monitoring stack (e.g., Datadog, Prometheus):
```bash
curl -i http://138.91.105.85/health
```
Returns a structured JSON payload:
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "modules": {
    "database": "ok",
    "embeddings": "ok",
    "aarkaa_engine": "ok (live)",
    "skills": "ok (51 skills)"
  }
}
```

#### 3. Maintenance Window Policy
* Standard maintenance windows occur on **Saturdays between 02:00 and 04:00 UTC** (outside all global trading exchange sessions). Scheduled disruptions are announced at least 72 hours in advance via dashboard banners and email alerts.

---

## [Q18] How do I customize the default risk metrics on my portfolio dashboard?

### Customizing Risk Metrics on the Institutional Portfolio Dashboard

#### 1. Modifying Default Risk Parameters
1. Navigate to **Portfolio > Risk Analytics** (`/portfolio/risk`).
2. Click the **Risk Configuration (Gear Icon)** in the top right control bar.
3. **Configurable Parameters:**
   * **Value at Risk (VaR) Confidence Level:** Toggle between **$95\%$** (standard regulatory reporting) and **$99\%$** (conservative stress testing).
   * **VaR Methodology:** Select *Historical Simulation* (default 252-day lookback), *Parametric Variance-Covariance*, or *Monte Carlo Simulation* (10,000 iterations).
   * **Benchmark Index for Beta & Sharpe:** Select the market benchmark (Nifty 50, Nifty 500, S&P 500, or a custom synthetic benchmark).
   * **Risk-Free Rate ($R_f$):** Input your firm's operational cost of capital or select the live 91-day Government of India Treasury Bill yield (typically $\sim 6.5 - 6.8\%$).

#### 2. Custom Dashboard Widget Layouts
* Drag and drop analytics widgets to rearrange your view: *Rolling Drawdown Chart*, *Sector Concentration Treemap*, *Factor Exposure Radar*, and *Component VaR Decomposition*.

---

## [Q19] What is the policy for reporting a potential security vulnerability or bug?

### Responsible Security Vulnerability Disclosure & Bug Bounty Program

#### 1. Vulnerability Reporting Channels
Aarka is committed to maintaining the highest security posture for financial institutional workloads:
* **Primary Security Inbox:** Submit vulnerability reports to `security@aarka.ai`.
* **Encrypted Submissions:** For sensitive exploit payloads, encrypt your email using our official security PGP key (Fingerprint: `A4D8 9C12 7B33 EF45 8890 1204 55CB A901 3E72 88FA`).
* **HackerOne Bug Bounty Program:** Qualified researchers can report vulnerabilities via our bug bounty portal at `https://hackerone.com/aarka-ai`.

#### 2. Safe Harbor & Responsible Disclosure Rules
We provide full Safe Harbor protection to security researchers who adhere to:
* Make a good-faith effort to avoid privacy violations, data destruction, and interruption of services.
* Do not access, modify, or exfiltrate customer account data.
* Allow the Aarka security engineering team a **90-day coordinated disclosure period** to triage, remediate, and verify the patch before publishing vulnerability details.

---

## [Q20] How do I configure email vs in-app push notifications for market alerts?

### Notification Channel Configuration: Email, Webhooks, and In-App Push

#### 1. Managing Notification Preferences
1. Navigate to **Settings > Notifications** (`/settings/notifications`).
2. Configure notification channels across alert categories:
   * **Critical Account Alerts (Password changes, new IP logins, 2FA updates):** Strictly delivered via Email + SMS for security assurance.
   * **Market & Price Alerts:** Toggle between In-App Toast, Mobile Push Notification, and Email Summary.
   * **Strategy Execution & Order Fills:** Configure instant Webhook dispatch for systematic order tracking.

#### 2. Custom Webhook Endpoint Integration
To receive alert payloads directly on your internal server:
1. Under **Settings > Notifications > Webhooks**, click **Add Webhook Endpoint**.
2. Input your HTTPS destination URL (e.g., `https://api.yourfirm.com/webhooks/aarka`).
3. Select trigger events: `alert.triggered`, `order.filled`, `portfolio.stop_loss_hit`.
4. Copy the **Webhook Signing Secret** (`whsec_...`) used to verify incoming HMAC-SHA256 signatures in the `X-Aarka-Signature` request header.

---

