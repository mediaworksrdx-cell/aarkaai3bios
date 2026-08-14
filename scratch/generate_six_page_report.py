import sys
import os
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Insert workspace root to import the generator skill
workspace_root = os.path.abspath(os.path.dirname(__file__) + "/..")
sys.path.insert(0, workspace_root)
from skills.html.docs_generator import generate_pdf

# Set custom styling for a premium look
def apply_chart_style():
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans']
    plt.rcParams['text.color'] = '#1e293b'
    plt.rcParams['axes.labelcolor'] = '#475569'
    plt.rcParams['xtick.color'] = '#64748b'
    plt.rcParams['ytick.color'] = '#64748b'

# Helper to generate base64 chart
def get_chart_base64(fig):
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=180, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

# Chart 1: Global AI Market Size Growth
def gen_market_chart():
    apply_chart_style()
    fig, ax = plt.subplots(figsize=(6, 2.8))
    years = ['2022', '2023', '2024', '2025', '2026']
    market_size = [136.5, 196.4, 298.2, 450.8, 675.2]
    ax.bar(years, market_size, color=['#3b82f6', '#2563eb', '#1d4ed8', '#1e40af', '#1e3a8a'], width=0.55, zorder=3)
    ax.set_title("Global AI Market Size Growth ($ Billion)", fontsize=10, fontweight='bold', color='#1e3a8a', pad=12)
    ax.set_ylabel("Market Size in $B", fontsize=8)
    ax.grid(axis='y', linestyle='--', alpha=0.4, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    return get_chart_base64(fig)

# Chart 2: Venture Capital Funding Trends
def gen_funding_chart():
    apply_chart_style()
    fig, ax = plt.subplots(figsize=(6, 2.8))
    quarters = ['Q1-25', 'Q2-25', 'Q3-25', 'Q4-25', 'Q1-26', 'Q2-26']
    funding = [12.4, 15.8, 18.2, 22.5, 26.1, 31.4]
    ax.plot(quarters, funding, marker='o', color='#10b981', linewidth=2.5, markersize=6, zorder=3)
    ax.fill_between(quarters, funding, color='#d1fae5', alpha=0.5, zorder=2)
    ax.set_title("AI Venture Capital Quarterly Funding ($ Billion)", fontsize=10, fontweight='bold', color='#065f46', pad=12)
    ax.set_ylabel("Funding in $B", fontsize=8)
    ax.grid(True, linestyle='--', alpha=0.4, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    return get_chart_base64(fig)

# Chart 3: AI Investment by Region
def gen_region_chart():
    apply_chart_style()
    fig, ax = plt.subplots(figsize=(6, 2.8))
    regions = ['North America', 'Asia-Pacific', 'Europe', 'Latin America', 'ME&A']
    investments = [45.2, 38.6, 22.4, 8.5, 5.3]
    ax.barh(regions, investments, color=['#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe', '#ede9fe'], height=0.55, zorder=3)
    ax.set_title("AI Regional Investment Distribution 2026 ($ Billion)", fontsize=10, fontweight='bold', color='#5b21b6', pad=12)
    ax.set_xlabel("Investment in $B", fontsize=8)
    ax.grid(axis='x', linestyle='--', alpha=0.4, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    return get_chart_base64(fig)

# Chart 4: AI Applications Breakdown
def gen_apps_chart():
    apply_chart_style()
    fig, ax = plt.subplots(figsize=(6, 2.8))
    labels = ['Natural Language', 'Computer Vision', 'Robotics', 'Predictive Analytics']
    shares = [40, 25, 20, 15]
    colors = ['#f59e0b', '#fbbf24', '#fcd34d', '#fef3c7']
    ax.pie(shares, labels=labels, autopct='%1.0f%%', startangle=90, colors=colors, 
           textprops={'fontsize': 8, 'weight': 'bold'}, wedgeprops={'edgecolor': 'white', 'linewidth': 1})
    ax.set_title("Enterprise AI Application Share 2026", fontsize=10, fontweight='bold', color='#b45309', pad=12)
    plt.tight_layout()
    return get_chart_base64(fig)

# Chart 5: Generative AI Adoption Rate
def gen_adoption_chart():
    apply_chart_style()
    fig, ax = plt.subplots(figsize=(6, 2.8))
    sectors = ['Tech', 'Finance', 'Healthcare', 'EdTech', 'Manufacturing']
    adoption = [85, 68, 52, 44, 35]
    ax.bar(sectors, adoption, color='#ef4444', width=0.5, zorder=3)
    ax.set_title("Generative AI Enterprise Adoption Rate (%)", fontsize=10, fontweight='bold', color='#991b1b', pad=12)
    ax.set_ylabel("Adoption Rate (%)", fontsize=8)
    ax.grid(axis='y', linestyle='--', alpha=0.4, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    return get_chart_base64(fig)

# Generate chart images
chart1 = gen_market_chart()
chart2 = gen_funding_chart()
chart3 = gen_region_chart()
chart4 = gen_apps_chart()
chart5 = gen_adoption_chart()

# Assemble premium 6-page HTML content
html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Global Artificial Intelligence Industry Report 2026</title>
<style>
    @page {{
        size: A4;
        margin: 18mm;
    }}
    body {{
        font-family: Arial, sans-serif;
        color: #1e293b;
        line-height: 1.6;
        font-size: 11.5px;
        margin: 0;
        padding: 0;
    }}
    .page {{
        height: 255mm; /* Max content height within printable bounds */
        page-break-after: always;
        box-sizing: border-box;
        position: relative;
    }}
    .page:last-child {{
        page-break-after: avoid;
    }}
    h1 {{
        font-size: 26px;
        color: #1e3a8a;
        margin-bottom: 5px;
        font-weight: bold;
    }}
    h2 {{
        font-size: 18px;
        color: #1e3a8a;
        border-bottom: 2px solid #3b82f6;
        padding-bottom: 6px;
        margin-top: 0;
        margin-bottom: 12px;
    }}
    p {{
        margin-bottom: 12px;
        text-align: justify;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 10.5px;
    }}
    th {{
        background: #1e3a8a;
        color: white;
        padding: 8px 10px;
        text-align: left;
        font-weight: bold;
    }}
    td {{
        padding: 7px 10px;
        border-bottom: 1px solid #e2e8f0;
    }}
    tr:nth-child(even) td {{
        background: #f8fafc;
    }}
    .chart-container {{
        text-align: center;
        margin: 15px 0;
    }}
    .chart-container img {{
        max-width: 85%;
        height: auto;
    }}
    .metadata {{
        font-size: 12px;
        color: #64748b;
        margin-top: 10px;
        border-top: 1px solid #e2e8f0;
        padding-top: 10px;
    }}
    .callout {{
        background: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 12px 16px;
        margin: 12px 0;
        font-size: 11px;
        color: #1e40af;
    }}
</style>
</head>
<body>

<!-- PAGE 1: Cover Page with Watermark -->
<div class="page">
    <!-- Centered Watermark overlay -->
    <div style="
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(-45deg);
        font-size: 70px;
        font-weight: bold;
        color: rgba(226, 232, 240, 0.55);
        z-index: 0;
        pointer-events: none;
        white-space: nowrap;
    ">
        CONFIDENTIAL
    </div>
    
    <div style="position: relative; z-index: 1; padding-top: 40mm; text-align: center;">
        <div style="font-size: 14px; font-weight: bold; color: #3b82f6; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 15px;">Industry Intelligence Report</div>
        <h1>Global Artificial Intelligence<br>Industry Report 2026</h1>
        <div style="font-size: 16px; color: #475569; margin-top: 15px; margin-bottom: 40px; font-style: italic;">Ecosystem Growth, Funding Trends, Regional Landscape, and Enterprise Adoption Dynamics</div>
        
        <div style="max-width: 500px; margin: 0 auto; text-align: justify; border-top: 2px solid #1e3a8a; border-bottom: 2px solid #1e3a8a; padding: 20px 0;">
            <p style="margin: 0; font-size: 11.5px; line-height: 1.7; color: #334155;">
                <strong>Executive Abstract:</strong> This comprehensive study analyzes the transformative evolution of the global artificial intelligence sector through the mid-2020s. We explore how generative AI has transitioned from experimental applications to enterprise-grade integrations, driving productivity gains across high-value verticals. By examining venture capital flows, regional competitiveness, application breakdowns, and sector-specific adoption curves, this document serves as a strategic roadmap for enterprises navigating the next wave of cognitive computing infrastructure and market disruption.
            </p>
        </div>
        
        <div class="metadata" style="margin-top: 50mm; font-size: 11px;">
            <strong>Prepared by:</strong> Synthetix Analytics Research Division &bull; <strong>Date:</strong> June 2026 &bull; <strong>Document ID:</strong> SA-AI-2026-06
        </div>
    </div>
</div>

<!-- PAGE 2: Executive Summary & Global Market Landscape -->
<div class="page">
    <h2>1. Executive Summary &amp; Market Landscape</h2>
    <p>
        The global artificial intelligence industry has reached an unprecedented inflection point in 2026. Over the past four years, the market has expanded at a compound annual growth rate (CAGR) exceeding 35%, driven by structural investments in specialized semiconductor hardware, scalable foundational models, and robust cloud infrastructure. Enterprises have shifted their focus from preliminary exploratory pilots to complex, multi-agent automated production deployments that yield tangible returns on investment.
    </p>
    <p>
        This rapid scaling is underpinned by the continuous optimization of large language models and multimodal perception networks, which have dramatically reduced the cost per token query. As open-source architectures achieve competitive parity with proprietary platforms, businesses are increasingly developing custom domain-specific models to protect proprietary IP and secure data privacy.
    </p>
    
    <div class="chart-container">
        <img src="data:image/png;base64,{chart1}" alt="Global AI Market Size Growth" />
    </div>

    <table>
        <thead>
            <tr>
                <th>Fiscal Year</th>
                <th>Global Market Size ($B)</th>
                <th>Year-over-Year Growth (%)</th>
                <th>Key Driving Factor</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>2022</td>
                <td>136.5</td>
                <td>28.4%</td>
                <td>Initial foundation model breakthroughs</td>
            </tr>
            <tr>
                <td>2023</td>
                <td>196.4</td>
                <td>43.9%</td>
                <td>Generative AI public awareness &amp; pilot starts</td>
            </tr>
            <tr>
                <td>2024</td>
                <td>298.2</td>
                <td>51.8%</td>
                <td>GPU hardware scaling &amp; cloud API expansions</td>
            </tr>
            <tr>
                <td>2025</td>
                <td>450.8</td>
                <td>51.2%</td>
                <td>Enterprise workflows transition to production</td>
            </tr>
            <tr>
                <td>2026 (Est.)</td>
                <td>675.2</td>
                <td>49.8%</td>
                <td>Autonomous agentic systems and local edge AI</td>
            </tr>
        </tbody>
    </table>
</div>

<!-- PAGE 3: Venture Capital & Funding Trends -->
<div class="page">
    <h2>2. Venture Capital &amp; Funding Trends</h2>
    <p>
        Venture capital investments in the artificial intelligence domain have remained exceptionally resilient despite broader macroeconomic headwinds. Institutional investors, sovereign wealth funds, and corporate venture arms have concentrated capital toward specialized foundation model builders, AI safety infrastructure, and sector-specific SaaS layers. The quarterly funding volume has steadily escalated, reflecting high investor confidence in cognitive tech.
    </p>
    <p>
        A notable trend in late 2025 and early 2026 is the surge in "mega-rounds" exceeding $500 million, alongside strategic joint ventures between hyperscalers and top-tier research laboratories. M&amp;A activity has also accelerated as legacy technology providers acquire agile AI startups to consolidate their technical capability and secure highly sought-after engineering talent.
    </p>
    
    <div class="chart-container">
        <img src="data:image/png;base64,{chart2}" alt="AI Venture Capital Quarterly Funding" />
    </div>

    <table>
        <thead>
            <tr>
                <th>Quarter</th>
                <th>Total VC Funding ($B)</th>
                <th>Deals Closed</th>
                <th>Average Deal Size ($M)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Q1-25</td>
                <td>12.4</td>
                <td>340</td>
                <td>36.5</td>
            </tr>
            <tr>
                <td>Q2-25</td>
                <td>15.8</td>
                <td>385</td>
                <td>41.0</td>
            </tr>
            <tr>
                <td>Q3-25</td>
                <td>18.2</td>
                <td>412</td>
                <td>44.2</td>
            </tr>
            <tr>
                <td>Q4-25</td>
                <td>22.5</td>
                <td>450</td>
                <td>50.0</td>
            </tr>
            <tr>
                <td>Q1-26</td>
                <td>26.1</td>
                <td>485</td>
                <td>53.8</td>
            </tr>
            <tr>
                <td>Q2-26 (Proj.)</td>
                <td>31.4</td>
                <td>520</td>
                <td>60.4</td>
            </tr>
        </tbody>
    </table>
</div>

<!-- PAGE 4: Regional Analysis & National Investments -->
<div class="page">
    <h2>3. Regional Analysis &amp; National Investments</h2>
    <p>
        The geopolitical race for artificial intelligence supremacy has intensified, with national governments enacting targeted funding programs, regulatory sandboxes, and sovereign cloud mandates. North America, driven by Silicon Valley's research clusters and massive capital markets, continues to lead in absolute funding. However, the Asia-Pacific region is experiencing the fastest acceleration, led by robust industrial automation demand and substantial public-private partnerships.
    </p>
    <p>
        European nations are carving out a distinct niche focused on trustworthy AI, ethical compliance, and high-precision industrial robotics, aligning with the comprehensive implementation of local regulatory frameworks. Concurrently, emerging digital hubs in India, Latin America, and the Middle East are leveraging AI to leapfrog legacy software infrastructure, developing localized systems designed for high-density mobile populations.
    </p>
    
    <div class="chart-container">
        <img src="data:image/png;base64,{chart3}" alt="AI Regional Investment Distribution" />
    </div>

    <table>
        <thead>
            <tr>
                <th>Geographic Region</th>
                <th>Capital Invested ($B)</th>
                <th>Active AI Patents (2025)</th>
                <th>Regulatory Focus</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>North America</td>
                <td>45.2</td>
                <td>145,000</td>
                <td>Innovation-first, voluntary safety agreements</td>
            </tr>
            <tr>
                <td>Asia-Pacific</td>
                <td>38.6</td>
                <td>162,000</td>
                <td>Industrial automation and local ecosystem subsidies</td>
            </tr>
            <tr>
                <td>Europe</td>
                <td>22.4</td>
                <td>68,000</td>
                <td>Strict compliance, data privacy, and ethical standards</td>
            </tr>
            <tr>
                <td>Latin America</td>
                <td>8.5</td>
                <td>15,000</td>
                <td>Socio-economic inclusion, fintech integrations</td>
            </tr>
            <tr>
                <td>Middle East &amp; Africa</td>
                <td>5.3</td>
                <td>12,000</td>
                <td>Sovereign cloud infrastructure, smart city platforms</td>
            </tr>
        </tbody>
    </table>
</div>

<!-- PAGE 5: Industry Applications & Use Cases -->
<div class="page">
    <h2>4. Industry Applications &amp; Use Cases</h2>
    <p>
        The deployment of artificial intelligence is no longer restricted to tech-first enterprises. Natural Language Processing (NLP) remains the largest segment, driven by customer support automation, real-time multilingual translation, and document synthesis. Computer Vision has achieved deep penetration in autonomous vehicles, retail automation, and automated medical diagnostics, where imaging algorithms assist clinical teams in identifying anomalies.
    </p>
    <p>
        Predictive Analytics systems are heavily utilized in algorithmic trading, supply chain forecasting, and predictive maintenance protocols in heavy manufacturing. Meanwhile, generative engineering and robotics are emerging as high-growth segments, enabling automated software development, rapid digital design, and intelligent robotic process control.
    </p>
    
    <div class="chart-container">
        <img src="data:image/png;base64,{chart4}" alt="Enterprise AI Application Share" />
    </div>

    <table>
        <thead>
            <tr>
                <th>Segment Name</th>
                <th>Primary Use Case</th>
                <th>Adoption Driver</th>
                <th>Productivity Yield</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Natural Language</td>
                <td>Automated customer support, text summarization</td>
                <td>Cost reduction and 24/7 service availability</td>
                <td>35% - 40% efficiency gains</td>
            </tr>
            <tr>
                <td>Computer Vision</td>
                <td>Defect detection, medical imaging, surveillance</td>
                <td>High precision, error reduction over human teams</td>
                <td>25% fewer defect escapes</td>
            </tr>
            <tr>
                <td>Robotics</td>
                <td>Autonomous warehouse logistics, mechanical assembly</td>
                <td>Labor shortages, physical safety optimization</td>
                <td>30% faster cycle times</td>
            </tr>
            <tr>
                <td>Predictive Analytics</td>
                <td>Demand forecasting, financial risk modeling</td>
                <td>Data-driven decision making, inventory optimization</td>
                <td>18% inventory cost reduction</td>
            </tr>
        </tbody>
    </table>
</div>

<!-- PAGE 6: Future Outlook, Generative AI Adoption, & Conclusion -->
<div class="page">
    <h2>5. Future Outlook, Generative AI Adoption, &amp; Conclusion</h2>
    <p>
        Looking ahead to the late 2020s, generative artificial intelligence will become deeply embedded in the modern corporate operating system. Sector-specific adoption curves show the Technology and Financial sectors leading in integration, with Healthcare and EdTech scaling rapidly as specialized domain models receive clinical and educational validation. Manufacturing is also rising steadily, leveraging AI to coordinate smart factory networks.
    </p>
    <p>
        In conclusion, the transition to an AI-augmented economy is accelerating. Organizations that invest in modern data pipelines, secure cloud infrastructure, and proactive workforce upskilling will build sustainable competitive advantages. Conversely, slow adopters face significant operational efficiency gaps. The future belongs to agent-driven enterprises that seamlessly coordinate human ingenuity with autonomous cognitive systems.
    </p>
    
    <div class="chart-container">
        <img src="data:image/png;base64,{chart5}" alt="Generative AI Enterprise Adoption Rate" />
    </div>

    <table>
        <thead>
            <tr>
                <th>Sector</th>
                <th>Adoption Rate (%)</th>
                <th>Primary Barrier</th>
                <th>Strategic Recommendation</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Technology</td>
                <td>85%</td>
                <td>GPU availability &amp; cost</td>
                <td>Invest in model quantization and small local models</td>
            </tr>
            <tr>
                <td>Finance</td>
                <td>68%</td>
                <td>Regulatory compliance &amp; security</td>
                <td>Deploy private sovereign cloud instances with strict compliance</td>
            </tr>
            <tr>
                <td>Healthcare</td>
                <td>52%</td>
                <td>Data privacy (HIPAA) &amp; accuracy</td>
                <td>Implement human-in-the-loop validation for clinical decisions</td>
            </tr>
            <tr>
                <td>EdTech</td>
                <td>44%</td>
                <td>Plagiarism concerns &amp; access equity</td>
                <td>Build personalized adaptive tutoring frameworks</td>
            </tr>
            <tr>
                <td>Manufacturing</td>
                <td>35%</td>
                <td>Legacy hardware integration</td>
                <td>Implement retrofitted IoT sensors for predictive telemetry</td>
            </tr>
        </tbody>
    </table>
</div>

</body>
</html>
"""

# Generate the PDF in the workspace
output_pdf_path = os.path.join(workspace_root, "premium_ai_report.pdf")
generate_pdf(html_content, output_pdf_path)
print(f"Success: PDF generated at {output_pdf_path}")
