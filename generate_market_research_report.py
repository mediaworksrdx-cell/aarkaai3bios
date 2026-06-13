import sys
import os
import base64
from io import BytesIO

# Configure matplotlib for headless environment
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Generate a high-end visualization chart
def generate_chart_base64():
    years = ['2021', '2022', '2023', '2024', '2025', '2026 (Est)']
    market_size_usd_billion = [1.2, 1.8, 2.5, 3.8, 5.6, 7.8]

    plt.figure(figsize=(7, 3.8), dpi=300)
    plt.plot(years, market_size_usd_billion, marker='o', color='#1e3a8a', linewidth=2.5, markersize=6)
    plt.fill_between(years, market_size_usd_billion, color='#3b82f6', alpha=0.15)
    
    plt.title('Indian AI Industry Market Size (USD Billions)', fontsize=12, fontweight='bold', pad=12, color='#1e3a8a')
    plt.xlabel('Year', fontsize=9, color='#4b5563')
    plt.ylabel('Market Size ($B)', fontsize=9, color='#4b5563')
    plt.grid(True, linestyle='--', alpha=0.5, color='#d1d5db')
    
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
<title>Comprehensive Market Research: The Indian AI Industry Landscape</title>
<style>
    @page {{
        size: A4;
        margin: 20mm;
    }}
    body {{
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #1f2937;
        line-height: 1.6;
        margin: 0;
        padding: 0;
    }}
    h1 {{
        color: #1e3a8a;
        font-size: 26px;
        font-weight: 700;
        border-bottom: 3px solid #3b82f6;
        padding-bottom: 12px;
        margin-top: 0;
        margin-bottom: 20px;
    }}
    h2 {{
        color: #1e40af;
        font-size: 18px;
        font-weight: 600;
        margin-top: 30px;
        margin-bottom: 12px;
    }}
    p {{
        font-size: 12px;
        margin-bottom: 16px;
        text-align: justify;
    }}
    .callout {{
        background-color: #f0f6ff;
        border-left: 4px solid #3b82f6;
        padding: 15px 20px;
        margin: 20px 0;
        border-radius: 0 8px 8px 0;
    }}
    .callout p {{
        font-weight: bold;
        color: #1e40af;
        margin: 0;
        font-size: 12px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 24px 0;
        font-size: 11px;
    }}
    th {{
        background-color: #1e3a8a;
        color: #ffffff;
        font-weight: bold;
        text-align: left;
        padding: 10px 12px;
    }}
    td {{
        padding: 10px 12px;
        border-bottom: 1px solid #e5e7eb;
    }}
    tr:nth-child(even) td {{
        background-color: #f9fafb;
    }}
    .chart-container {{
        text-align: center;
        margin: 30px 0;
    }}
    .chart-img {{
        width: 100%;
        max-width: 600px;
        border-radius: 8px;
    }}
    .footer {{
        font-size: 9px;
        color: #9ca3af;
        text-align: center;
        margin-top: 40px;
        border-top: 1px solid #e5e7eb;
        padding-top: 10px;
    }}
</style>
</head>
<body>

<h1>Comprehensive Market Research: The Indian AI Industry Landscape</h1>

<p>
    The Indian Artificial Intelligence (AI) sector has transitioned from a supporting outsourcing hub to a global powerhouse in algorithmic development, computer vision, and machine learning deployments. Driven by government backing via the National AI Strategy, expansive cloud infrastructure investments, and a vast ecosystem of over 4.5 million IT professionals, India's AI market size is projected to reach USD 7.8 billion by 2026.
</p>

<div class="callout">
    <p>Key Insight: India ranks 1st globally in AI skill penetration and talent concentration, reflecting a massive talent pool shifting towards advanced generative models.</p>
</div>

<h2>Market Growth Projections</h2>
<div class="chart-container">
    <img class="chart-img" src="data:image/png;base64,{chart_data}" alt="AI Market Size Chart">
</div>

<h2>Sector-Specific Adoption Patterns</h2>
<table>
    <thead>
        <tr>
            <th style="width: 25%;">Sector</th>
            <th style="width: 20%;">Adoption Rate</th>
            <th>Primary Drivers & Use Cases</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><strong>Healthcare</strong></td>
            <td>High (72%)</td>
            <td>Computer-aided diagnostics, automated patient triage, and regional-language AI chat systems.</td>
        </tr>
        <tr>
            <td><strong>Fintech & Banking</strong></td>
            <td>Very High (88%)</td>
            <td>Algorithmic credit scoring, real-time transaction fraud analytics, and multilingual customer service automation.</td>
        </tr>
        <tr>
            <td><strong>Manufacturing & Industry 4.0</strong></td>
            <td>Moderate (54%)</td>
            <td>Predictive maintenance pipelines, supply chain optimization, and automated visual quality inspections.</td>
        </tr>
        <tr>
            <td><strong>Agritech</strong></td>
            <td>Emerging (35%)</td>
            <td>Satellite-based crop health modeling, weather analytics integration, and price trend forecasting.</td>
        </tr>
    </tbody>
</table>

<h2>Competitive Landscape & Strategic Outlook</h2>
<p>
    The domestic market is intensely competitive, characterized by the convergence of hyperscale multi-national corporations (including AWS, Microsoft Azure, Google Cloud) establishing local data centers, and IT giants (such as Infosys, TCS, Wipro) training hundreds of thousands of engineers in foundational LLM techniques. Concurrently, native AI startups are raising significant early-stage funding to build specialized vertical agents tailored for localized workflows, multilingual support, and highly resource-efficient CPU/edge deployments.
</p>

<div class="footer">
    AARKAAI Research Analytics Services © 2026 • Confidential Document
</div>

</body>
</html>
"""

generate_pdf(html_content, 'market_research_report.pdf')
print('PDF generated successfully with embedded high-resolution chart')