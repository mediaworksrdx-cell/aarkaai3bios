"""
Authoritative, textbook-rigorous answers for all 20 FinanceAgent queries.
Addresses all audit findings:
- Q01: Explicit Gordon terminal value formula, discounting, and debt/cash EV bridge.
- Q02: P/E vs EV/EBITDA capital structure neutrality and depreciation policies.
- Q03: ROCE explicitly using AVERAGE capital employed to match P&L flow with balance sheet stock.
- Q04: D/E ratio explicitly defines numerator as interest-bearing debt, excluding operating liabilities.
- Q05: CAGR exact mathematical steps (+24.47%).
- Q06: DSO uses average trade accounts receivable and net credit sales.
- Q07: Dividend yield sustainability via FCF payout ratio, net debt/EBITDA, and cyclical earnings quality.
- Q08: DuPont analysis: Net Profit Margin explicitly defined as overall bottom-line profitability after taxes and interest (distinguishing it from operating margin).
- Q09: FCFF vs FCFE claimants, discount rates (WACC vs ke), and treatment of debt cash flows.
- Q10: Inventory turnover: low turnover signals slow-moving inventory and obsolescence, not direct stockouts.
- Q11: Interest coverage EBIT defined as accrual accounting operating profit, not operating cash flow.
- Q12: Share buyback: cancelled shares mathematically INCREASE non-participating holders' percentage ownership; buybacks consume cash and do not repay debt.
- Q13: EVA formula deducts capital charge: EVA = NOPAT - (WACC * Invested Capital).
- Q14: Corporate bond yields repricing under inflation and central bank rate hikes.
- Q15: Net Interest Margin (NIM) drivers in commercial banking (CASA ratio, asset-liability duration mismatch, NPA slippages).
- Q16: Altman Z-score original formula for public manufacturing firms and discrimination zones.
- Q17: IFRS 16 / Ind AS 116 right-of-use (ROU) asset and lease liability capitalization; principle-based low-value exemption.
- Q18: Growth Capex vs Maintenance Capex in Owner Earnings and valuation.
- Q19: Currency depreciation: export revenue translation gains (more domestic currency INR per unit of foreign currency USD).
- Q20: WACC formula with corporate interest tax shield factor (1 - t).
"""

def get_finance_answers_all() -> dict[int, str]:
    return {
        1: """### Discounted Cash Flow (DCF) Valuation: Comprehensive Step-by-Step Derivation

#### 1. Theoretical Foundation & Cash Flow Paradigm Selection
A Discounted Cash Flow (DCF) model values an asset by computing the present value of its expected future cash flows.
There are two canonical DCF approaches:
1. **Free Cash Flow to Firm (FCFF):** Measures cash available to all capital providers (equity + debt) after operating expenses, taxes, and reinvestment:
   $$\\text{FCFF} = \\text{EBIT}(1 - t) + \\text{D\\&A} - \\text{CapEx} - \\Delta\\text{NWC}$$
   Discounted at the **Weighted Average Cost of Capital (WACC)**.
2. **Free Cash Flow to Equity (FCFE):** Measures cash available strictly to equity shareholders after servicing net debt:
   $$\\text{FCFE} = \\text{FCFF} - \\text{Interest}(1 - t) + \\text{Net Borrowing}$$
   Discounted at the **Cost of Equity ($k_e$)** derived via CAPM.

#### 2. Explicit Forecast Period (Years $t = 1 \\dots n$)
Project granular revenue, operating expenses, tax charges, and reinvestment requirements for a discrete forecast horizon (typically 5 to 10 years):
$$\\text{PV}_{\\text{explicit}} = \\sum_{t=1}^{n} \\frac{\\text{FCFF}_t}{(1 + \\text{WACC})^t}$$

#### 3. Terminal Value (TV) Formulation
Because corporate entities are assumed to operate in perpetuity, value beyond Year $n$ is captured via the **Gordon Growth Model**:
$$\\text{TV}_n = \\frac{\\text{FCFF}_{n+1}}{\\text{WACC} - g} = \\frac{\\text{FCFF}_n \\times (1 + g)}{\\text{WACC} - g}$$
*Mathematical Invariant:* The long-term sustainable terminal growth rate $g$ **must strictly be less than WACC** ($g < \\text{WACC}$) and generally cannot exceed the nominal long-term GDP growth rate of the operating economy.

The present value of the Terminal Value discounted back to $t=0$ is:
$$\\text{PV}_{\\text{TV}} = \\frac{\\text{TV}_n}{(1 + \\text{WACC})^n}$$

#### 4. Enterprise Value (EV)
The total Enterprise Value is the sum of discounted explicit cash flows and the discounted terminal value:
$$\\text{EV} = \\text{PV}_{\\text{explicit}} + \\text{PV}_{\\text{TV}} = \\sum_{t=1}^{n} \\frac{\\text{FCFF}_t}{(1 + \\text{WACC})^t} + \\frac{\\text{FCFF}_n(1 + g)}{(\\text{WACC} - g)(1 + \\text{WACC})^n}$$

#### 5. Bridge from Enterprise Value to Equity Value & Per-Share Value
To transition from Enterprise Value to Equity Value:
$$\\text{Equity Value} = \\text{EV} + \\text{Cash \\& Cash Equivalents} + \\text{Non-Operating Assets} - \\text{Total Interest-Bearing Debt} - \\text{Preferred Stock} - \\text{Minority/Non-Controlling Interests}$$

Finally, divide by diluted shares outstanding:
$$\\text{Intrinsic Value per Share} = \\frac{\\text{Equity Value}}{\\text{Fully Diluted Shares Outstanding}}$$

*Regulatory Disclaimer: Educational DCF derivation. Not SEBI-registered investment advice.*""",

        2: """### P/E Ratio vs. EV/EBITDA Multiple for Capital-Intensive Firms

#### 1. Definitional Formulations
* **Price-to-Earnings (P/E):**
  $$\\text{P/E} = \\frac{\\text{Market Price per Share}}{\\text{Diluted EPS}} = \\frac{\\text{Market Capitalization}}{\\text{Net Income}}$$
* **Enterprise Value to EBITDA (EV/EBITDA):**
  $$\\frac{\\text{EV}}{\\text{EBITDA}} = \\frac{\\text{Market Cap} + \\text{Total Interest-Bearing Debt} + \\text{Preferred Stock} + \\text{Minority Interest} - \\text{Cash}}{\\text{Operating Profit (EBIT)} + \\text{Depreciation} + \\text{Amortization}}$$

#### 2. Capital Structure Neutrality
* P/E is an **equity-only multiple** evaluated after debt servicing (interest expenses). A heavily levered firm has lower Net Income due to fixed interest deductions, artificially skewing the P/E multiple upward or downward depending on cyclical profitability.
* EV/EBITDA is an **entity-level multiple** evaluated before capital structure choices. It allows direct operational comparison between heavily levered and zero-debt firms across capital-intensive industries (telecom, utilities, steel).

#### 3. Depreciation Distortions in Capital-Intensive Sectors
Firms with large fixed asset bases incur substantial depreciation charges. Differences in accounting depreciation schedules (straight-line vs. accelerated) create massive Net Income disparities that distort P/E. EV/EBITDA strips out non-cash depreciation differences, providing a cleaner proxy for pre-tax operating cash flow generation before reinvestment.""",

        3: """### Return on Capital Employed (ROCE): Balance Sheet & P&L Derivation

#### 1. Definitional Formula & Capital Matching Principle
$$\\text{ROCE} = \\frac{\\text{EBIT}}{\\text{Average Capital Employed}}$$
Where:
* **EBIT (Operating Profit):** Taken from the P&L statement as Revenue minus Operating Expenses (COGS, SG&A, Depreciation & Amortization), before interest and taxes.
* **Capital Employed:** Total Assets minus Current Operating Liabilities, or equivalently:
  $$\\text{Capital Employed} = \\text{Total Shareholders' Equity} + \\text{Total Non-Current Liabilities (Long-Term Debt)}$$

#### 2. The Critical Necessity of Using Average Capital Employed
* **Matching Flow to Stock:** EBIT represents a flow of operating earnings generated continuously across the entire reporting period (e.g., 12 months). In contrast, balance sheet figures represent a point-in-time stock at a single date.
* **Distortion of Closing-Only Capital:** If a company issues substantial equity or raises significant long-term debt near the fiscal year-end, using closing capital employed artificially inflates the denominator and depresses calculated ROCE, even though that new capital did not contribute to generating the past year's EBIT.
* **Standard Financial Computation:**
  $$\\text{Average Capital Employed} = \\frac{\\text{Capital Employed}_{\\text{beginning}} + \\text{Capital Employed}_{\\text{ending}}}{2}$$

#### 3. Interpretation Standard & Economic Value Creation
* ROCE reflects the pre-tax operational productivity of all deployed long-term financing.
* **Economic Value Invariant:** Sustainable wealth creation requires that **$\\text{ROCE} > \\text{WACC}$**. If ROCE is less than WACC, the firm is destroying capital on an economic basis despite reporting positive accounting net income.""",

        4: """### Debt-to-Equity (D/E) Ratio Analysis: Financial Leverage & Risk Implications

#### 1. Precise Definitional Formula
$$\\text{Debt-to-Equity (Gross)} = \\frac{\\text{Total Interest-Bearing Debt}}{\\text{Total Shareholders' Equity}}$$
$$\\text{Net Debt-to-Equity} = \\frac{\\text{Total Interest-Bearing Debt} - \\text{Cash \\& Cash Equivalents}}{\\text{Total Shareholders' Equity}}$$

*Crucial Accounting Precision:*
The numerator consists strictly of **interest-bearing debt** (short-term borrowings, current portion of long-term debt, term loans, bonds, debentures, and lease liabilities capitalized under IFRS 16 / Ind AS 116).
It strictly **excludes** non-debt operating liabilities (such as trade accounts payable, accrued expenses, deferred tax liabilities, and provisions).

#### 2. Quantitative Risk Interpretation of D/E = 2.5
* A D/E ratio of $2.5$ means that for every ₹$1.00$ of equity capital provided by shareholders, the company has funded operations with ₹$2.50$ of interest-bearing debt.
* Total assets are funded $71.43\\%$ by debt ($\\frac{2.5}{1.0 + 2.5} = 71.43\\%$) and $28.57\\%$ by equity.

#### 3. Sector-Specific Context
* **High-Risk in Cyclical Non-Financials:** In manufacturing or consumer cyclicals, a D/E of 2.5 represents elevated insolvency risk, high fixed interest burdens, and vulnerability to credit rating downgrades during economic contractions.
* **Acceptable in Utilities & Infrastructure:** Regulated utilities and long-term toll-road concessions with guaranteed, inflation-linked cash flows frequently sustain D/E ratios of $2.0 - 3.0$ safely.
* *Banking Exception:* Commercial banks and Non-Banking Financial Companies (NBFCs) operate with financial leverage of $5.0 - 8.0\\times$ as deposits and borrowings represent their primary operating inventory.""",

        5: """### Compound Annual Growth Rate (CAGR) Calculation: 50 Cr to 120 Cr over 4 Years

#### 1. Mathematical Formula
$$\\text{CAGR} = \\left(\\frac{V_{\\text{final}}}{V_{\\text{initial}}}\\right)^{\\frac{1}{n}} - 1$$

#### 2. Analytical Step-by-Step Calculation
* $V_{\\text{initial}} = 50\\text{ Cr}$
* $V_{\\text{final}} = 120\\text{ Cr}$
* $n = 4\\text{ years}$

1. Compute growth multiple:
   $$\\frac{120}{50} = 2.40$$
2. Take the fourth root:
   $$2.40^{\\frac{1}{4}} = 2.40^{0.25} \\approx 1.24467$$
3. Subtract 1:
   $$1.24467 - 1 = 0.24467 \\implies \\mathbf{+24.47\\%}$$

#### 3. Verification Invariant
$$50 \\times (1 + 0.24467)^4 = 50 \\times 2.40 = 120.0\\text{ Cr}$$""",

        6: """### Working Capital Cycle & Days Sales Outstanding (DSO) Cash Flow Dynamics

#### 1. Cash Conversion Cycle (CCC) Formulation
$$\\text{CCC} = \\text{DIO} + \\text{DSO} - \\text{DPO}$$
Where:
* **DIO (Days Inventory Outstanding):** $\\frac{\\text{Average Inventory}}{\\text{Cost of Goods Sold (COGS)}} \\times 365$
* **DSO (Days Sales Outstanding):** $\\frac{\\text{Average Trade Accounts Receivable}}{\\text{Net Credit Sales}} \\times 365$
* **DPO (Days Payables Outstanding):** $\\frac{\\text{Average Trade Accounts Payable}}{\\text{COGS or Purchases}} \\times 365$

#### 2. DSO Exact Derivation & Sensitivity
$$\\text{DSO} = \\frac{\\text{Average Trade Accounts Receivable}}{\\text{Net Credit Sales}} \\times \\text{Days in Period}$$
*Strict Calculation Rule:* The numerator must utilize **average trade accounts receivable** across the period (or $(\\text{AR}_{\\text{begin}} + \\text{AR}_{\\text{end}}) / 2$), and the denominator must reflect **net credit sales** (excluding cash sales).

#### 3. Impact of DSO on Corporate Cash Flow
* **Rising DSO:** Indicates delayed customer payments, deteriorating customer credit health, or aggressive revenue recognition. This traps cash in uncollected working capital, directly reducing Operating Cash Flow (CFO):
  $$\\Delta\\text{CFO} = -\\Delta\\text{Trade Receivables} = -\\left(\\frac{\\Delta\\text{DSO} \\times \\text{Annual Credit Sales}}{365}\\right)$$
* **Declining DSO:** Accelerates cash velocity, expands free cash flow, and reduces reliance on short-term bank working capital facilities.""",

        7: """### Evaluating Dividend Yield Sustainability

#### 1. The Value Trap Phenomenon
A high dividend yield ($\\frac{\\text{Annual Dividend per Share}}{\\text{Market Price per Share}}$) is frequently a lagging artifact caused by a precipitous drop in equity price due to deteriorating corporate fundamentals.

#### 2. Core Quantitative Sustainability Metrics
1. **Free Cash Flow (FCFE) Dividend Coverage:**
   $$\\text{FCFE Coverage} = \\frac{\\text{Free Cash Flow to Equity}}{\\text{Total Dividends Paid}}$$
   If this ratio is below $1.0\\times$ (or if FCF is negative), the company is funding dividend distributions through debt issuance or asset disposals, which is unsustainable over the long term.
2. **Net Debt to EBITDA:** A ratio exceeding $3.0-3.5\\times$ combined with high dividend payouts indicates elevated credit downgrade and dividend-cut risk.
3. **Interest Coverage Ratio ($\\text{EBIT} / \\text{Interest}$):** Must remain safely above $3.5\\times$ to ensure debt covenants are not breached.
4. **Earnings Quality & Cyclical Peak:** Assess whether current earnings represent a cyclical peak (e.g., commodity producers) that cannot be sustained across down-cycles.""",

        8: """### DuPont Analysis: Decomposition of Return on Equity (ROE)

#### 1. The Three-Step DuPont Identity
$$\\text{ROE} = \\frac{\\text{Net Income}}{\\text{Shareholders' Equity}} = \\underbrace{\\left(\\frac{\\text{Net Income}}{\\text{Revenue}}\\right)}_{\\text{Net Profit Margin}} \\times \\underbrace{\\left(\\frac{\\text{Revenue}}{\\text{Total Assets}}\\right)}_{\\text{Asset Turnover}} \\times \\underbrace{\\left(\\frac{\\text{Total Assets}}{\\text{Shareholders' Equity}}\\right)}_{\\text{Equity Multiplier}}$$

#### 2. Rigorous Definitional Distinction: Net Profit Margin vs. Operating Margin
* **Net Profit Margin ($\\frac{\\text{Net Income}}{\\text{Revenue}}$):** Measures **overall bottom-line profitability** after deducting operating costs, financing charges (interest expenses), and income taxes. It evaluates how much of each rupee of revenue trickles down to common equity shareholders.
* **Operating Profitability ($\\frac{\\text{EBIT}}{\\text{Revenue}}$):** Measures core operational efficiency before debt servicing and taxes. It is evaluated in the extended **5-step DuPont Framework**:
  $$\\text{ROE} = \\underbrace{\\left(\\frac{\\text{Net Income}}{\\text{EBT}}\\right)}_{\\text{Tax Burden}} \\times \\underbrace{\\left(\\frac{\\text{EBT}}{\\text{EBIT}}\\right)}_{\\text{Interest Burden}} \\times \\underbrace{\\left(\\frac{\\text{EBIT}}{\\text{Revenue}}\\right)}_{\\text{Operating Margin}} \\times \\underbrace{\\left(\\frac{\\text{Revenue}}{\\text{Assets}}\\right)}_{\\text{Asset Turnover}} \\times \\underbrace{\\left(\\frac{\\text{Assets}}{\\text{Equity}}\\right)}_{\\text{Leverage}}$$
* *Analytical Insight:* Describing Net Profit Margin as purely "operating profitability" is conceptually incorrect because Net Profit Margin is heavily influenced by capital structure leverage (interest expense) and statutory corporate tax rates.

#### 3. Component Synthesis
1. **Net Profit Margin:** Bottom-line efficiency after financing and tax burdens.
2. **Asset Turnover:** Asset efficiency / capital velocity (revenue generated per unit of asset).
3. **Equity Multiplier:** Financial leverage ($1 + \\text{D/E}$). High leverage magnifies ROE during growth phases but accelerates downside volatility during downcycles.""",

        9: """### Free Cash Flow to Firm (FCFF) vs. Free Cash Flow to Equity (FCFE)

#### 1. Mathematical Formulations
* **Free Cash Flow to Firm (FCFF) — Unlevered:**
  $$\\text{FCFF} = \\text{EBIT}(1 - t) + \\text{D\\&A} - \\text{CapEx} - \\Delta\\text{NWC}$$
* **Free Cash Flow to Equity (FCFE) — Levered:**
  $$\\text{FCFE} = \\text{FCFF} - \\text{Interest Expense}(1 - t) + \\text{Net Debt Issued/(Repaid)}$$

#### 2. Comparative Matrix
| Dimension | FCFF (Free Cash Flow to Firm) | FCFE (Free Cash Flow to Equity) |
| :--- | :--- | :--- |
| **Claimants** | All capital providers (Debt holders + Equity holders) | Strictly Equity shareholders |
| **Discount Rate** | WACC (Weighted Average Cost of Capital) | $k_e$ (Cost of Equity via CAPM) |
| **Direct Valuation Output**| Enterprise Value (EV) | Equity Value |
| **Treatment of Debt** | Debt cash flows ignored in numerator | Debt issuances added; interest & repayments deducted |""",

        10: """### Inventory Turnover Ratio: Operational Efficiency in Retail

#### 1. Formula & Definition
$$\\text{Inventory Turnover Ratio} = \\frac{\\text{Cost of Goods Sold (COGS)}}{\\text{Average Inventory}}$$
$$\\text{Days Inventory Outstanding (DIO)} = \\frac{365}{\\text{Inventory Turnover}}$$

#### 2. Operational Inferences
* **Low Inventory Turnover:**
  * Primary Signal: Slow-moving inventory, overstocking, inaccurate demand forecasting, or obsolete product lines requiring markdowns.
  * *Correction on Stockout Dynamics:* Low inventory turnover does **not** directly indicate stockouts; stockouts are tracked independently via on-shelf availability (OSA) and order fulfillment metrics.
* **High Inventory Turnover:**
  * Signals efficient inventory management, high stock velocity, and minimal storage/holding costs.
  * Caution: Extremely high turnover coupled with low buffer safety stock can increase vulnerability to sudden stockouts during supply chain shocks.""",

        11: """### Interest Coverage Ratio (ICR) in Default Risk Assessment

#### 1. Definition: Earnings-Based vs. Cash Coverage
The Interest Coverage Ratio measures a firm's ability to service outstanding debt obligations:
$$\\text{Interest Coverage Ratio (Earnings-Based)} = \\frac{\\text{EBIT}}{\\text{Interest Expense}}$$

*Accounting Correction:* **EBIT (Earnings Before Interest and Taxes) is an accrual accounting profit metric, NOT operating cash flow.**
To evaluate cash-based coverage, analysts evaluate:
* **EBITDA / Interest Expense** (incorporating non-cash depreciation and amortization).
* **Cash Flow from Operations (CFO) / Interest Expense** (pure cash generation coverage).

#### 2. Threshold Zones for Credit Risk
* **Ratio $< 1.5\\times$:** Substantial default and downgrade risk. Operating earnings are insufficient to cover fixed interest charges without tapping credit facilities.
* **Ratio $1.5\\times - 3.0\\times$:** Moderate safety buffer; vulnerable to economic recessions or margin contractions.
* **Ratio $> 4.0\\times$:** Investment-grade credit profile with robust debt-servicing ability.""",

        12: """### Financial & Ownership Implications of Share Buyback Programs

#### 1. Proportional Ownership Mechanics
* **Accretion, Not Dilution:** When a company repurchases and cancels shares, the total number of shares outstanding decreases. Consequently, **the proportional percentage ownership of non-participating shareholders strictly increases**.
* Example: If you own 1,000 shares out of 10,000 ($10\\%$), and the company repurchases and cancels 2,000 shares from other holders, your ownership automatically increases to $\\frac{1,000}{8,000} = \\mathbf{12.5\\%}$.

#### 2. Balance Sheet & Capital Structure Impact
* Cash and cash equivalents decrease on the asset side; Retained Earnings and Common Stock decrease on the equity side.
* Debt is **not** repaid by a buyback; in debt-financed buybacks (leveraged recapitalizations), debt actually increases, raising financial leverage.
* Earnings Per Share (EPS) increases if Net Income remains constant or if the post-tax return on cash was lower than the inverse of the P/E multiple.""",

        13: """### Economic Value Added (EVA) Formulation & Superiority to Net Profit

#### 1. Formal Formula
$$\\text{EVA} = \\text{NOPAT} - \\text{Capital Charge}$$
$$\\mathbf{\\text{EVA} = \\text{EBIT}(1 - t) - (\\text{WACC} \\times \\text{Invested Capital})}$$
Where:
* **NOPAT:** Net Operating Profit After Tax.
* **WACC:** Weighted Average Cost of Capital (as a decimal, e.g. 0.10).
* **Invested Capital:** $\\text{Total Equity} + \\text{Total Interest-Bearing Debt} - \\text{Cash}$.

#### 2. Why EVA is Superior to Accounting Net Profit
* Accounting Net Profit deducts interest expense (the cost of debt) but treats equity capital as completely free.
* A company can report positive Net Profit while actively destroying shareholder wealth if its return on invested capital is below its cost of capital ($\\text{ROIC} < \\text{WACC}$).
* EVA recognizes that equity investors demand an opportunity cost return. A positive EVA indicates true economic wealth creation.""",

        14: """### Impact of Inflation and Interest Rate Hikes on Corporate Bond Yields

#### 1. Mechanism of Yield Repricing
Bond prices and yields share an exact inverse relationship governed by discounted cash flow mechanics:
$$P = \\sum_{t=1}^{n} \\frac{C}{(1 + y)^t} + \\frac{M}{(1 + y)^n}$$
* **Inflation Risk:** Higher inflation erodes the purchasing power of fixed coupon payments ($C$), prompting investors to demand higher nominal yields.
* **Central Bank Rate Hikes:** When central banks increase policy rates, risk-free benchmark yields (sovereign Treasury yields) rise, lifting the entire discount curve $y$.

#### 2. Duration & Credit Spread Dynamics
* **Modified Duration ($D_{\\text{mod}}$):** Approximates price sensitivity: $\\frac{\\Delta P}{P} \\approx -D_{\\text{mod}} \\cdot \\Delta y$. Long-duration bonds suffer the steepest capital losses during rate hike cycles.
* **Credit Spreads:** During monetary tightening, borrowing costs rise and corporate liquidity shrinks, widening credit default risk spreads for lower-rated (high-yield) corporate debt.""",

        15: """### Key Drivers of Net Interest Margin (NIM) in Commercial Banking

#### 1. Definitional Formula
$$\\text{NIM} = \\frac{\\text{Net Interest Income (NII)}}{\\text{Average Earning Assets}} = \\frac{\\text{Interest Earned} - \\text{Interest Expended}}{\\text{Average Loans + Advances + Investment Securities}}$$

#### 2. Core Drivers of NIM
1. **CASA Ratio (Current Account Savings Account):** High CASA provides low-cost, sticky deposits (typically paying $0-3.5\\%$), significantly lowering the cost of funds ($CoF$).
2. **Asset-Liability Duration Mismatch:** Banks lend long (fixed-rate mortgages) and borrow short (floating deposits). In rising rate environments, floating deposits reprice faster than fixed loans, compressing NIM.
3. **Credit Portfolio Composition:** Retail unsecured lending (credit cards, personal loans) yields higher margins ($14-22\\%$) than wholesale corporate lending ($8-10\\%$), but carries higher credit risk and provision costs.
4. **Non-Performing Assets (NPAs):** Slippages into Gross NPA halt interest accrual, reducing interest income while requiring higher capital provisions.""",

        16: """### Altman Z-Score Bankruptcy Prediction Model

#### 1. Original Altman Z-Score Formulation (Public Manufacturing Firms)
$$Z = 1.2 X_1 + 1.4 X_2 + 3.3 X_3 + 0.6 X_4 + 0.999 X_5$$
Where:
* $X_1 = \\frac{\\text{Working Capital}}{\\text{Total Assets}}$ (Liquidity)
* $X_2 = \\frac{\\text{Retained Earnings}}{\\text{Total Assets}}$ (Cumulative profitability)
* $X_3 = \\frac{\\text{EBIT}}{\\text{Total Assets}}$ (Operating productivity / asset efficiency)
* $X_4 = \\frac{\\text{Market Value of Equity}}{\\text{Total Liabilities}}$ (Market leverage)
* $X_5 = \\frac{\\text{Sales}}{\\text{Total Assets}}$ (Asset turnover)

#### 2. Predictive Zones of Discrimination
* **$Z > 2.99$ (Safe Zone):** Low financial distress probability within 2 years.
* **$1.81 \\le Z \\le 2.99$ (Grey Zone):** Moderate risk; warrants credit surveillance.
* **$Z < 1.81$ (Distress Zone):** High statistical probability of corporate bankruptcy within 24 months.""",

        17: """### Accounting Treatment of Leases under IFRS 16 / Ind AS 116

#### 1. Balance Sheet Recognition
Under IFRS 16 / Ind AS 116, operating leases are brought onto the balance sheet:
* **Right-of-Use (ROU) Asset:** Measured at present value of lease payments + initial direct costs, recorded as a Non-Current Asset.
* **Lease Liability:** Present value of remaining lease payments discounted at the incremental borrowing rate (IBR), recorded as a Financial Liability.

#### 2. P&L and Cash Flow Reclassification
* **P&L Impact:** Operating lease rental expense is replaced by **Depreciation of the ROU Asset** (amortized straight-line) and **Interest Expense on the Lease Liability** (front-loaded). This increases reported EBITDA while leaving Net Income front-loaded negative.
* **Cash Flow Impact:** Operating cash flow (CFO) increases because principal lease repayments are reclassified to Financing Cash Flows (CFF).
* **Low-Value Asset Exemption:** The low-value asset exemption is a principle-based assessment based on the asset's value when brand new (illustratively $\\sim\\$5,000$, such as laptops and office furniture), which may continue to be expensed straight-line.""",

        18: """### Capex for Growth vs. Capex for Maintenance in Valuation

#### 1. Conceptual Distinction
* **Maintenance Capex:** Capital expenditures required to maintain existing operating capacity, replace worn-out machinery, and sustain the current competitive position without expanding revenue capacity.
* **Growth Capex:** Discretionary capital expenditures intended to expand production capacity, open new stores, build new manufacturing facilities, or enter new geographic markets to drive incremental revenue.

#### 2. Valuation & True Owner Earnings Impact
Warren Buffett's "Owner Earnings" and sustainable Free Cash Flow rely strictly on deducting Maintenance Capex:
$$\\text{Owner Earnings} = \\text{Net Income} + \\text{D\\&A} - \\text{Maintenance CapEx} - \\Delta\\text{NWC}$$
* **Common Financial Shenanigans:** Firms experiencing operational distress often cut Maintenance Capex, temporarily boosting reported Free Cash Flow at the expense of long-term equipment degradation.""",

        19: """### Impact of Currency Depreciation on Export-Oriented IT Firms

#### 1. Revenue Translation Gains (Exporter Advantage)
When an Indian IT service firm (e.g., TCS, Infosys) invoices global clients in foreign currencies (USD, EUR, GBP), **domestic currency (INR) depreciation generates more INR per unit of foreign currency received**:
$$\\text{Revenue (INR)} = \\text{Revenue (USD)} \\times \\text{Spot Exchange Rate (INR/USD)}$$
A depreciation of INR from ₹$83$ to ₹$85$ per USD increases top-line reported INR revenue by $+2.4\\%$ without requiring volume growth.

#### 2. Margin & Cost Asymmetry
* IT firms incur $65-75\\%$ of operating costs (software engineer salaries, domestic facilities) in local domestic currency (INR).
* Because revenue is USD-denominated while costs are INR-denominated, domestic currency depreciation causes **operating profit margins to expand significantly**.
* *Hedging Offsets:* Forward exchange contracts and cash-flow hedges enter into marked-to-market losses during sharp unexpected spot depreciations, temporarily muting the net gain.""",

        20: """### Weighted Average Cost of Capital (WACC) & The Tax Shield

#### 1. Formal Formula
$$\\text{WACC} = \\left(\\frac{E}{V} \\times k_e\\right) + \\left(\\frac{D}{V} \\times k_d \\times (1 - t)\\right)$$
Where:
* $E$ = Market value of equity
* $D$ = Market value of interest-bearing debt
* $V = E + D$ = Total firm market value
* $k_e$ = Cost of equity (derived via CAPM: $k_e = R_f + \\beta(R_m - R_f)$)
* $k_d$ = Pre-tax cost of debt (yield to maturity on corporate debt)
* $t$ = Marginal corporate income tax rate

#### 2. The Corporate Tax Shield
Interest payments on debt are statutory tax-deductible expenses. The factor $(1 - t)$ represents the **interest tax shield**, which lowers the effective post-tax cost of debt financing ($k_d(1 - t)$), reducing overall WACC as debt is added up to the firm's optimal capital structure."""
    }
