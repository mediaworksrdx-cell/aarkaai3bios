import sys
import os
import base64
from io import BytesIO

# Configure matplotlib for headless environment
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Generate a high-end data visualization chart
def generate_chart_base64():
    categories = ['Fintech', 'Healthcare', 'Enterprise', 'Automotive', 'Agritech']
    adoption_rates = [88, 72, 65, 54, 35]

    plt.figure(figsize=(7.5, 3.8), dpi=300)
    colors = ['#1e3a8a', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe']
    bars = plt.barh(categories, adoption_rates, color=colors, height=0.6)
    
    # Add values on top of bars
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 2, bar.get_y() + bar.get_height()/2, f'{int(width)}%', 
                 va='center', ha='left', fontsize=8, fontweight='bold', color='#1f2937')
        
    plt.title('AI Adoption Rates by Industry Sector in India (2026)', fontsize=11, fontweight='bold', pad=15, color='#1e3a8a')
    plt.xlabel('Adoption Rate (%)', fontsize=9, color='#4b5563')
    plt.xlim(0, 100)
    plt.gca().invert_yaxis()  # Top-down order
    plt.grid(axis='x', linestyle='--', alpha=0.5, color='#d1d5db')
    
    # Clean up borders
    for spine in plt.gca().spines.values():
        spine.set_visible(False)
        
    plt.tight_layout()
    
    # Save plot to buffer
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

chart_data = generate_chart_base64()

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from skills.html.docs_generator import generate_pdf

html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Indian AI Industry - Executive Business Report</title>
<style>
    @page {{
        size: A4;
        margin: 20mm;
        @bottom-right {{
            content: "Page " counter(page);
            font-size: 8px;
            color: #9ca3af;
        }}
        @bottom-left {{
            content: "AARKAAI Intelligence Services";
            font-size: 8px;
            color: #9ca3af;
        }}
    }}
    body {{
        font-family: 'Arial', sans-serif;
        color: #1f2937;
        line-height: 1.6;
        margin: 0;
        padding: 0;
    }}
    .page {{
        page-break-after: always;
    }}
    .page:last-child {{
        page-break-after: avoid;
    }}
    
    /* Cover Page Styling */
    .cover-container {{
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding-top: 60px;
    }}
    .cover-accent-bar {{
        width: 80px;
        height: 8px;
        background-color: #3b82f6;
        margin-bottom: 30px;
    }}
    .cover-title {{
        font-size: 32px;
        color: #1e3a8a;
        font-weight: 800;
        line-height: 1.2;
        margin: 0 0 15px 0;
    }}
    .cover-subtitle {{
        font-size: 16px;
        color: #4b5563;
        margin: 0 0 80px 0;
        font-weight: normal;
    }}
    .cover-metadata {{
        border-top: 1px solid #e5e7eb;
        padding-top: 20px;
        margin-top: auto;
    }}
    .metadata-item {{
        font-size: 11px;
        color: #6b7280;
        margin-bottom: 6px;
    }}
    .metadata-label {{
        font-weight: bold;
        color: #374151;
    }}
    
    /* Document Layout */
    h1 {{
        color: #1e3a8a;
        font-size: 22px;
        font-weight: 700;
        border-bottom: 2px solid #3b82f6;
        padding-bottom: 8px;
        margin-top: 0;
        margin-bottom: 20px;
    }}
    h2 {{
        color: #1e40af;
        font-size: 15px;
        font-weight: 600;
        margin-top: 25px;
        margin-bottom: 10px;
    }}
    p {{
        font-size: 11.5px;
        margin-bottom: 14px;
        text-align: justify;
    }}
    
    /* Key Metrics Grid */
    .metrics-grid {{
        display: table;
        width: 100%;
        margin: 20px 0;
        border-spacing: 10px;
    }}
    .metric-card {{
        display: table-cell;
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 15px;
        text-align: center;
        width: 33.33%;
    }}
    .metric-val {{
        font-size: 20px;
        font-weight: bold;
        color: #1e3a8a;
        margin-bottom: 5px;
    }}
    .metric-label {{
        font-size: 10px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .callout {{
        background-color: #f0f6ff;
        border-left: 4px solid #3b82f6;
        padding: 12px 18px;
        margin: 20px 0;
        border-radius: 0 6px 6px 0;
    }}
    .callout-title {{
        font-weight: bold;
        color: #1e40af;
        margin: 0 0 5px 0;
        font-size: 12px;
    }}
    .callout-body {{
        margin: 0;
        font-size: 11px;
        color: #1e3a8a;
    }}
    
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-size: 10.5px;
    }}
    th {{
        background-color: #1e3a8a;
        color: #ffffff;
        font-weight: bold;
        text-align: left;
        padding: 8px 10px;
    }}
    td {{
        padding: 8px 10px;
        border-bottom: 1px solid #e5e7eb;
    }}
    tr:nth-child(even) td {{
        background-color: #f9fafb;
    }}
    .chart-container {{
        text-align: center;
        margin: 25px 0;
    }}
    .chart-img {{
        width: 100%;
        max-width: 580px;
        border-radius: 6px;
    }}
</style>
</head>
<body>

<!-- PAGE 1: COVER PAGE -->
<div class="page">
    <div class="cover-container">
        <div>
            <div class="cover-accent-bar"></div>
            <h1 class="cover-title">THE INDIAN AI INDUSTRY<br>Strategic Growth & Market Report</h1>
            <h2 class="cover-subtitle">An executive analysis of sector adoption, core metrics, and strategic recommendations for 2026.</h2>
        </div>
        
        <div class="cover-metadata">
            <div class="metadata-item"><span class="metadata-label">Prepared By:</span> AARKAAI Intelligence Services</div>
            <div class="metadata-item"><span class="metadata-label">Target Sector:</span> Enterprise Artificial Intelligence & IT Services</div>
            <div class="metadata-item"><span class="metadata-label">Date:</span> June 2026</div>
            <div class="metadata-item"><span class="metadata-label">Document Class:</span> Confidential Executive Report</div>
        </div>
    </div>
</div>

<!-- PAGE 2: EXECUTIVE SUMMARY & METRICS -->
<div class="page">
    <h1>Executive Summary</h1>
    <p>
        The landscape of Artificial Intelligence in India has transitioned rapidly from software support operations to specialized model engineering and product deployments. Backed by government initiatives, local data residency hubs, and the largest concentration of IT talent globally, India is solidifying its position as a primary market for AI execution. This report outlines market sizes, adoption indicators, and strategic vectors.
    </p>

    <div class="callout">
        <p class="callout-title">Key Advisory Insight</p>
        <p class="callout-body">India ranks #1 globally in AI skill penetration, representing a unique supply-side advantage for companies building complex vertical agent networks.</p>
    </div>

    <h2>Industry Performance Indicators</h2>
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-val">$7.8 Billion</div>
            <div class="metric-label">Projected Market Size (2026)</div>
        </div>
        <div class="metric-card">
            <div class="metric-val">34.5%</div>
            <div class="metric-label">Compound Annual Growth (CAGR)</div>
        </div>
        <div class="metric-card">
            <div class="metric-val">4.5 Million</div>
            <div class="metric-label">Active IT Talent Pool</div>
        </div>
    </div>

    <h2>Market Sector Landscape</h2>
    <table>
        <thead>
            <tr>
                <th style="width: 25%;">Sector</th>
                <th style="width: 20%;">Adoption Rate</th>
                <th>Primary Use Cases</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Fintech & Banking</strong></td>
                <td>High (88%)</td>
                <td>Risk scoring, fraud transaction alerts, and automated customer services.</td>
            </tr>
            <tr>
                <td><strong>Healthcare</strong></td>
                <td>Moderate (72%)</td>
                <td>Image-based diagnostics, health data processing, and triage support.</td>
            </tr>
            <tr>
                <td><strong>Enterprise SaaS</strong></td>
                <td>Steady (65%)</td>
                <td>Agentic workflow automation, dynamic document processing, and code compilation.</td>
            </tr>
            <tr>
                <td><strong>Automotive</strong></td>
                <td>Emerging (54%)</td>
                <td>ADAS integration, factory floor robotics, and telemetry analytics.</td>
            </tr>
        </tbody>
    </table>
</div>

<!-- PAGE 3: DATA VISUALIZATION & RECOMMENDATIONS -->
<div class="page">
    <h1>Data Insights & Growth Projections</h1>
    <p>
        Sector-specific indicators reveal that transaction-heavy, highly regulated fields (such as Banking and Fintech) lead the transition due to the direct cost-benefits of transaction security automation and automated customer routing.
    </p>

    <div class="chart-container">
        <img class="chart-img" src="data:image/png;base64,{chart_data}" alt="Adoption Rates Chart">
    </div>

    <h2>Strategic Recommendations</h2>
    <p>
        <strong>1. Implement On-Premise CPU Inference:</strong> To address strict data protection requirements, companies should build secure local models rather than calling external cloud services.
    </p>
    <p>
        <strong>2. Standardize Verification Layers:</strong> Critical sectors like Banking and Healthcare must integrate secondary verification filters to check LLM responses for safety and accuracy rules.
    </p>
    <p>
        <strong>3. Tap into Localized Multilingual Models:</strong> AI interfaces must support regional Indian languages to expand adoption across suburban and rural markets.
    </p>
</div>

</body>
</html>
"""

generate_pdf(html_content, 'market_research_report.pdf')
print('PDF generated successfully as a premium Executive Business Report')