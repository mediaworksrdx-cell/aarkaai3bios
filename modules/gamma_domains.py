# -*- coding: utf-8 -*-
"""
AARKAAI – Domain Registry & Specialized Industry Profiles
Contains complete layout schemas, custom SVGs, KPI indicators, timeline milestones,
and high-density, jargon-rich consulting paragraphs for all 15 specialized domains.
"""
import re

# Premium Color Template mapping for each domain
DOMAIN_TEMPLATES = {
    "vc": "emerald",
    "equity": "indigo",
    "options": "dark",
    "ml": "dark",
    "corporate": "amber",
    "crypto": "dark",
    "macro": "indigo",
    "healthcare": "emerald",
    "cybersecurity": "crimson",
    "esg": "emerald",
    "realestate": "amber",
    "manufacturing": "indigo",
    "supplychain": "indigo",
    "pharma": "crimson",
    "energy": "amber",
    "general": "indigo"
}

# The Domain Registry containing 15 specialized domains
DOMAIN_REGISTRY = {
    "vc": {
        "name": "Venture Capital & Startup Ecosystems",
        "template": "emerald",
        "cover_kpis": [
            {"label": "Est. Market Size", "val": "$1.85 Billion"},
            {"label": "Ecosystem CAGR", "val": "+22.4% YoY"},
            {"label": "Startup Density", "val": "240+ Active"}
        ],
        "dashboard_kpis": [
            {"label": "Market Velocity", "val": "$1.85B", "change": "▲ +22.4% CAGR", "status": ""},
            {"label": "Ecosystem Funding", "val": "$480M", "change": "▲ +18.7% YoY", "status": ""},
            {"label": "Ecosystem Density", "val": "242 Co.", "change": "▲ +35 Net New", "status": ""},
            {"label": "Ecosystem Score", "val": "84 / 100", "change": "Strong Growth", "status": "purple"}
        ],
        "brand_logos": [
            {"name": "ZOHO", "type": "rect", "color": "#10B981"},
            {"name": "FRESH", "type": "diamond", "color": "#3B82F6"},
            {"name": "BEE", "type": "polygon", "color": "#F59E0B"}
        ],
        "swot": {
            "s": "Strong technical talent density; capital-efficient OMR corridor operations.",
            "w": "Limited early-stage domestic institutional growth capital.",
            "o": "Global enterprise SaaS migration and cross-border expansion playbooks.",
            "t": "Global macroeconomic cooling and high-yield interest rate environments."
        },
        "visual_svg": """
        <svg width="100%" height="80" viewBox="0 0 200 120" style="max-height: 80px; background: #F8FAFC; border-radius: 4px;">
            <path d="M 150 0 C 155 40, 160 80, 170 120" fill="none" stroke="#93C5FD" stroke-width="2"/>
            <text x="172" y="60" font-family="sans-serif" font-size="8" fill="#3B82F6" transform="rotate(82, 172, 60)" opacity="0.6">Bay of Bengal</text>
            <circle cx="50" cy="20" r="5" fill="#EF4444" opacity="0.8"/>
            <text x="58" y="23" font-family="sans-serif" font-size="8" font-weight="bold" fill="#0F172A">Ambattur (SaaS)</text>
            <circle cx="90" cy="50" r="5" fill="#10B981" opacity="0.8"/>
            <text x="98" y="53" font-family="sans-serif" font-size="8" font-weight="bold" fill="#0F172A">Guindy (DeepTech)</text>
            <circle cx="120" cy="90" r="5" fill="#3B82F6" opacity="0.8"/>
            <text x="50" y="93" font-family="sans-serif" font-size="8" font-weight="bold" fill="#0F172A">OMR Corridor (AI)</text>
        </svg>
        """,
        "timeline": [
            {"time": "H1 2026: Consolidation", "desc": "Unified SaaS compliance cloud provisioning completed across local seed networks."},
            {"time": "H2 2026: Automation", "desc": "Capital deployment pipelines automated across top accelerators."}
        ],
        "table": {
            "headers": ["Segment", "Growth Rate", "Funding Density", "Talent Pool"],
            "rows": [
                ["Enterprise AI", "95% (High)", "92% (High)", "78% (Med)"],
                ["Fintech SaaS", "88% (Med)", "75% (Med)", "90% (High)"]
            ]
        },
        "charts": {
            "bar": {"title": "Annual Venture Capital Inflows", "ylabel": "Capital Inflow ($ Millions)"},
            "line": {"title": "Ecosystem Net Retention & ARR Velocity"},
            "donut": {"title": "Capital Distribution by Vertical"},
            "hbar": {"title": "Startup Operational Readiness Scores"},
            "area": {"title": "Cumulative Ecosystem Funding Risk"}
        },
        "fallbacks": {
            "Executive Summary & Framework": "The comprehensive evaluation of the Venture Capital sector reveals a profound paradigm shift, driven by accelerating software adoption vectors, evolving founder dynamics, and restructuring early-stage capital. To remain competitive in this fast-moving landscape, startups must aggressively optimize their capital runways, integrate scalable software architectures, and target clear product-market fit metrics. A robust analytical framework is essential for navigating these multi-dimensional changes, allowing venture partners to identify untapped seed-stage value drivers while simultaneously mitigating scale-up integration risks. Furthermore, the integration of deep tech infrastructure and automated SaaS platforms is transitioning from a luxury to a critical operational necessity. Organizations that fail to establish a resilient, data-driven foundation face immediate valuation compression as competitors leverage high-velocity expansion cycles and capital-efficient scaling models.",
            "Market Analysis & Sector Segmentation": "A rigorous, multi-layered market analysis of the venture ecosystem highlights substantial structural transformations across all primary, secondary, and tertiary sector segments. Current venture indicators suggest a significant reallocation of institutional capital away from consumer applications and toward highly agile, B2B SaaS and DeepTech platforms. This shift is characterized by a growing polarization between first-mover innovators who capture exponential market share and late-stage legacy systems struggling with technical debt. Sector segmentation reveals that high-value niches are expanding rapidly, driven by localized talent pools and specialized product offerings that address precise enterprise pain points. Concurrently, competitive dynamics are intensifying as cross-industry partnerships and API integrations redefine traditional venture value chains.",
            "Quantitative Performance & Revenue Velocity": "Analyzing the quantitative performance metrics of the startup sector demonstrates a clear correlation between technological integration and compounding revenue velocity. Key financial indicators, including annual recurring revenue (ARR), net revenue retention (NRR), and customer lifetime value (LTV) relative to customer acquisition cost (CAC), showcase strong upward trends among organizations that have fully embraced digital transformation. This financial outperformance is primarily driven by operational leverage, where software-defined scaling allows for exponential expansion without a corresponding linear increase in overhead expenses. Quarter-on-quarter performance benchmarks reveal that top-quartile startups are experiencing accelerated growth rates, fueled by high-velocity customer acquisition and successful expansion into adjacent geographic markets.",
            "Operational Efficiency & Architecture": "The operational infrastructure supporting the startup sector is undergoing a massive reconfiguration, centered on maximizing throughput, minimizing unit economics, and ensuring continuous platform availability. Modern SaaS and DeepTech pipelines are highly distributed, requiring sophisticated coordination mechanisms to manage real-time data flows, cloud provisioning, and computational resource allocation. By transitioning to serverless architectures, edge computing nodes, and automated containerization, startups can significantly reduce their operational footprint while improving scalability. Furthermore, the deployment of intelligent monitoring tools and automated self-healing protocols allows organizations to detect and resolve system bottlenecks before they impact end-users.",
            "Risk Analysis, Vulnerability & Strategic Outlook": "A comprehensive risk assessment of the venture landscape identifies several critical vulnerability vectors that startups must proactively address to safeguard their market position. Chief among these risks are shifting venture capital availability, cybersecurity threats targeting distributed databases, and potential disruptions in global talent supply chains. Implementing a robust, multi-layered defensive posture is essential for mitigating these threats, combining real-time threat detection, rigorous data encryption, and redundant operational pathing. Concurrently, strategic planning must account for rapid technological obsolescence, ensuring that product roadmaps remain flexible and aligned with long-term ecosystem trends."
        }
    },
    "equity": {
        "name": "Equity Research & Public Valuations",
        "template": "indigo",
        "cover_kpis": [
            {"label": "Market Cap", "val": "$842.5 Billion"},
            {"label": "P/E Ratio", "val": "24.8x LTM"},
            {"label": "Dividend Yield", "val": "1.85% Ann."}
        ],
        "dashboard_kpis": [
            {"label": "EBITDA Margin", "val": "34.2%", "change": "▲ +120 bps YoY", "status": ""},
            {"label": "Free Cash Flow", "val": "$42.5B", "change": "▲ +15.4% YoY", "status": ""},
            {"label": "Leverage Ratio", "val": "1.4x", "change": "▼ -0.2x Debt", "status": ""},
            {"label": "Target Rating", "val": "Outperform", "change": "PE Target 28x", "status": "purple"}
        ],
        "brand_logos": [
            {"name": "AAPL", "type": "rect", "color": "#6366F1"},
            {"name": "MSFT", "type": "diamond", "color": "#10B981"},
            {"name": "TSLA", "type": "polygon", "color": "#EF4444"}
        ],
        "swot": {
            "s": "Market leadership; robust balance sheet with compounding free cash flow yield.",
            "w": "High concentration of segment revenue in consumer-facing hardware.",
            "o": "Enterprise cloud monetization and artificial intelligence subscriptions.",
            "t": "Antitrust litigation barriers and global regulatory compliance hurdles."
        },
        "visual_svg": """
        <svg width="100%" height="80" viewBox="0 0 200 120" style="max-height: 80px; background: #F8FAFC; border-radius: 4px;">
            <line x1="30" y1="20" x2="30" y2="100" stroke="#EF4444" stroke-width="1.5"/>
            <rect x="25" y="40" width="10" height="40" fill="#EF4444"/>
            <line x1="70" y1="10" x2="70" y2="90" stroke="#10B981" stroke-width="1.5"/>
            <rect x="65" y="30" width="10" height="40" fill="#10B981"/>
            <line x1="110" y1="30" x2="110" y2="110" stroke="#EF4444" stroke-width="1.5"/>
            <rect x="105" y="50" width="10" height="30" fill="#EF4444"/>
            <line x1="150" y1="10" x2="150" y2="100" stroke="#10B981" stroke-width="1.5"/>
            <rect x="145" y="20" width="10" height="60" fill="#10B981"/>
            <path d="M 30 80 Q 70 40 110 70 T 150 30" fill="none" stroke="#3B82F6" stroke-width="1.5" stroke-dasharray="3,3"/>
            <text x="10" y="15" font-family="sans-serif" font-size="8" font-weight="bold" fill="#64748B">EMA/SMA Cross</text>
        </svg>
        """,
        "timeline": [
            {"time": "Q3 Earnings Release", "desc": "EBITDA margins expanded past target guidelines due to cloud software growth."},
            {"time": "M&A Integration", "desc": "Core asset acquisition finalized, projecting 12% cash flow synergy."}
        ],
        "table": {
            "headers": ["Ticker", "Target Price", "P/E Multiple", "FCF Yield"],
            "rows": [
                ["AAPL", "$220.00 (Buy)", "28.4x", "4.2%"],
                ["MSFT", "$450.00 (Buy)", "32.1x", "3.8%"]
            ]
        },
        "charts": {
            "bar": {"title": "Quarterly Revenue & EBITDA Expansion", "ylabel": "Revenue ($ Millions)"},
            "line": {"title": "Operating Cash Flow vs Free Cash Flow Yield"},
            "donut": {"title": "Segment Revenue Breakdown"},
            "hbar": {"title": "Peer Valuation Multiples (P/E & EV/EBITDA)"},
            "area": {"title": "Shareholder Returns & Capital Allocation Profile"}
        },
        "fallbacks": {
            "Executive Summary & Framework": "Our fundamental equity analysis indicates a robust underlying business model operating amidst evolving macroeconomic variables and shifting competitive frameworks. To secure margin stability in this climate, the enterprise must aggressively optimize capital expenditures, manage operational leverage, and accelerate high-margin revenue streams. A structured valuation framework is essential for assessing these trends, utilizing discounted cash flows and relative valuation multiples to isolate intrinsic value drivers from market noise. Institutional investors are increasingly prioritizing cash flow generation over top-line expansion, demanding a disciplined approach to capital allocation and balance sheet strength.",
            "Market Analysis & Sector Segmentation": "A rigorous, multi-layered market analysis of the sector highlights substantial structural transformations and competitive repositioning across primary business lines. Current equity indicators suggest a significant reallocation of institutional capital away from cyclical assets and toward secular growth platforms. This shift is characterized by a growing polarization between low-cost scale leaders who capture premium margins and legacy operators struggling with supply chain inefficiencies. Sector segmentation reveals that high-margin business segments are expanding rapidly, driven by strong pricing power and customer retention rates.",
            "Quantitative Performance & Revenue Velocity": "Analyzing the quantitative performance metrics demonstrates a clear correlation between capital allocation discipline and compounding free cash flow yield. Key financial indicators, including operating margins, return on invested capital (ROIC), and debt-to-equity ratios, showcase strong upward trends among top-quartile industry leaders. This financial outperformance is primarily driven by operational leverage, where fixed cost control allows incremental revenues to flow directly to operating income. Quarter-on-quarter performance benchmarks reveal that leading firms are experiencing expanded gross margins.",
            "Operational Efficiency & Architecture": "The operational infrastructure supporting the business model is undergoing a massive reconfiguration, centered on maximizing supply chain throughput, minimizing production costs, and ensuring asset utilization. Modern manufacturing and distribution pipelines are highly integrated, requiring sophisticated coordination mechanisms to manage logistics, raw material sourcing, and energy inputs. By transitioning to automated production, centralized inventory management, and energy-efficient facilities, the enterprise can significantly reduce its operating cost base.",
            "Risk Analysis, Vulnerability & Strategic Outlook": "A comprehensive risk assessment identifies several critical vulnerability vectors that could impact long-term cash flow projections. Chief among these risks are changing regulatory compliance standards, geopolitical threats targeting global supply chains, and potential currency translation exposures. Implementing a robust risk mitigation framework is essential, combining currency hedging, diversified supplier sourcing, and proactive compliance auditing. Concurrently, strategic planning must account for interest rate volatility."
        }
    },
    "options": {
        "name": "Quantitative Options & Derivatives Strategy",
        "template": "dark",
        "cover_kpis": [
            {"label": "Implied Volatility (IV)", "val": "28.4% (92nd %)"},
            {"label": "Put/Call Ratio", "val": "0.68 (Bullish)"},
            {"label": "Max Pain Price", "val": "$175.00 Exp."}
        ],
        "dashboard_kpis": [
            {"label": "Net Portfolio Theta", "val": "+$4,850/day", "change": "▲ +12.4% Decay", "status": ""},
            {"label": "Gamma Exposure", "val": "-1,250 Short", "change": "▼ Risk Hedged", "status": ""},
            {"label": "Vega Sensitivity", "val": "-$820/1% Vol", "change": "▲ Short Vol Bias", "status": ""},
            {"label": "Margin Cushion", "val": "68% Available", "change": "Portfolio Margin", "status": "purple"}
        ],
        "brand_logos": [
            {"name": "SPY", "type": "rect", "color": "#8B5CF6"},
            {"name": "QQQ", "type": "diamond", "color": "#F59E0B"},
            {"name": "VIX", "type": "polygon", "color": "#EF4444"}
        ],
        "swot": {
            "s": "High cash flow generation from time decay; defined risk structures.",
            "w": "Slippage during extreme tail events; overnight gap risk exposures.",
            "o": "Volatility expansion during earnings seasons providing rich premium skews.",
            "t": "Sudden volatility collapse (IV crush) or systemic margin liquidation."
        },
        "visual_svg": """
        <svg width="100%" height="80" viewBox="0 0 200 120" style="max-height: 80px; background: #F8FAFC; border-radius: 4px;">
            <line x1="20" y1="100" x2="180" y2="100" stroke="#94A3B8" stroke-width="1"/>
            <line x1="20" y1="20" x2="20" y2="110" stroke="#94A3B8" stroke-width="1"/>
            <line x1="20" y1="60" x2="180" y2="60" stroke="#CBD5E1" stroke-width="0.8" stroke-dasharray="2,2"/>
            <path d="M 20 100 L 70 100 L 120 30 L 180 30" fill="none" stroke="#10B981" stroke-width="2.5"/>
            <circle cx="70" cy="100" r="3.5" fill="#EF4444"/>
            <circle cx="120" cy="30" r="3.5" fill="#10B981"/>
            <text x="70" y="112" font-family="sans-serif" font-size="7" fill="#64748B" text-anchor="middle">Strike A</text>
            <text x="120" y="22" font-family="sans-serif" font-size="7" fill="#64748B" text-anchor="middle">Strike B</text>
            <text x="150" y="45" font-family="sans-serif" font-size="8" font-weight="bold" fill="#10B981">Max Profit</text>
            <text x="35" y="85" font-family="sans-serif" font-size="8" font-weight="bold" fill="#EF4444">Max Loss</text>
        </svg>
        """,
        "timeline": [
            {"time": "Weekly Cycle Rebalance", "desc": "Consolidated short iron condor positions near 15 delta to harvest premium decay."},
            {"time": "Delta Hedging Auto-Trigger", "desc": "Smart routing executed shares short-covering to neutralize gamma spikes."}
        ],
        "table": {
            "headers": ["Strategy", "Strike Width", "IV Rank", "Risk/Reward"],
            "rows": [
                ["Iron Condor", "10 Point", "78%", "1:2.4 Max Payoff"],
                ["Bull Put Spread", "5 Point", "85%", "1:3.8 Max Payoff"]
            ]
        },
        "charts": {
            "bar": {"title": "Time Decay & Premium Yield Velocity", "ylabel": "Decay Rate ($/Day)"},
            "line": {"title": "Implied vs Realized Volatility Skew Curve"},
            "donut": {"title": "Greeks Exposure Distribution by Asset"},
            "hbar": {"title": "Option Chain Liquidity & Open Interest"},
            "area": {"title": "Delta & Gamma Hedging Risk Bounds"}
        },
        "fallbacks": {
            "Executive Summary & Framework": "The quantitative derivation of the options model outlines a structured approach to volatility-harvesting and risk-managed yield enhancement. To capture premium decay efficiently, the strategist must aggressively manage Greeks, monitor implied volatility skew, and optimize margin collateral allocation. A robust mathematical framework is essential for navigating these multi-dimensional curves, allowing traders to identify mispriced tail risk while simultaneously hedging directional exposure. Ultimately, our core thesis posits that options premium capture is a function of implied vs. realized volatility differentials and the structural decay of time value.",
            "Market Analysis & Sector Segmentation": "A rigorous, multi-layered market analysis of the volatility surface highlights substantial structural shifts across the implied volatility skew and term structure. Current quantitative indicators suggest a significant volatility premium in near-term expirations, driven by hedging demand and tail-risk pricing. This regime is characterized by a polarization between out-of-the-money put skew and front-month call premium decay dynamics. Segmenting the option chain reveals that high-liquidity strikes are expanding rapidly, driven by institutional positioning.",
            "Quantitative Performance & Revenue Velocity": "Analyzing the quantitative performance metrics demonstrates a clear correlation between delta-neutral positioning and compounding Sharpe ratios. Key performance indicators, including theta decay velocity, gamma exposure curves, and profit-factor ratios, showcase strong upward trends when risk is dynamically adjusted. This premium capture outperformance is primarily driven by delta-hedging efficiency, where automated rebalancing keeps directional risk within narrow tolerances.",
            "Operational Efficiency & Architecture": "The operational infrastructure supporting the trading strategy is engineered to minimize execution slippage, optimize margin collateral, and ensure low-latency order routing. Modern quantitative desks rely on direct market access (DMA), smart order routing (SOR) algorithms, and co-located servers to execute multi-leg option orders. By employing advanced execution algorithms, traders can execute complex spreads within the bid-ask spread, avoiding unnecessary transaction costs.",
            "Risk Analysis, Vulnerability & Strategic Outlook": "A comprehensive risk assessment identifies several critical vulnerability vectors inherent to leveraged derivative positions. Chief among these risks are gap-risk during market closures, extreme implied volatility expansion, and execution slippage during high-stress liquidity events. Implementing a robust hedging framework is essential, combining long-gamma tail hedges, dynamic delta adjustments, and strict size limits. Concurrently, strategic planning must account for volatility regime changes."
        }
    },
    "ml": {
        "name": "Machine Learning & AI Architectures",
        "template": "dark",
        "cover_kpis": [
            {"label": "Model Scale", "val": "70B Parameters"},
            {"label": "Training FLOPs", "val": "1.8e25 FP8"},
            {"label": "Inference Latency", "val": "18.5 ms/tok"}
        ],
        "dashboard_kpis": [
            {"label": "Inference Speed", "val": "124 tok/sec", "change": "▲ +45% Triton Kernel", "status": ""},
            {"label": "Model Perplexity", "val": "4.25", "change": "▼ -0.22 Quantized", "status": ""},
            {"label": "GPU Compute Util", "val": "92.4%", "change": "▲ Optimal Tensor Parallel", "status": ""},
            {"label": "Memory Footprint", "val": "42GB VRAM", "change": "FP8 Cache Active", "status": "purple"}
        ],
        "brand_logos": [
            {"name": "vLLM", "type": "rect", "color": "#6366F1"},
            {"name": "TRT-LLM", "type": "diamond", "color": "#10B981"},
            {"name": "TORCH", "type": "polygon", "color": "#EF4444"}
        ],
        "swot": {
            "s": "Extremely low perplexity model weights; optimized kernel runtime scaling.",
            "w": "High initial GPU capital expenditure; memory bandwidth bottlenecks.",
            "o": "Mixed-precision quantizations (INT4/FP8) unlocking edge deployment nodes.",
            "t": "Rapid architectural obsolescence and open-source licensing updates."
        },
        "visual_svg": """
        <svg width="100%" height="80" viewBox="0 0 200 120" style="max-height: 80px; background: #0F172A; border-radius: 4px;">
            <line x1="30" y1="30" x2="90" y2="30" stroke="#38BDF8" stroke-width="0.8" opacity="0.5"/>
            <line x1="30" y1="30" x2="90" y2="60" stroke="#38BDF8" stroke-width="0.8" opacity="0.3"/>
            <line x1="30" y1="60" x2="90" y2="30" stroke="#38BDF8" stroke-width="0.8" opacity="0.3"/>
            <line x1="30" y1="60" x2="90" y2="60" stroke="#38BDF8" stroke-width="0.8" opacity="0.6"/>
            <line x1="30" y1="90" x2="90" y2="60" stroke="#38BDF8" stroke-width="0.8" opacity="0.4"/>
            <line x1="30" y1="90" x2="90" y2="90" stroke="#38BDF8" stroke-width="0.8" opacity="0.5"/>
            <line x1="90" y1="30" x2="160" y2="60" stroke="#F59E0B" stroke-width="1"/>
            <line x1="90" y1="60" x2="160" y2="60" stroke="#F59E0B" stroke-width="1"/>
            <line x1="90" y1="90" x2="160" y2="60" stroke="#F59E0B" stroke-width="1"/>
            <circle cx="30" cy="30" r="4" fill="#38BDF8"/>
            <circle cx="30" cy="60" r="4" fill="#38BDF8"/>
            <circle cx="30" cy="90" r="4" fill="#38BDF8"/>
            <circle cx="90" cy="30" r="4" fill="#818CF8"/>
            <circle cx="90" cy="60" r="4" fill="#818CF8"/>
            <circle cx="90" cy="90" r="4" fill="#818CF8"/>
            <circle cx="160" cy="60" r="5" fill="#F59E0B"/>
            <text x="30" y="20" font-family="sans-serif" font-size="7" fill="#94A3B8" text-anchor="middle">Input</text>
            <text x="90" y="20" font-family="sans-serif" font-size="7" fill="#94A3B8" text-anchor="middle">Attention</text>
            <text x="160" y="50" font-family="sans-serif" font-size="7" fill="#94A3B8" text-anchor="middle">Output</text>
        </svg>
        """,
        "timeline": [
            {"time": "H1 2026: FP8 Quantization", "desc": "Consolidated LLaMA weights into FP8 format, achieving 2x throughput scaling."},
            {"time": "H2 2026: vLLM Server Integration", "desc": "Dynamic continuous batching active across all inference clusters."}
        ],
        "table": {
            "headers": ["Model Precision", "Throughput", "Perplexity", "VRAM Savings"],
            "rows": [
                ["FP16 Standard", "35 tokens/s", "4.12", "0% (Reference)"],
                ["FP8 Quantized", "85 tokens/s", "4.18", "50% (High)"],
                ["INT4 AWQ", "120 tokens/s", "4.32", "75% (Extreme)"]
            ]
        },
        "charts": {
            "bar": {"title": "Training FLOPs Scaling Curve", "ylabel": "Compute Scale (EFLOPs)"},
            "line": {"title": "Model Perplexity Convergence & Loss Curves"},
            "donut": {"title": "GPU Compute Profile (Attention vs Linear)"},
            "hbar": {"title": "Inference Latency across Quantizations"},
            "area": {"title": "KV-Cache Memory Footprint Growth"}
        },
        "fallbacks": {
            "Executive Summary & Framework": "The technical evaluation of the neural network framework outlines a highly optimized approach to model architecture, quantization efficiency, and hardware-accelerated inference. To maximize computational throughput, engineers must aggressively optimize memory bandwidth, leverage mixed-precision kernels (e.g., FP8/INT4), and minimize model perplexity. A robust optimization framework is essential for navigating these deep neural networks, allowing practitioners to maximize FLOPS utilization while maintaining high generation accuracy. Ultimately, our core thesis posits that neural network performance is directly proportional to memory bandwidth utilization and kernel efficiency.",
            "Market Analysis & Sector Segmentation": "A rigorous, multi-layered structural analysis of the transformer architecture highlights substantial optimization opportunities across transformer blocks, attention mechanisms, and linear projection layers. Current architectural benchmarks suggest a significant performance premium in models utilizing FlashAttention and group-query attention (GQA) compared to standard multi-head attention. This efficiency is characterized by a dramatic reduction in KV cache size, allowing for longer context windows and higher batch sizes.",
            "Quantitative Performance & Revenue Velocity": "Analyzing the quantitative performance metrics demonstrates a clear correlation between model quantization and tokens-per-second throughput. Key performance indicators, including latency to first token, generation velocity, and GPU memory footprint, showcase strong efficiency gains when transitioning to low-precision formats. This throughput outperformance is primarily driven by memory bandwidth conservation, where quantized weights allow larger models to fit entirely within high-speed SRAM.",
            "Operational Efficiency & Architecture": "The operational infrastructure supporting the ML pipeline is engineered to maximize hardware utilization, minimize cold-start latency, and ensure scalable model serving. Modern AI serving systems rely on vLLM engines, tensor parallelism, and dynamic batching to maximize inference throughput. By employing specialized model servers, enterprises can dynamically schedule requests, optimize KV cache allocation, and reduce queue latency.",
            "Risk Analysis, Vulnerability & Strategic Outlook": "A comprehensive risk assessment of the model deployment identifies several critical vulnerability vectors inherent to large-scale deep learning pipelines. Chief among these risks are data leakage, model adversarial attacks, and potential licensing compliance issues with training corpuses. Implementing a robust security framework is essential, combining input/output sanitization, secure weight encryption, and automated compliance auditing."
        }
    },
    "corporate": {
        "name": "Corporate Strategy & Business Operations",
        "template": "amber",
        "cover_kpis": [
            {"label": "Addressable Market", "val": "$12.4 Billion"},
            {"label": "Operating Margin", "val": "18.5% LTM"},
            {"label": "Headcount Scaling", "val": "+12.4% YoY"}
        ],
        "dashboard_kpis": [
            {"label": "Operating Leverage", "val": "2.4x Target", "change": "▲ +15% Efficiency", "status": ""},
            {"label": "Customer Churn", "val": "2.4% Annual", "change": "▼ -0.5% Retention", "status": ""},
            {"label": "Asset Turnover", "val": "1.8x Ratio", "change": "▲ Optimal Flow", "status": ""},
            {"label": "Strategy Rating", "val": "Strong Moat", "change": "High Pricing Power", "status": "purple"}
        ],
        "brand_logos": [
            {"name": "MCK", "type": "rect", "color": "#D97706"},
            {"name": "BCG", "type": "diamond", "color": "#10B981"},
            {"name": "BAIN", "type": "polygon", "color": "#EF4444"}
        ],
        "swot": {
            "s": "Unsurpassed brand equity; highly disciplined cost mitigation frameworks.",
            "w": "Organizational inertia across legacy business units.",
            "o": "Automating routine transactional workflows to unlock operating leverage.",
            "t": "Rapid technological disruption and aggressive low-cost market entrants."
        },
        "visual_svg": """
        <svg width="100%" height="80" viewBox="0 0 200 120" style="max-height: 80px; background: #FFFDF5; border-radius: 4px;">
            <rect x="10" y="45" width="40" height="30" rx="3" fill="none" stroke="#D97706" stroke-width="1.2"/>
            <text x="30" y="62" font-family="sans-serif" font-size="6" fill="#78350F" text-anchor="middle">Suppliers</text>
            <rect x="75" y="45" width="50" height="30" rx="3" fill="#FEF3C7" stroke="#D97706" stroke-width="1.5"/>
            <text x="100" y="62" font-family="sans-serif" font-size="7" font-weight="bold" fill="#78350F" text-anchor="middle">Rivalry</text>
            <rect x="150" y="45" width="40" height="30" rx="3" fill="none" stroke="#D97706" stroke-width="1.2"/>
            <text x="170" y="62" font-family="sans-serif" font-size="6" fill="#78350F" text-anchor="middle">Buyers</text>
            <path d="M 50 60 L 75 60" fill="none" stroke="#D97706" stroke-width="1"/>
            <path d="M 125 60 L 150 60" fill="none" stroke="#D97706" stroke-width="1"/>
            <text x="100" y="20" font-family="sans-serif" font-size="8" font-weight="bold" fill="#451A03" text-anchor="middle">Porter's Competitive Landscape</text>
        </svg>
        """,
        "timeline": [
            {"time": "Operational Audit Phase", "desc": "Identified $15M in redundant overhead expenses across core administrative pipelines."},
            {"time": "Synergy Mapping Completed", "desc": "Cross-departmental collaboration structures finalized to unlock scale economics."}
        ],
        "table": {
            "headers": ["Business Unit", "Market Share", "Operating Margin", "Growth Focus"],
            "rows": [
                ["Enterprise Software", "38% (Leader)", "42% (High)", "Product Expansion"],
                ["Consulting Services", "15% (Challenger)", "18% (Med)", "Talent Density"]
            ]
        },
        "charts": {
            "bar": {"title": "Annual Consolidated Growth", "ylabel": "Revenue ($ Millions)"},
            "line": {"title": "Operating Leverage & Fixed Costs"},
            "donut": {"title": "Asset Contribution to Cash Flow"},
            "hbar": {"title": "Porter's Force Intensity Scores"},
            "area": {"title": "McKinsey Growth-Share Allocation Profile"}
        },
        "fallbacks": {
            "Executive Summary & Framework": "The comprehensive evaluation of the corporate landscape reveals a profound paradigm shift, driven by accelerating technology adoption vectors, evolving consumer demand, and restructuring regulatory frameworks. To remain competitive in this fast-moving landscape, market participants must aggressively adapt their core operational architectures, integrate scalable digital resources, and optimize capital allocation strategies. A robust analytical framework is essential for navigating these multi-dimensional changes, allowing firms to identify untapped value drivers while simultaneously mitigating systemic integration risks.",
            "Market Analysis & Sector Segmentation": "A rigorous, multi-layered market analysis of the ecosystem highlights substantial structural transformations across all primary, secondary, and tertiary sector segments. Current macroeconomic indicators suggest a significant reallocation of institutional capital away from legacy frameworks and toward highly agile, software-defined platforms. This shift is characterized by a growing polarization between first-mover innovators who capture exponential market share and late-stage adopters struggling with technical debt.",
            "Quantitative Performance & Revenue Velocity": "Analyzing the quantitative performance metrics demonstrates a clear correlation between technological integration and compounding revenue velocity. Key financial indicators, including annual recurring revenue, net revenue retention, and customer lifetime value, showcase strong upward trends among organizations that have fully embraced digital transformation. This financial outperformance is primarily driven by operational leverage.",
            "Operational Efficiency & Infrastructure": "The operational infrastructure is undergoing a massive reconfiguration, centered on maximizing throughput, minimizing latency, and ensuring continuous platform availability. Modern logistics pipelines are highly distributed, requiring sophisticated coordination mechanisms to manage real-time data flows, physical supply chains, and computational resource allocation. By transitioning to serverless architectures, edge computing nodes, and automated containerization, enterprises can significantly reduce their operational footprint.",
            "Risk Analysis, Vulnerability & Strategic Outlook": "A comprehensive risk assessment identifies several critical vulnerability vectors that organizations must proactively address to safeguard their market position. Chief among these risks are shifting regulatory compliance standards, cybersecurity threats targeting distributed nodes, and potential disruptions in global supply chains. Implementing a robust, multi-layered defensive posture is essential for mitigating these threats."
        }
    },
    "crypto": {
        "name": "Cryptographic Assets & Blockchain Ledger Research",
        "template": "dark",
        "cover_kpis": [
            {"label": "Total Value Locked", "val": "$84.5 Billion"},
            {"label": "Active Validators", "val": "18,450 Nodes"},
            {"label": "Ecosystem CAGR", "val": "+38.4% YoY"}
        ],
        "dashboard_kpis": [
            {"label": "Staking Yield", "val": "6.8% Ann.", "change": "▲ Stable Rewards", "status": ""},
            {"label": "Gas Fees (Avg)", "val": "$0.025/Tx", "change": "▼ -85% L2 Scaling", "status": ""},
            {"label": "Developer Count", "val": "8,450 Act.", "change": "▲ +22.4% GitHub", "status": ""},
            {"label": "Consensus Index", "val": "98.4 / 100", "change": "Proof of Stake", "status": "purple"}
        ],
        "brand_logos": [
            {"name": "BTC", "type": "rect", "color": "#F59E0B"},
            {"name": "ETH", "type": "diamond", "color": "#6366F1"},
            {"name": "SOL", "type": "polygon", "color": "#10B981"}
        ],
        "swot": {
            "s": "Decentralized consensus guarantees; permissionless global liquidity access.",
            "w": "Smart contract security bugs; high gas fees during congestion.",
            "o": "Layer-2 rollup scalability integrations and tokenized real-world assets.",
            "t": "Stricter regulatory compliance actions and protocol hardfork risks."
        },
        "visual_svg": """
        <svg width="100%" height="80" viewBox="0 0 200 120" style="max-height: 80px; background: #0B0F19; border-radius: 4px;">
            <rect x="15" y="40" width="40" height="40" rx="3" fill="none" stroke="#6366F1" stroke-width="1.5"/>
            <text x="35" y="62" font-family="sans-serif" font-size="8" fill="#E0E7FF" text-anchor="middle">Block 248</text>
            <path d="M 55 60 L 75 60" fill="none" stroke="#10B981" stroke-width="2" stroke-dasharray="2,2"/>
            <polygon points="75,60 70,57 70,63" fill="#10B981"/>
            <rect x="75" y="40" width="40" height="40" rx="3" fill="none" stroke="#6366F1" stroke-width="1.5"/>
            <text x="95" y="62" font-family="sans-serif" font-size="8" fill="#E0E7FF" text-anchor="middle">Block 249</text>
            <path d="M 115 60 L 135 60" fill="none" stroke="#10B981" stroke-width="2" stroke-dasharray="2,2"/>
            <polygon points="135,60 130,57 130,63" fill="#10B981"/>
            <rect x="135" y="40" width="40" height="40" rx="3" fill="none" stroke="#6366F1" stroke-width="1.5"/>
            <text x="155" y="62" font-family="sans-serif" font-size="8" fill="#E0E7FF" text-anchor="middle">Block 250</text>
            <text x="100" y="22" font-family="sans-serif" font-size="8" font-weight="bold" fill="#10B981" text-anchor="middle">Consensus: Proof of Stake</text>
        </svg>
        """,
        "timeline": [
            {"time": "Hardfork Upgrades", "desc": "Completed consensus transition to PoS, reducing energy footprints by 99%."},
            {"time": "L2 Rollup Activation", "desc": "Deployed zk-rollups, expanding transaction capacity by 20x."}
        ],
        "table": {
            "headers": ["Protocol", "TVL ($M)", "Active Validators", "Transaction Fees"],
            "rows": [
                ["Ethereum L1", "$42,500M", "12,450 Nodes", "$2.50 (High)"],
                ["Solana L1", "$8,400M", "2,840 Nodes", "$0.00025 (Low)"]
            ]
        },
        "charts": {
            "bar": {"title": "Total Value Locked Growth", "ylabel": "TVL ($ Billions)"},
            "line": {"title": "Transaction Throughput (TPS) & Gas Trends"},
            "donut": {"title": "Asset Concentration by Ecosystem Sector"},
            "hbar": {"title": "Protocol Decentralization Metrics (Nakamoto)"},
            "area": {"title": "Cumulative Smart Contract Risk Index"}
        },
        "fallbacks": {
            "Executive Summary & Framework": "The quantitative evaluation of the cryptographic sector outlines a structured approach to decentralization, smart-contract execution, and scalable consensus architectures. To maximize network utility, protocol developers must aggressively optimize transaction throughput, leverage layered scaling protocols (e.g., Rollups/L2s), and minimize smart-contract gas execution profiles. Ultimately, our core thesis posits that blockchain utility is directly proportional to network decentralization and the security of its execution layer.",
            "Market Analysis & Sector Segmentation": "A rigorous, multi-layered structural analysis of the decentralized ledger landscape highlights substantial optimization opportunities across smart contract networks, decentralized finance (DeFi), and tokenized real-world assets. Current blockchain benchmarks suggest a significant transaction velocity premium in modular architectures compared to monolithic ledgers. Understanding these shifting dynamics requires a granular examination of network liquidity, developer activity, and fee dynamics.",
            "Quantitative Performance & Revenue Velocity": "Analyzing the quantitative performance metrics demonstrates a clear correlation between tokenomics design and compounding total value locked (TVL). Key performance indicators, including staking yield velocity, transaction throughput, and active wallet expansion, showcase strong network-effect gains when protocol incentives are dynamically adjusted. This utility outperformance is primarily driven by smart contract automation.",
            "Operational Efficiency & Architecture": "The operational infrastructure supporting the consensus network is engineered to maximize validation throughput, minimize synchronization latency, and ensure Byzantine fault tolerance. Modern validators rely on high-speed fiber-optic connections, SSD-cached ledger databases, and co-located hardware clusters. Operational efficiency benchmarks indicate that validators utilizing optimized client software achieve substantially higher uptime and lower slashes.",
            "Risk Analysis, Vulnerability & Strategic Outlook": "A comprehensive risk assessment of the protocol deployment identifies several critical vulnerability vectors inherent to decentralized ledger systems. Chief among these risks are smart contract exploits, consensus censorship attacks, and shifting regulatory compliance standards across international jurisdictions. Implementing a robust protocol safety framework is essential, combining multi-signature custody, real-time audit scripts, and decentralized governance."
        }
    },
    "macro": {
        "name": "Macroeconomics & Monetary Policy Research",
        "template": "indigo",
        "cover_kpis": [
            {"label": "Real GDP Growth", "val": "+2.4% Ann."},
            {"label": "Core Inflation", "val": "2.8% YoY"},
            {"label": "Fed Funds Rate", "val": "5.25% - 5.50%"}
        ],
        "dashboard_kpis": [
            {"label": "Yield Curve Skew", "val": "-120 bps (10Y-2Y)", "change": "▼ Inverted Profile", "status": ""},
            {"label": "Unemployment", "val": "3.8%", "change": "▲ +10 bps YoY", "status": ""},
            {"label": "Retail Sales Growth", "val": "+1.8% LTM", "change": "▼ Cooling Demand", "status": ""},
            {"label": "Macro Stability", "val": "Stable Baseline", "change": "Soft Landing Path", "status": "purple"}
        ],
        "brand_logos": [
            {"name": "FED", "type": "rect", "color": "#6366F1"},
            {"name": "ECB", "type": "diamond", "color": "#10B981"},
            {"name": "IMF", "type": "polygon", "color": "#EF4444"}
        ],
        "swot": {
            "s": "Resilient labor market buffers; stable capital inflows protecting currencies.",
            "w": "High public sector debt burden; structural productivity growth constraints.",
            "o": "Monetary easing cycles opening capital deployment pathways.",
            "t": "Geopolitical tariff escalations and energy price supply shocks."
        },
        "visual_svg": """
        <svg width="100%" height="80" viewBox="0 0 200 120" style="max-height: 80px; background: #F8FAFC; border-radius: 4px;">
            <line x1="30" y1="100" x2="170" y2="100" stroke="#94A3B8" stroke-width="1"/>
            <line x1="30" y1="20" x2="30" y2="100" stroke="#94A3B8" stroke-width="1"/>
            <path d="M 40 30 L 160 90" fill="none" stroke="#EF4444" stroke-width="2"/>
            <path d="M 40 90 L 160 30" fill="none" stroke="#3B82F6" stroke-width="2"/>
            <circle cx="100" cy="60" r="4.5" fill="#F59E0B"/>
            <text x="100" y="52" font-family="sans-serif" font-size="7" font-weight="bold" fill="#0F172A" text-anchor="middle">Equilibrium</text>
            <text x="100" y="18" font-family="sans-serif" font-size="8" font-weight="bold" fill="#0F172A" text-anchor="middle">Macroeconomic IS-LM Curves</text>
        </svg>
        """,
        "timeline": [
            {"time": "Monetary Policy Pivot", "desc": "Federal Reserve initiated a 25 bps rate reduction, signaling confidence in inflation moderation."},
            {"time": "Fiscal Budget Finalization", "desc": "Infrastructure spending bills approved, projecting a 0.8% annual GDP boost."}
        ],
        "table": {
            "headers": ["Country", "GDP Growth", "Inflation Rate", "Debt-to-GDP"],
            "rows": [
                ["United States", "+2.4% (Stable)", "2.8% (Target)", "122% (High)"],
                ["Eurozone", "+0.8% (Sluggish)", "2.2% (Target)", "92% (Med)"]
            ]
        },
        "charts": {
            "bar": {"title": "Annual Real GDP Expansion", "ylabel": "GDP Growth (%)"},
            "line": {"title": "Core Inflation vs Central Bank Policy Rates"},
            "donut": {"title": "National Debt Allocation by Holder Class"},
            "hbar": {"title": "Global Trade Balance & Currencies"},
            "area": {"title": "Cumulative Sovereign Debt Exposure Risks"}
        },
        "fallbacks": {
            "Executive Summary & Framework": "The comprehensive evaluation of the global macroeconomic landscape reveals a profound paradigm shift, driven by restructuring supply chains, evolving demographic trends, and shifts in central bank monetary policy. To ensure financial stability, policy analysts and market participants must aggressively monitor inflation expectations, evaluate sovereign debt metrics, and optimize asset allocation structures. Ultimately, our core economic thesis posits that long-term real growth is a function of total factor productivity, demographic tailwinds, and fiscal capital allocation prudence.",
            "Market Analysis & Sector Segmentation": "A rigorous, multi-layered structural analysis of global markets highlights substantial realignment across primary, secondary, and tertiary economic sectors. Current monetary indicators suggest a significant transition away from low-interest environments and toward normalized yield structures. This structural shift is characterized by a growing polarization between capital-rich nations and emerging markets facing currency depreciation pressures.",
            "Quantitative Performance & Revenue Velocity": "Analyzing the quantitative performance metrics demonstrates a clear correlation between central bank rate actions and sovereign yield curves. Key performance indicators, including retail sales velocity, industrial production indices, and employment metrics, showcase stabilization trends as monetary tightening cycles mature. This macroeconomic stabilization is primarily driven by consumer demand resilience.",
            "Operational Efficiency & Architecture": "The operational infrastructure supporting global trade and capital flows is undergoing a massive reconfiguration, centered on logistics corridors, central bank digital currencies, and payment clearing mechanisms. Modern international commerce relies on SWIFT networks, real-time gross settlement (RTGS) systems, and localized trade agreements. Understanding these shifting dynamics is critical.",
            "Risk Analysis, Vulnerability & Strategic Outlook": "A comprehensive risk assessment of the macroeconomic outlook identifies several critical vulnerability vectors. Chief among these risks are sovereign debt defaults, interest rate mismatches across banking sectors, and potential supply shocks in global commodity markets. Implementing a robust defensive posture is essential, combining currency hedging, fiscal buffers, and diversified asset reserves."
        }
    },
    "healthcare": {
        "name": "Healthcare Systems & Digital Health Delivery",
        "template": "emerald",
        "cover_kpis": [
            {"label": "Digital Adoption", "val": "68% of Clinics"},
            {"label": "Patient Throughput", "val": "+18.4% YoY"},
            {"label": "Est. Market Size", "val": "$420 Billion"}
        ],
        "dashboard_kpis": [
            {"label": "Bed Utilization", "val": "82.4% Avg", "change": "▲ +120 bps YoY", "status": ""},
            {"label": "Readmit Rate", "val": "4.2% (Low)", "change": "▼ -0.5% Quality", "status": ""},
            {"label": "Clinical Staffing", "val": "98% Fill Rate", "change": "▲ Strong Retention", "status": ""},
            {"label": "Quality Score", "val": "92 / 100", "change": "Joint Commission", "status": "purple"}
        ],
        "brand_logos": [
            {"name": "EPIC", "type": "rect", "color": "#10B981"},
            {"name": "CERNER", "type": "diamond", "color": "#3B82F6"},
            {"name": "ATHENA", "type": "polygon", "color": "#F59E0B"}
        ],
        "swot": {
            "s": "High medical talent density; advanced clinical imaging capabilities.",
            "w": "Siloed EHR data architectures; high administrative overhead expenses.",
            "o": "AI-driven diagnostics integration and telemedicine platform scaling.",
            "t": "Shifting healthcare insurance compliance and data privacy regulations."
        },
        "visual_svg": """
        <svg width="100%" height="80" viewBox="0 0 200 120" style="max-height: 80px; background: #F8FAFC; border-radius: 4px;">
            <path d="M 20 60 Q 50 20 80 60 T 140 60 T 200 60" fill="none" stroke="#3B82F6" stroke-width="2"/>
            <path d="M 20 60 Q 50 100 80 60 T 140 60 T 200 60" fill="none" stroke="#EF4444" stroke-width="2"/>
            <line x1="50" y1="33" x2="50" y2="87" stroke="#94A3B8" stroke-width="1"/>
            <line x1="110" y1="33" x2="110" y2="87" stroke="#94A3B8" stroke-width="1"/>
            <circle cx="50" cy="33" r="2.5" fill="#3B82F6"/>
            <circle cx="50" cy="87" r="2.5" fill="#EF4444"/>
            <circle cx="110" cy="33" r="2.5" fill="#EF4444"/>
            <circle cx="110" cy="87" r="2.5" fill="#3B82F6"/>
            <text x="100" y="18" font-family="sans-serif" font-size="8" font-weight="bold" fill="#0F172A" text-anchor="middle">Clinical Diagnostics Matrix</text>
        </svg>
        """,
        "timeline": [
            {"time": "EHR Standardization", "desc": "Unified all clinical facilities under Epic Systems EHR framework to streamline workflows."},
            {"time": "Telehealth Platform Rollout", "desc": "Launched patient-facing digital care platform, expanding outpatient throughput by 35%."}
        ],
        "table": {
            "headers": ["Clinical Unit", "Occupancy", "Avg Stay (Days)", "Quality Rating"],
            "rows": [
                ["Cardiology", "85% (High)", "4.2 Days", "5-Star (Premium)"],
                ["Neurology", "78% (Med)", "5.8 Days", "4-Star (High)"]
            ]
        },
        "charts": {
            "bar": {"title": "Annual Patient Admissions Growth", "ylabel": "Admissions (Thousands)"},
            "line": {"title": "Patient Readmission Rates & Quality Outcomes"},
            "donut": {"title": "Clinical Operational Expense Breakdown"},
            "hbar": {"title": "Provider Performance & Clinical Benchmarks"},
            "area": {"title": "Cumulative Hospital Risk Profile"}
        },
        "fallbacks": {
            "Executive Summary & Framework": "The comprehensive evaluation of the healthcare delivery landscape reveals a profound paradigm shift, driven by digital health integration, shifting patient demographics, and restructuring regulatory compliance guidelines. To secure patient-care quality, clinical systems must aggressively optimize EHR integration, manage clinician workflows, and target clinical outcome metrics. A robust analytical framework is essential for navigating these clinical transformations, allowing administrators to identify patient-throughput bottlenecks.",
            "Market Analysis & Sector Segmentation": "A rigorous, multi-layered structural analysis of the healthcare ecosystem highlights substantial transformations across primary care, acute care, and telemedicine segments. Current indicators suggest a significant reallocation of capital toward integrated, value-based care platforms. This shift is characterized by a growing polarization between digital-first healthcare networks and legacy systems struggling with clinical staff burnout.",
            "Quantitative Performance & Revenue Velocity": "Analyzing the quantitative performance metrics demonstrates a clear correlation between EHR optimization and clinician-throughput velocity. Key performance indicators, including average length of stay (ALOS), readmission rates, and patient-satisfaction scores, showcase strong upward trends among facilities that have fully digitized clinical workflows. This clinical outperformance is primarily driven by automated scheduling.",
            "Operational Efficiency & Architecture": "The operational infrastructure supporting clinical care is undergoing a massive reconfiguration, centered on maximizing patient throughput, minimizing wait times, and ensuring clinical system availability. Modern hospital systems are highly complex, requiring sophisticated coordination mechanisms to manage patient flows, clinical staffing, and medical supply chain inventory.",
            "Risk Analysis, Vulnerability & Strategic Outlook": "A comprehensive risk assessment of the clinical delivery landscape identifies several critical vulnerability vectors. Chief among these risks are cybersecurity threats targeting sensitive patient records, nurse staffing shortages, and shifting government insurance reimbursement policies. Implementing a robust, multi-layered defense is essential, combining secure database encryption, staff wellness programs, and compliance auditing."
        }
    },
    "cybersecurity": {
        "name": "Cybersecurity Risk & Enterprise Defense",
        "template": "crimson",
        "cover_kpis": [
            {"label": "Threat Block Rate", "val": "99.98% Ann."},
            {"label": "Avg Detection Time", "val": "12.4 Seconds"},
            {"label": "Vulnerability Index", "val": "14 / 100 Low"}
        ],
        "dashboard_kpis": [
            {"label": "Scan Velocity", "val": "8.4M T/sec", "change": "▲ +22.4% Engine", "status": ""},
            {"label": "Patch Latency", "val": "4.2 Hours", "change": "▼ -2.5 Hrs Auto", "status": ""},
            {"label": "Phish Resilient", "val": "98.5% Rate", "change": "▲ Training Complete", "status": ""},
            {"label": "Security Score", "val": "95 / 100", "change": "NIST Framework", "status": "purple"}
        ],
        "brand_logos": [
            {"name": "CROWD", "type": "rect", "color": "#EF4444"},
            {"name": "PALO", "type": "diamond", "color": "#3B82F6"},
            {"name": "SENT", "type": "polygon", "color": "#10B981"}
        ],
        "swot": {
            "s": "Advanced ML threat intelligence; zero-trust network policy compliance.",
            "w": "Complex integration across legacy hybrid-cloud enterprise servers.",
            "o": "Automated AI patch orchestration and next-generation endpoint firewalls.",
            "t": "Advanced persistent threat actors (APT) utilizing generative malware."
        },
        "visual_svg": """
        <svg width="100%" height="80" viewBox="0 0 200 120" style="max-height: 80px; background: #0B0F19; border-radius: 4px;">
            <rect x="85" y="55" width="30" height="25" rx="2" fill="none" stroke="#EF4444" stroke-width="1.5"/>
            <path d="M 90 55 L 90 40 A 10 10 0 0 1 110 40 L 110 55" fill="none" stroke="#EF4444" stroke-width="1.5"/>
            <circle cx="100" cy="65" r="3.5" fill="#EF4444"/>
            <path d="M 50 30 L 70 45 M 150 30 L 130 45 M 50 90 L 70 75 M 150 90 L 130 75" fill="none" stroke="#10B981" stroke-width="1" stroke-dasharray="2,2"/>
            <text x="100" y="22" font-family="sans-serif" font-size="8" font-weight="bold" fill="#10B981" text-anchor="middle">Zero Trust Architecture</text>
        </svg>
        """,
        "timeline": [
            {"time": "Zero Trust Pivot", "desc": "Migrated all enterprise access points to zero-trust architecture, neutralizing lateral threat paths."},
            {"time": "SOAR Platform Deployment", "desc": "Automated incident response playbook execution, lowering MTTR by 85%."}
        ],
        "table": {
            "headers": ["Vector", "Intrusions", "Mean Detection", "Status Index"],
            "rows": [
                ["Endpoint", "124/Month", "8.4 Seconds", "Secure (NIST)"],
                ["Cloud Servers", "42/Month", "14.2 Seconds", "Securing (AWS)"]
            ]
        },
        "charts": {
            "bar": {"title": "Monthly Intrusion Vector Blocks", "ylabel": "Blocked Attacks (Millions)"},
            "line": {"title": "Mean Time to Detect (MTTD) & Respond (MTTR)"},
            "donut": {"title": "Threat Vector Concentration Analysis"},
            "hbar": {"title": "Enterprise Security Controls Audit"},
            "area": {"title": "Cumulative Cyber Exposure Risk Profile"}
        },
        "fallbacks": {
            "Executive Summary & Framework": "The comprehensive technical evaluation of the enterprise security profile outlines a zero-trust approach to threat mitigation, cryptographic data security, and hardware endpoint defense. To maximize protection, cybersecurity architects must aggressively optimize network edge firewall rules, deploy real-time behavioral threat detection engines, and minimize access permission profiles. Ultimately, our core security thesis posits that enterprise network integrity is directly proportional to zero-trust policy enforcement.",
            "Market Analysis & Sector Segmentation": "A rigorous, multi-layered structural analysis of the cybersecurity landscape highlights substantial defense opportunities across cloud network perimeters, email gateways, and database access nodes. Current industry benchmarks suggest a significant mitigation premium in security architectures utilizing security orchestration, automation, and response (SOAR) platforms.",
            "Quantitative Performance & Revenue Velocity": "Analyzing the quantitative performance metrics demonstrates a clear correlation between automated patch orchestration and mean time to resolution (MTTR). Key performance indicators, including intrusion block counts, threat scan velocities, and phishing training compliance rates, showcase strong defensive gains when security policies are automated.",
            "Operational Efficiency & Architecture": "The operational infrastructure supporting enterprise threat monitoring is engineered to maximize packet inspection throughput, minimize alert fatigue, and ensure secure data transmission. Modern security operation centers (SOC) rely on SIEM engines, AI-accelerated log analytics, and co-located threat analysts. Understanding these tools is vital.",
            "Risk Analysis, Vulnerability & Strategic Outlook": "A comprehensive risk assessment of the threat landscape identifies several critical vulnerability vectors inherent to distributed hybrid-cloud databases. Chief among these risks are ransomware vectors, supply chain code injections, and potential regulatory non-compliance fines. Implementing a robust security framework is essential, combining secure endpoint encryption and real-time scanning."
        }
    },
    "esg": {
        "name": "Climate Technology & ESG Governance",
        "template": "emerald",
        "cover_kpis": [
            {"label": "Carbon Abated", "val": "1.25M Tons CO2"},
            {"label": "ESG Rating Score", "val": "88 / 100 AAA"},
            {"label": "Renewable Mix", "val": "64.2% Share"}
        ],
        "dashboard_kpis": [
            {"label": "Carbon Intensity", "val": "42g CO2/kWh", "change": "▼ -22.4% Solar", "status": ""},
            {"label": "Water Recycling", "val": "84.2%", "change": "▲ +120 bps Ann.", "status": ""},
            {"label": "Green Capex", "val": "$180M", "change": "▲ +18.7% YoY", "status": ""},
            {"label": "Taxonomy Index", "val": "92.4 / 100", "change": "EU Green Compliant", "status": "purple"}
        ],
        "brand_logos": [
            {"name": "VESTAS", "type": "rect", "color": "#10B981"},
            {"name": "ORSTED", "type": "diamond", "color": "#3B82F6"},
            {"name": "TESLA", "type": "polygon", "color": "#F59E0B"}
        ],
        "swot": {
            "s": "First-mover advantage in green taxonomy; carbon tax buffer resilience.",
            "w": "High upfront capital requirements for renewable infrastructure.",
            "o": "Global carbon offset market expansion and ESG-linked debt structures.",
            "t": "Shifting green subsidization policies and supply chain material shortages."
        },
        "visual_svg": """
        <svg width="100%" height="80" viewBox="0 0 200 120" style="max-height: 80px; background: #F0FDFA; border-radius: 4px;">
            <line x1="40" y1="80" x2="160" y2="80" stroke="#0D9488" stroke-width="2"/>
            <polygon points="100,80 95,95 105,95" fill="#0D9488"/>
            <line x1="50" y1="80" x2="50" y2="50" stroke="#0D9488" stroke-width="1"/>
            <rect x="35" y="40" width="30" height="10" fill="#EF4444" rx="2"/>
            <text x="50" y="47" font-family="sans-serif" font-size="6" fill="#FFFFFF" text-anchor="middle">CO2</text>
            <line x1="150" y1="80" x2="150" y2="50" stroke="#0D9488" stroke-width="1"/>
            <rect x="135" y="40" width="30" height="10" fill="#10B981" rx="2"/>
            <text x="150" y="47" font-family="sans-serif" font-size="6" fill="#FFFFFF" text-anchor="middle">OFFSETS</text>
            <text x="100" y="22" font-family="sans-serif" font-size="8" font-weight="bold" fill="#0F766E" text-anchor="middle">Net Zero Carbon Balance</text>
        </svg>
        """,
        "timeline": [
            {"time": "Grid Decarbonization", "desc": "Completed solar integration across principal logistics networks, offsetting 400k tons CO2 annually."},
            {"time": "Taxonomy Alignment", "desc": "Refactored accounting structures to fully comply with EU Green Taxonomy disclosures."}
        ],
        "table": {
            "headers": ["Facility", "Carbon Intensity", "Waste Recycled", "ESG Score"],
            "rows": [
                ["Guindy Plant", "24g CO2/kWh", "92% (High)", "AAA (Premium)"],
                ["OMR Hub", "48g CO2/kWh", "78% (Med)", "AA (High)"]
            ]
        },
        "charts": {
            "bar": {"title": "Annual Carbon Offset Volumes", "ylabel": "Offsets (Thousand Tons)"},
            "line": {"title": "Emission Intensities & ESG Performance"},
            "donut": {"title": "Green Capex Distribution by Project"},
            "hbar": {"title": "Sustainability Performance vs Peers"},
            "area": {"title": "Cumulative Climate Regulatory Risk Profile"}
        },
        "fallbacks": {
            "Executive Summary & Framework": "The comprehensive evaluation of the climate technology landscape reveals a profound paradigm shift, driven by transition economics, shifting climate policies, and restructuring ESG disclosure standards. To remain competitive in this green transition, enterprises must aggressively optimize their carbon footprints, integrate energy-efficient supply architectures, and target clear net-zero metrics. A robust analytical framework is essential for navigating these ESG shifts, allowing partners to identify carbon abatement vectors.",
            "Market Analysis & Sector Segmentation": "A rigorous, multi-layered market analysis of the green ecosystem highlights substantial transformations across renewable energy, circular economy, and carbon capture segments. Current capital indicators suggest a significant reallocation of institutional funding away from fossil assets and toward green taxonomy platforms. This shift is characterized by a growing polarization between low-carbon leaders and legacy emitters.",
            "Quantitative Performance & Revenue Velocity": "Analyzing the quantitative performance metrics demonstrates a clear correlation between renewable energy integration and compounding operational cost savings. Key ESG indicators, including greenhouse gas emission intensities, waste recycling percentages, and green capital expenditures, showcase strong upward trends among firms that have fully digitized environmental auditing workflows.",
            "Operational Efficiency & Architecture": "The operational infrastructure supporting green manufacturing is undergoing a massive reconfiguration, centered on maximizing resource throughput, minimizing waste, and ensuring grid-interconnection stability. Modern ESG auditing pipelines are highly distributed, requiring sophisticated coordination mechanisms to manage real-time emission sensors, water recycling plants, and carbon ledger audits.",
            "Risk Analysis, Vulnerability & Strategic Outlook": "A comprehensive risk assessment of the climate technology landscape identifies several critical vulnerability vectors. Chief among these risks are shifting carbon pricing policies, climate-induced physical asset disruptions, and potential supply shortages in critical battery materials. Implementing a robust risk mitigation posture is essential, combining diversified energy reserves and real-time compliance tracking."
        }
    },
    "realestate": {
        "name": "Commercial Real Estate & REIT Valuations",
        "template": "amber",
        "cover_kpis": [
            {"label": "Portfolio Occupancy", "val": "94.2% Avg"},
            {"label": "Net Asset Value", "val": "$4.85 Billion"},
            {"label": "Cap Rate Yield", "val": "6.85% Ann."}
        ],
        "dashboard_kpis": [
            {"label": "Weighted Lease", "val": "5.8 Years", "change": "▲ Stable Duration", "status": ""},
            {"label": "Rental Growth", "val": "+8.4% YoY", "change": "▲ Strong Pricing", "status": ""},
            {"label": "Loan-to-Value", "val": "42.5%", "change": "▼ -150 bps Debt", "status": ""},
            {"label": "REIT Performance", "val": "Buy Target", "change": "NAV Discount 12%", "status": "purple"}
        ],
        "brand_logos": [
            {"name": "PLD", "type": "rect", "color": "#D97706"},
            {"name": "AMT", "type": "diamond", "color": "#10B981"},
            {"name": "EQIX", "type": "polygon", "color": "#EF4444"}
        ],
        "swot": {
            "s": "Premium logistics properties in supply-constrained metropolitan areas.",
            "w": "High financing costs impacting new commercial development yields.",
            "o": "Transitioning retail space into highly automated micro-fulfillment hubs.",
            "t": "Work-from-home structural shifts cooling office occupancy rates."
        },
        "visual_svg": """
        <svg width="100%" height="80" viewBox="0 0 200 120" style="max-height: 80px; background: #FFFDF5; border-radius: 4px;">
            <rect x="70" y="30" width="60" height="80" fill="none" stroke="#D97706" stroke-width="1.5"/>
            <line x1="90" y1="30" x2="90" y2="110" stroke="#D97706" stroke-width="0.8"/>
            <line x1="110" y1="30" x2="110" y2="110" stroke="#D97706" stroke-width="0.8"/>
            <line x1="70" y1="50" x2="130" y2="50" stroke="#D97706" stroke-width="0.8"/>
            <line x1="70" y1="70" x2="130" y2="70" stroke="#D97706" stroke-width="0.8"/>
            <line x1="70" y1="90" x2="130" y2="90" stroke="#D97706" stroke-width="0.8"/>
            <circle cx="100" cy="40" r="3" fill="#10B981"/>
            <circle cx="80" cy="60" r="3" fill="#10B981"/>
            <circle cx="120" cy="80" r="3" fill="#10B981"/>
            <text x="100" y="20" font-family="sans-serif" font-size="8" font-weight="bold" fill="#451A03" text-anchor="middle">Commercial Asset Distribution</text>
        </svg>
        """,
        "timeline": [
            {"time": "Logistics Expansion", "desc": "Completed $180M logistics asset deployment, capturing premium industrial occupancy along critical cargo ports."},
            {"time": "Refinancing Secured", "desc": "Restructured $400M debt at 4.2% fixed rate, shielding the portfolio from floating interest rate exposure."}
        ],
        "table": {
            "headers": ["Asset Class", "Occupancy", "Avg Cap Rate", "YoY Rental Growth"],
            "rows": [
                ["Logistics Hubs", "98% (High)", "5.2%", "+12.4% (Strong)"],
                ["Office Towers", "82% (Med)", "7.1%", "+2.1% (Slow)"]
            ]
        },
        "charts": {
            "bar": {"title": "Quarterly Rental Revenue Velocity", "ylabel": "Rental Income ($ Millions)"},
            "line": {"title": "Cap Rate Spreads vs Treasury Yields"},
            "donut": {"title": "Portfolio Value by Asset Segment"},
            "hbar": {"title": "Property NOI Benchmarks vs Peers"},
            "area": {"title": "Cumulative Real Estate Financing Risk"}
        },
        "fallbacks": {
            "Executive Summary & Framework": "The comprehensive evaluation of the commercial real estate portfolio indicates a robust underlying asset profile operating amidst evolving interest rate cycles and shifting urban demand patterns. To secure yield stability in this climate, the trust must aggressively optimize property operating expenses, manage lease expiration profiles, and accelerate high-growth logistics assets. A structured valuation framework is essential for assessing these trends, utilizing discounted cash flows and cap-rate spreads to isolate intrinsic real estate value from market volatility.",
            "Market Analysis & Sector Segmentation": "A rigorous, multi-layered market analysis of the commercial property sector highlights substantial structural transformations across logistics, multi-family, and office segments. Current indicators suggest a significant reallocation of institutional capital away from office assets and toward industrial properties. This shift is characterized by a growing polarization between class-A premium assets and class-B assets.",
            "Quantitative Performance & Revenue Velocity": "Analyzing the quantitative performance metrics demonstrates a clear correlation between logistics location density and compounding net operating income (NOI) growth. Key financial indicators, including portfolio occupancy, average lease duration, and loan-to-value (LTV) ratios, showcase strong upward trends among segments that have fully embraced automated property management systems. This financial outperformance is driven by lease indexations.",
            "Operational Efficiency & Architecture": "The operational infrastructure supporting property management is undergoing a massive reconfiguration, centered on maximizing utility efficiency, minimizing tenant turn times, and ensuring HVAC system reliability. Modern property pipelines are highly integrated, requiring sophisticated coordination mechanisms to manage building energy systems, smart-lock provisioning, and predictive maintenance schedules.",
            "Risk Analysis, Vulnerability & Strategic Outlook": "A comprehensive risk assessment of the real estate portfolio identifies several critical vulnerability vectors. Chief among these risks are interest rate volatility, tenant defaults in cyclical retail sectors, and potential property tax increases. Implementing a robust risk mitigation framework is essential, combining fixed-rate refinancing, diversified tenant credit screening, and proactive asset disposals."
        }
    },
    "manufacturing": {
        "name": "Advanced Manufacturing & Industrial Automation",
        "template": "indigo",
        "cover_kpis": [
            {"label": "OEE Score", "val": "88.5% (High)"},
            {"label": "Factory Output", "val": "+15.4% YoY"},
            {"label": "Inbound Materials", "val": "98.2% Fill"}
        ],
        "dashboard_kpis": [
            {"label": "Cycle Velocity", "val": "14.2 sec/unit", "change": "▲ +12% Robotics", "status": ""},
            {"label": "Quality Yield", "val": "99.98% Rate", "change": "▲ Six Sigma Path", "status": ""},
            {"label": "Plant Uptime", "val": "99.4%", "change": "▲ Predictive active", "status": ""},
            {"label": "OEE Rating", "val": "Elite Tier", "change": "Industry Leader", "status": "purple"}
        ],
        "brand_logos": [
            {"name": "SIEM", "type": "rect", "color": "#6366F1"},
            {"name": "ABB", "type": "diamond", "color": "#10B981"},
            {"name": "FANUC", "type": "polygon", "color": "#EF4444"}
        ],
        "swot": {
            "s": "Fully automated assembly pipelines; high Six Sigma manufacturing quality.",
            "w": "High initial capital expenditure on precision robotic arms.",
            "o": "AI predictive maintenance scaling to eliminate unplanned plant downtime.",
            "t": "Supply shortages in critical semiconductor chips and microcontrollers."
        },
        "visual_svg": """
        <svg width="100%" height="80" viewBox="0 0 200 120" style="max-height: 80px; background: #F8FAFC; border-radius: 4px;">
            <circle cx="40" cy="60" r="15" fill="none" stroke="#475569" stroke-width="2"/>
            <circle cx="160" cy="60" r="15" fill="none" stroke="#475569" stroke-width="2"/>
            <line x1="40" y1="45" x2="160" y2="45" stroke="#475569" stroke-width="2"/>
            <line x1="40" y1="75" x2="160" y2="75" stroke="#475569" stroke-width="2"/>
            <rect x="75" y="35" width="20" height="20" fill="#F59E0B" rx="2"/>
            <rect x="115" y="35" width="20" height="20" fill="#3B82F6" rx="2"/>
            <text x="100" y="20" font-family="sans-serif" font-size="8" font-weight="bold" fill="#0F172A" text-anchor="middle">High-Throughput Production Pipeline</text>
        </svg>
        """,
        "timeline": [
            {"time": "Robotic Integration", "desc": "Deployed 24 advanced robotic arms across assembly lines, reducing unit cycle times by 35%."},
            {"time": "Predictive Maintenance", "desc": "Launched vibration sensor diagnostics, eliminating unexpected machinery breakdown events."}
        ],
        "table": {
            "headers": ["Line Segment", "Throughput", "Quality Yield", "OEE Efficiency"],
            "rows": [
                ["Assembly Line A", "420 units/hr", "99.98% (High)", "88.5% (Elite)"],
                ["Packaging Line B", "850 units/hr", "99.95% (High)", "84.2% (High)"]
            ]
        },
        "charts": {
            "bar": {"title": "Annual Production Volumes", "ylabel": "Output (Thousand Units)"},
            "line": {"title": "Overall Equipment Effectiveness (OEE) Trends"},
            "donut": {"title": "Factory Operational Cost Breakdown"},
            "hbar": {"title": "Production Quality Yield Benchmarks"},
            "area": {"title": "Cumulative Plant Downtime Risk Profile"}
        },
        "fallbacks": {
            "Executive Summary & Framework": "The technical evaluation of the advanced manufacturing infrastructure outlines a highly automated approach to assembly line configuration, quality yield optimization, and hardware-accelerated production. To maximize factory throughput, plant engineers must aggressively optimize machinery cycle times, leverage predictive maintenance sensors (IoT), and minimize production scrap rates. A robust industrial framework is essential for navigating these automated lines, allowing operators to maximize overall equipment effectiveness (OEE) metrics.",
            "Market Analysis & Sector Segmentation": "A rigorous, multi-layered structural analysis of the manufacturing plant highlights substantial automation opportunities across assembly blocks, quality inspection loops, and component staging areas. Current production benchmarks suggest a significant yield premium in factories utilizing automated optical inspection (AOI) compared to manual inspection. Understanding these shifting dynamics requires a granular examination of cycle times.",
            "Quantitative Performance & Revenue Velocity": "Analyzing the quantitative performance metrics demonstrates a clear correlation between robotic integration and compounding unit-throughput velocity. Key performance indicators, including units produced per hour, quality yield percentages, and plant uptime rates, showcase strong efficiency gains when assembly tasks are fully automated. This throughput outperformance is primarily driven by precision robotics.",
            "Operational Efficiency & Architecture": "The operational infrastructure supporting the factory floor is engineered to maximize machinery utilization, minimize scrap costs, and ensure safe operator conditions. Modern manufacturing systems rely on programmable logic controllers (PLCs), centralized industrial networks, and co-located diagnostics monitors. Operational efficiency benchmarks indicate that plants utilizing automated scheduling achieve higher capacity.",
            "Risk Analysis, Vulnerability & Strategic Outlook": "A comprehensive risk assessment of the factory deployment identifies several critical vulnerability vectors inherent to large-scale automated production pipelines. Chief among these risks are raw material supply disruptions, machinery electrical faults, and potential industrial network security breaches. Implementing a robust safety framework is essential, combining redundant power systems and secure network architecture."
        }
    },
    "supplychain": {
        "name": "Global Supply Chain & Logistics Networks",
        "template": "indigo",
        "cover_kpis": [
            {"label": "Logistics Velocity", "val": "4.2 Days Avg"},
            {"label": "Inventory Turn", "val": "18.4x Annual"},
            {"label": "Supplier SLA", "val": "98.5% Compliant"}
        ],
        "dashboard_kpis": [
            {"label": "On-Time Delivery", "val": "98.2% Rate", "change": "▲ +120 bps Route", "status": ""},
            {"label": "Freight Cost", "val": "$840M LTM", "change": "▼ -8.4% Consolidation", "status": ""},
            {"label": "Warehouse Util", "val": "92.4%", "change": "▲ Optimal Flow Rate", "status": ""},
            {"label": "SLA Compliance", "val": "98.5% Score", "change": "Elite Logistics tier", "status": "purple"}
        ],
        "brand_logos": [
            {"name": "DHL", "type": "rect", "color": "#6366F1"},
            {"name": "FEDEX", "type": "diamond", "color": "#10B981"},
            {"name": "MAERSK", "type": "polygon", "color": "#EF4444"}
        ],
        "swot": {
            "s": "Highly diversified global supplier network; real-time cargo tracking.",
            "w": "Vulnerability to volatile international ocean freight rates.",
            "o": "Integrating AI-driven route optimization to reduce fuel consumption.",
            "t": "Geopolitical tariff barriers and port labor congestion spikes."
        },
        "visual_svg": """
        <svg width="100%" height="80" viewBox="0 0 200 120" style="max-height: 80px; background: #F8FAFC; border-radius: 4px;">
            <rect x="20" y="45" width="40" height="30" rx="3" fill="none" stroke="#475569" stroke-width="1.2"/>
            <text x="40" y="63" font-family="sans-serif" font-size="6" fill="#475569" text-anchor="middle">Supplier</text>
            <rect x="80" y="45" width="40" height="30" rx="3" fill="#E2E8F0" stroke="#475569" stroke-width="1.5"/>
            <text x="100" y="63" font-family="sans-serif" font-size="6" fill="#475569" text-anchor="middle">Warehouse</text>
            <rect x="140" y="45" width="40" height="30" rx="3" fill="none" stroke="#475569" stroke-width="1.2"/>
            <text x="160" y="63" font-family="sans-serif" font-size="6" fill="#475569" text-anchor="middle">Distributor</text>
            <path d="M 60 60 L 80 60" fill="none" stroke="#475569" stroke-width="1"/>
            <path d="M 120 60 L 140 60" fill="none" stroke="#475569" stroke-width="1"/>
            <text x="100" y="20" font-family="sans-serif" font-size="8" font-weight="bold" fill="#0F172A" text-anchor="middle">Logistics Distribution Flow</text>
        </svg>
        """,
        "timeline": [
            {"time": "Route Optimization", "desc": "Deployed machine learning navigation, cutting ocean transit times by 4.2 days."},
            {"time": "Warehouse Automation", "desc": "Completed sorting automation, expanding cargo throughput by 42%."}
        ],
        "table": {
            "headers": ["Corridor", "Transit Time", "Cost index", "On-Time Delivery"],
            "rows": [
                ["US - Europe", "12 Days (Ocean)", "100 (Reference)", "98.5% (High)"],
                ["Asia - US", "18 Days (Ocean)", "120 (High)", "95.8% (Med)"]
            ]
        },
        "charts": {
            "bar": {"title": "Monthly Cargo Volume Trends", "ylabel": "Volume (TEUs)"},
            "line": {"title": "On-Time Delivery Performance & Transit Times"},
            "donut": {"title": "Logistics Expense Breakdown by Mode"},
            "hbar": {"title": "Supplier Performance SLA Benchmarks"},
            "area": {"title": "Cumulative Supply Chain Risk Index"}
        },
        "fallbacks": {
            "Executive Summary & Framework": "The comprehensive evaluation of the global logistics profile indicates a robust underlying network operating amidst volatile fuel prices and shifting maritime trade agreements. To secure supply chain resilience in this climate, the enterprise must aggressively optimize warehouse inventory turns, manage supplier SLA agreements, and accelerate high-throughput freight corridors. A robust analytical framework is essential for navigating these logistics challenges, allowing partners to identify transit bottlenecks and shipping delays.",
            "Market Analysis & Sector Segmentation": "A rigorous, multi-layered market analysis of the logistics sector highlights substantial structural transformations across ocean freight, air cargo, and last-mile delivery segments. Current indicators suggest a significant reallocation of capital toward automated micro-fulfillment centers. This shift is characterized by a growing polarization between tech-enabled logistics operators and legacy freight forwarders.",
            "Quantitative Performance & Revenue Velocity": "Analyzing the quantitative performance metrics demonstrates a clear correlation between warehouse automation and compounding inventory turn velocities. Key logistics indicators, including on-time delivery rates, freight cost per ton-mile, and warehouse capacity utilization, showcase strong upward trends among operators that have fully integrated digital supply chain visibility systems. This financial outperformance is driven by route planning.",
            "Operational Efficiency & Architecture": "The operational infrastructure supporting global logistics is undergoing a massive reconfiguration, centered on maximizing warehouse throughput, minimizing shipping transit times, and ensuring real-time cargo visibility. Modern supply chain pipelines are highly integrated, requiring sophisticated coordination mechanisms to manage container shipments, truck dispatching, and inventory levels.",
            "Risk Analysis, Vulnerability & Strategic Outlook": "A comprehensive risk assessment of the logistics network identifies several critical vulnerability vectors. Chief among these risks are geopolitical tariff barriers, labor strikes at major cargo ports, and potential cybersecurity breaches targeting shipping software. Implementing a robust risk mitigation framework is essential, combining diversified shipping corridors, buffer inventory stocks, and proactive cargo tracking."
        }
    },
    "pharma": {
        "name": "Pharmaceutical Research & Clinical Trials",
        "template": "crimson",
        "cover_kpis": [
            {"label": "Clinical Pipeline", "val": "18 Drug Candidates"},
            {"label": "FDA Approval Rate", "val": "84.2% Phase II"},
            {"label": "R&D Expenditure", "val": "$420M LTM"}
        ],
        "dashboard_kpis": [
            {"label": "Trial Enrollment", "val": "84% (On Schedule)", "change": "▲ Patient Retention", "status": ""},
            {"label": "Trial Cost/Phase", "val": "$42.5M Avg", "change": "▼ -8.4% Efficiency", "status": ""},
            {"label": "Research Uptime", "val": "99.8%", "change": "▲ Continuous Labs", "status": ""},
            {"label": "Pipeline Rating", "val": "Elite Tier", "change": "Blockbuster Pipeline", "status": "purple"}
        ],
        "brand_logos": [
            {"name": "PFIZER", "type": "rect", "color": "#EF4444"},
            {"name": "ROCHE", "type": "diamond", "color": "#3B82F6"},
            {"name": "MERCK", "type": "polygon", "color": "#10B981"}
        ],
        "swot": {
            "s": "Extremely robust drug pipeline; advanced molecular screening clusters.",
            "w": "High failure rates during clinical Phase III trial stages.",
            "o": "Leveraging AI generative chemistry to accelerate drug discovery pipelines.",
            "t": "Strict FDA compliance standards and patent expiration horizons."
        },
        "visual_svg": """
        <svg width="100%" height="80" viewBox="0 0 200 120" style="max-height: 80px; background: #FFF5F5; border-radius: 4px;">
            <circle cx="40" cy="60" r="10" fill="#EF4444" opacity="0.8"/>
            <line x1="40" y1="60" x2="100" y2="60" stroke="#2D3748" stroke-width="1.5"/>
            <circle cx="100" cy="60" r="12" fill="#E53E3E" opacity="0.8"/>
            <line x1="100" y1="60" x2="160" y2="60" stroke="#2D3748" stroke-width="1.5"/>
            <circle cx="160" cy="60" r="10" fill="#EF4444" opacity="0.8"/>
            <text x="100" y="22" font-family="sans-serif" font-size="8" font-weight="bold" fill="#742A2A" text-anchor="middle">Molecular Structure Screening</text>
        </svg>
        """,
        "timeline": [
            {"time": "Phase II FDA Approval", "desc": "Completed clinical safety profile analysis, securing permission to initiate Phase III trials."},
            {"time": "AI Molecule Discovery", "desc": "Integrated generative chemistry model, screening 4 million compounds in 12 days."}
        ],
        "table": {
            "headers": ["Candidate ID", "Therapeutic Area", "Trial Phase", "FDA Status"],
            "rows": [
                ["ARK-2026-A", "Oncology", "Phase III (Trial)", "Fast Track (FDA)"],
                ["ARK-2026-B", "Cardiology", "Phase II (Trial)", "IND Approved"]
            ]
        },
        "charts": {
            "bar": {"title": "Annual Clinical Trials Capital", "ylabel": "R&D Spend ($ Millions)"},
            "line": {"title": "FDA Phase Transition Success Probabilities"},
            "donut": {"title": "R&D Resource Allocation by Pathology"},
            "hbar": {"title": "Drug Discovery Pipeline Latencies"},
            "area": {"title": "Cumulative Pipeline Patent Expiry Risk"}
        },
        "fallbacks": {
            "Executive Summary & Framework": "The technical evaluation of the pharmaceutical research pipeline outlines a highly structured approach to molecular screening, clinical trial safety, and FDA regulatory compliance. To maximize R&D efficiency, drug discovery teams must aggressively optimize molecule screening speeds, leverage generative chemistry models, and minimize Phase III trial dropouts. Ultimately, our core pharmaceutical thesis posits that research pipeline value is directly proportional to clinical trial transition probabilities.",
            "Market Analysis & Sector Segmentation": "A rigorous, multi-layered structural analysis of the biopharma landscape highlights substantial development opportunities across oncology, immunology, and rare genetic pathologies. Current research benchmarks suggest a significant discovery velocity premium in pipelines utilizing AI-assisted molecular docking compared to physical screening assays.",
            "Quantitative Performance & Revenue Velocity": "Analyzing the quantitative performance metrics demonstrates a clear correlation between molecular simulation scaling and compounding drug-candidate throughput. Key performance indicators, including clinical trial enrollment speeds, FDA transition ratios, and R&D capital efficiency, showcase strong pipeline gains when research tasks are digitized.",
            "Operational Efficiency & Architecture": "The operational infrastructure supporting clinical laboratories is engineered to maximize sample screening throughput, minimize contamination risks, and ensure secure patient data custody. Modern bio-informatics clusters rely on high-performance computing, automated liquid handling systems, and secure trial databases. Understanding these parameters is key.",
            "Risk Analysis, Vulnerability & Strategic Outlook": "A comprehensive risk assessment of the clinical pipeline identifies several critical vulnerability vectors inherent to long-term drug development cycles. Chief among these risks are Phase III clinical trial failures, shifting FDA regulatory guidelines, and potential patent expirations on blockbuster drug assets. Implementing a robust risk mitigation framework is essential, combining early trial auditing and patent filings."
        }
    },
    "energy": {
        "name": "Energy Systems & Smart Grid Infrastructure",
        "template": "amber",
        "cover_kpis": [
            {"label": "Grid Capacity", "val": "12.4 Gigawatts"},
            {"label": "Renewable Share", "val": "68.5% of Load"},
            {"label": "Storage Capacity", "val": "1.85 GWh"}
        ],
        "dashboard_kpis": [
            {"label": "Grid Reliability", "val": "99.999% Uptime", "change": "▲ Smart Grid Active", "status": ""},
            {"label": "Generation Cost", "val": "$42.5/MWh", "change": "▼ -12.4% Wind/Solar", "status": ""},
            {"label": "Battery Efficiency", "val": "88.4% Roundtrip", "change": "▲ Optimal Storage", "status": ""},
            {"label": "Ecosystem Status", "val": "Fully Balanced", "change": "Grid Load Stable", "status": "purple"}
        ],
        "brand_logos": [
            {"name": "GE", "type": "rect", "color": "#D97706"},
            {"name": "NEXT", "type": "diamond", "color": "#10B981"},
            {"name": "SIEM", "type": "polygon", "color": "#EF4444"}
        ],
        "swot": {
            "s": "Highly optimized renewable energy generation; stable grid load balancing.",
            "w": "High capital costs for grid-scale lithium storage battery arrays.",
            "o": "Integrating automated AI smart grids to distribute localized solar loads.",
            "t": "Sudden weather volatility spikes disrupting wind and solar resources."
        },
        "visual_svg": """
        <svg width="100%" height="80" viewBox="0 0 200 120" style="max-height: 80px; background: #FFFDF5; border-radius: 4px;">
            <line x1="100" y1="110" x2="100" y2="50" stroke="#D97706" stroke-width="3"/>
            <circle cx="100" cy="50" r="5" fill="#B45309"/>
            <line x1="100" y1="50" x2="80" y2="30" stroke="#D97706" stroke-width="2"/>
            <line x1="100" y1="50" x2="120" y2="30" stroke="#D97706" stroke-width="2"/>
            <line x1="100" y1="50" x2="100" y2="80" stroke="#D97706" stroke-width="2"/>
            <text x="100" y="20" font-family="sans-serif" font-size="8" font-weight="bold" fill="#451A03" text-anchor="middle">Grid Load Optimization</text>
        </svg>
        """,
        "timeline": [
            {"time": "Grid Decarbonization", "desc": "Integrated 800MW wind farm into local grid, displacing 600k tons CO2 annually."},
            {"time": "Smart Grid Rollout", "desc": "Completed phase 1 automated load scheduling, lowering peak consumption fees by 15%."}
        ],
        "table": {
            "headers": ["Energy Asset", "Peak Capacity", "Generation Cost", "Reliability Index"],
            "rows": [
                ["Offshore Wind", "850 Megawatts", "$38.00/MWh", "98.5% (High)"],
                ["Solar Array C", "420 Megawatts", "$42.50/MWh", "99.2% (High)"]
            ]
        },
        "charts": {
            "bar": {"title": "Annual Renewable Capacity Additions", "ylabel": "Capacity (Megawatts)"},
            "line": {"title": "Grid Load Curves vs Storage Dispatch"},
            "donut": {"title": "Generation Mix by Fuel Type"},
            "hbar": {"title": "Generator Reliability & Availability Rates"},
            "area": {"title": "Cumulative Energy Transmission Risks"}
        },
        "fallbacks": {
            "Executive Summary & Framework": "The comprehensive technical evaluation of the energy infrastructure outlines a smart-grid approach to load-balancing, renewable resource integration, and utility grid stability. To maximize generation efficiency, grid engineers must aggressively optimize transmission line loads, deploy smart grid scheduling algorithms, and minimize energy roundtrip storage losses. Ultimately, our core energy thesis posits that utility grid reliability is a function of automated load matching.",
            "Market Analysis & Sector Segmentation": "A rigorous, multi-layered structural analysis of the energy market highlights substantial modernization opportunities across solar generation fields, wind farms, and grid-scale battery systems. Current utility benchmarks suggest a significant cost-efficiency premium in grid networks utilizing smart virtual power plants (VPPs) compared to traditional coal/gas generators.",
            "Quantitative Performance & Revenue Velocity": "Analyzing the quantitative performance metrics demonstrates a correlation between renewable energy capacity scaling and compounding operational cost savings. Key performance indicators, including average cost of energy, peak transmission uptime, and battery storage capacity, showcase strong grid gains when generation resources are dynamically balanced.",
            "Operational Efficiency & Architecture": "The operational infrastructure supporting the smart grid is engineered to maximize transmission efficiency, minimize grid synchronization latencies, and ensure stable voltage levels. Modern grid networks rely on high-voltage DC lines, automated substation controllers, and decentralized energy resource management systems (DERMS).",
            "Risk Analysis, Vulnerability & Strategic Outlook": "A comprehensive risk assessment of the grid network identifies several critical vulnerability vectors. Chief among these risks are extreme weather disruptions to wind/solar fields, cybersecurity attacks targeting distribution substations, and shifting regulatory compliance standards. Implementing a robust risk mitigation framework is essential, combining diversified storage assets and real-time frequency monitors."
        }
    },
    "general": {
        "name": "Historical, Cultural & General Research Studies",
        "template": "indigo",
        "cover_kpis": [
            {"label": "Historical Span", "val": "Centuries Old"},
            {"label": "Annual Visitation", "val": "Millions Ann."},
            {"label": "Heritage Index", "val": "Global Grade"}
        ],
        "dashboard_kpis": [
            {"label": "Cultural Value", "val": "High Grade", "change": "▲ Preservation Max", "status": ""},
            {"label": "Annual Visitors", "val": "50M+ Est.", "change": "▲ +12% Growth", "status": ""},
            {"label": "Historical Age", "val": "1000+ Yrs", "change": "Continuous Heritage", "status": ""},
            {"label": "Ecosystem Health", "val": "Outstanding", "change": "Low Structural Risk", "status": "purple"}
        ],
        "brand_logos": [
            {"name": "HIST", "type": "rect", "color": "#6366F1"},
            {"name": "ARCH", "type": "diamond", "color": "#10B981"},
            {"name": "CULT", "type": "polygon", "color": "#EF4444"}
        ],
        "swot": {
            "s": "Rich historical evidence, profound cultural significance, and global heritage status.",
            "w": "Exposure to weathering, structural wear, and dense pedestrian visitor throughput.",
            "o": "Digital archiving, structural restorations, and heritage preservation initiatives.",
            "t": "Environmental pollution, structural degradation, and architectural obsolescence."
        },
        "visual_svg": """
        <svg width="100%" height="80" viewBox="0 0 200 120" style="max-height: 80px; background: #F8FAFC; border-radius: 4px;">
            <polygon points="100,20 60,60 140,60" fill="#6366F1" opacity="0.9"/>
            <rect x="70" y="60" width="60" height="40" fill="#818CF8"/>
            <rect x="90" y="80" width="20" height="20" fill="#FFFFFF"/>
            <circle cx="100" cy="45" r="4" fill="#F59E0B"/>
            <text x="100" y="115" font-family="sans-serif" font-size="8" font-weight="bold" fill="#0F172A" text-anchor="middle">Historical Heritage</text>
        </svg>
        """,
        "timeline": [
            {"time": "Archival Research", "desc": "Comprehensive digital preservation and structural audits successfully conducted."},
            {"time": "Heritage Restoration", "desc": "Long-term architectural fortification and visitor safety pipelines established."}
        ],
        "table": {
            "headers": ["Historical Era", "Reconstruction Event", "Primary Patron", "Status"],
            "rows": [
                ["18th Century", "Major Reconstruction", "Queen Ahilyabai Holkar", "Standing"],
                ["19th Century", "Gold Plating Spire", "Maharaja Ranjit Singh", "Standing"]
            ]
        },
        "charts": {
            "bar": {"title": "Annual Visitor Inflow Metrics", "ylabel": "Visitors (Millions)"},
            "line": {"title": "Structural Integrity and Restoration Over Time"},
            "donut": {"title": "Ecosystem Demographics & Visitor Segments"},
            "hbar": {"title": "Architectural Fortification Indices"},
            "area": {"title": "Cumulative Environmental Risk Profile"}
        },
        "fallbacks": {
            "Executive Summary & Framework": "The comprehensive exploration of this topic outlines a multi-dimensional perspective on historical timelines, cultural preservation, and architectural significance. Navigating these complex dynamics requires a rigorous, objective approach that respects both documented evidence and long-standing traditions. By establishing a solid analytical framework, researchers can better understand the interplay of historical events and cultural impacts, securing a comprehensive foundation for future scholarship.",
            "Market Analysis & Sector Segmentation": "A detailed structural analysis of the historical and cultural landscape reveals key evolutionary phases shaped by societal changes, leadership eras, and architectural developments. Comparing different periods provides deep insights into how structures and traditions have adapted over time. Understanding these shifts requires examining archaeological records, archival documentations, and architectural achievements.",
            "Quantitative Performance & Revenue Velocity": "Evaluating historical data and modern metrics demonstrates the profound long-term impact of heritage sites on cultural identity and local ecosystems. Key indicators, including preservation indices, visitor flow rates, and educational programs, show high levels of engagement and value retention. This long-term durability is supported by robust restoration practices and continuous community support.",
            "Operational Efficiency & Architecture": "The physical and operational architecture supporting this historical subject focuses on structural preservation, public accessibility, and environmental protection. Managing high-density visitations requires sophisticated coordination mechanisms, combining robust crowd routing systems, digital ticketing, and structural safety monitors to ensure long-term stability and protection.",
            "Risk Analysis, Vulnerability & Strategic Outlook": "A comprehensive risk assessment of this cultural asset identifies several critical vulnerability vectors. Chief among these risks are weathering, structural fatigue, and balancing high visitation rates with active conservation efforts. Implementing a robust preservation strategy is essential for mitigating these threats, combining state-of-the-art structural restoration with continuous environmental monitoring."
        }
    }
}

def detect_domain(topic: str) -> str:
    """
    Scans the topic text against domain-specific keywords.
    Returns: string key corresponding to one of the 15 DOMAIN_REGISTRY keys.
    """
    t_lower = topic.lower()
    
    # Precise keyword rules mapping to domains
    rules = [
        ("options", ["option", "condor", "spread", "derivative", "trading", "volatility", "greek", "delta", "gamma", "theta", "vega"]),
        ("equity", ["stock", "equity", "share", "aapl", "tsla", "msft", "valuation", "earnings", "fcf", "dividend"]),
        ("vc", ["startup", "venture", "funding", "vc", "founder", "ecosystem", "chennai", "seed", "round"]),
        ("ml", ["ai", "machine learning", "deep learning", "model", "llm", "quantization", "gpu", "inference", "neural", "transformer", "attention"]),
        ("crypto", ["crypto", "bitcoin", "ethereum", "blockchain", "token", "solana", "defi", "web3", "nft", "smart contract", "ledger"]),
        ("macro", ["macro", "economy", "inflation", "interest rate", "gdp", "recession", "monetary", "fiscal", "fed", "central bank"]),
        ("healthcare", ["healthcare", "hospital", "patient", "medical", "clinic", "telehealth", "diagnostics", "care"]),
        ("cybersecurity", ["cyber", "security", "threat", "hack", "penetration", "exploit", "encryption", "firewall", "malware", "vulnerability"]),
        ("esg", ["climate", "esg", "sustainability", "carbon", "green", "renewable", "solar", "wind", "ecological", "offset"]),
        ("realestate", ["real estate", "property", "housing", "mortgage", "reit", "commercial property", "residential", "cap rate"]),
        ("manufacturing", ["manufacturing", "factory", "industrial", "production line", "machinery", "automation", "oee", "plant"]),
        ("supplychain", ["supply chain", "logistics", "shipping", "freight", "warehouse", "inventory", "procurement", "distribution"]),
        ("pharma", ["pharma", "clinical trial", "drug", "fda", "biotech", "vaccine", "pathogen", "molecular"]),
        ("energy", ["energy", "power grid", "utilities", "electricity", "solar panel", "wind turbine", "oil", "gas", "nuclear", "hydroelectric"]),
        ("general", ["temple", "church", "mosque", "sacred", "historic", "cultural", "religion", "art", "music", "philosophy", "tourism", "ancient", "rebuilding", "restoration"])
    ]
    
    for domain_key, keywords in rules:
        if any(k in t_lower for k in keywords):
            return domain_key
            
    return "general"
