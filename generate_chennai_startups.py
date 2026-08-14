import sys
import os
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Custom chart styling for premium look
def apply_chart_style():
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans']
    plt.rcParams['text.color'] = '#1e293b'
    plt.rcParams['axes.labelcolor'] = '#475569'
    plt.rcParams['xtick.color'] = '#64748b'
    plt.rcParams['ytick.color'] = '#64748b'

# Helpers to generate base64 charts
def get_tech_chart():
    apply_chart_style()
    fig, ax = plt.subplots(figsize=(6, 3), dpi=180)
    years = ['2022', '2023', '2024', '2025', '2026']
    startups = [240, 310, 420, 580, 750]
    ax.bar(years, startups, color=['#3b82f6', '#2563eb', '#1d4ed8', '#1e40af', '#1e3a8a'], width=0.6, zorder=3)
    ax.set_title("Tech Startup Growth in Chennai", fontsize=10, fontweight='bold', color='#1e3a8a', pad=12)
    ax.set_ylabel("Number of Active Startups", fontsize=8)
    ax.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def get_sustain_chart():
    apply_chart_style()
    fig, ax = plt.subplots(figsize=(6, 3), dpi=180)
    labels = ['Green Energy', 'Eco-Packaging', 'Waste Mgmt', 'Water Purification']
    shares = [35, 25, 20, 20]
    colors = ['#10b981', '#34d399', '#6ee7b7', '#a7f3d0']
    ax.pie(shares, labels=labels, autopct='%1.0f%%', startangle=90, colors=colors, 
           textprops={'fontsize': 8, 'weight': 'bold'}, wedgeprops={'edgecolor': 'white', 'linewidth': 1})
    ax.set_title("Chennai Sustainable Market Demand Breakdown", fontsize=10, fontweight='bold', color='#065f46', pad=12)
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def get_health_chart():
    apply_chart_style()
    fig, ax = plt.subplots(figsize=(6, 3), dpi=180)
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    users = [10, 25, 45, 75, 110, 160]
    ax.plot(months, users, marker='o', color='#ef4444', linewidth=2.5, markersize=6, zorder=3)
    ax.fill_between(months, users, color='#fee2e2', alpha=0.5, zorder=2)
    ax.set_title("Telehealth App Adoption Rate (Chennai Users in Thousands)", fontsize=10, fontweight='bold', color='#991b1b', pad=12)
    ax.grid(True, linestyle='--', alpha=0.5, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def get_edtech_chart():
    apply_chart_style()
    fig, ax = plt.subplots(figsize=(6, 3), dpi=180)
    categories = ['K-12', 'Upskilling', 'Language', 'Vocational']
    revenues = [4.5, 6.2, 2.8, 1.9]
    ax.barh(categories, revenues, color='#8b5cf6', height=0.5, zorder=3)
    ax.set_title("Chennai EdTech Segment Revenue Forecast ($M)", fontsize=10, fontweight='bold', color='#5b21b6', pad=12)
    ax.grid(axis='x', linestyle='--', alpha=0.5, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def get_invest_chart():
    apply_chart_style()
    fig, ax = plt.subplots(figsize=(6, 3), dpi=180)
    sectors = ['Tech', 'Green', 'Health', 'EdTech']
    investments = [120, 85, 95, 60]
    ax.bar(sectors, investments, color='#f59e0b', width=0.5, zorder=3)
    ax.set_title("Expected Venture Capital Investment (₹ Crores)", fontsize=10, fontweight='bold', color='#b45309', pad=12)
    ax.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

# Render all charts
chart_tech = get_tech_chart()
chart_sustain = get_sustain_chart()
chart_health = get_health_chart()
chart_edtech = get_edtech_chart()
chart_invest = get_invest_chart()

# HTML Assembly
html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{
        size: A4;
        margin: 20mm;
    }}
    body {{
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #334155;
        line-height: 1.6;
        font-size: 11.5px;
    }}
    h1 {{
        color: #1e3a8a;
        font-size: 24px;
        font-weight: 800;
        margin-bottom: 20px;
    }}
    h2 {{
        color: #1e3a8a;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 6px;
        margin-top: 0;
        font-size: 16px;
        font-weight: 700;
    }}
    p {{
        margin-bottom: 14px;
        text-align: justify;
    }}
    .page {{
        page-break-after: always;
        height: 257mm; /* Adjust for printable area with 20mm margins */
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }}
    .page:last-child {{
        page-break-after: avoid;
    }}
    .watermark {{
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(-45deg);
        font-size: 72px;
        font-weight: 900;
        color: rgba(226, 232, 240, 0.35);
        z-index: 0;
        pointer-events: none;
        white-space: nowrap;
    }}
    .chart-container {{
        text-align: center;
        margin-top: 15px;
    }}
    .chart-img {{
        max-width: 100%;
        height: auto;
        border: 1px solid #f1f5f9;
        border-radius: 8px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        font-size: 10.5px;
    }}
    th {{
        background: #1e3a8a;
        color: white;
        padding: 6px 10px;
        text-align: left;
    }}
    td {{
        padding: 6px 10px;
        border-bottom: 1px solid #e2e8f0;
    }}
    tr:nth-child(even) td {{
        background: #f8fafc;
    }}
    .callout {{
        background: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 10px 14px;
        margin: 10px 0;
        border-radius: 0 8px 8px 0;
        font-style: italic;
    }}
</style>
</head>
<body>

<!-- PAGE 1: COVER PAGE -->
<div class="page" style="position: relative; justify-content: center; text-align: center;">
    <div class="watermark">CONFIDENTIAL</div>
    <div style="position: relative; z-index: 1;">
        <h1 style="font-size: 32px; margin-bottom: 10px; color: #1e3a8a;">Business Ideas for Startups in Chennai</h1>
        <p style="font-size: 14px; text-align: center; color: #64748b; margin-bottom: 40px;">An In-depth Strategic Analysis of Growth Sectors</p>
        <div style="width: 80px; height: 4px; background: #3b82f6; margin: 0 auto 40px;"></div>
        <p style="max-width: 500px; margin: 0 auto; line-height: 1.8; color: #334155;">
            Chennai, the capital of Tamil Nadu, is a vibrant economic hub with a rapidly evolving startup ecosystem. 
            This comprehensive report evaluates critical market opportunities across Technology, Sustainability, 
            Healthcare, and Education sectors, presenting data-driven recommendations for modern entrepreneurs.
        </p>
        <div style="margin-top: 80px; font-size: 11px; color: #94a3b8;">
            Prepared by Aarkaa AI &bull; Confidential Assessment Report &bull; June 2026
        </div>
    </div>
</div>

<!-- PAGE 2: TECHNOLOGY SECTOR -->
<div class="page">
    <h2>1. Technology & Digital Services Sector</h2>
    <p>
        Chennai's technology landscape continues to mature, bolstered by established infrastructure such as the Chennai Technology Park (CTP) and the Chennai Software Technology Park (CSTP). Emerging startups are moving beyond traditional IT outsourcing and shifting focus to high-value SaaS products, custom mobile applications, and AI-driven digital marketing automation.
    </p>
    <p>
        The availability of engineering talent from premier local institutions makes the region a prime destination for developer tools and business workflow startups. Lower operational costs compared to Bangalore and Mumbai make early bootstrapping highly efficient.
    </p>
    <div class="chart-container">
        <img class="chart-img" src="data:image/png;base64,{chart_tech}" />
    </div>
</div>

<!-- PAGE 3: SUSTAINABLE SOLUTIONS -->
<div class="page">
    <h2>2. Sustainable Solutions & Green Markets</h2>
    <p>
        Chennai's rapid urban growth has led to severe constraints on resource availability, making sustainability a lucrative frontier for startup innovation. Rising awareness among urban consumers is driving high market potential for renewable solar energy installations and eco-friendly packaging alternatives designed to eliminate single-use plastics.
    </p>
    <table style="margin-bottom: 12px;">
        <tr>
            <th>Solution Area</th>
            <th>Purpose</th>
            <th>Market Potential</th>
        </tr>
        <tr>
            <td>Green Energy Solutions</td>
            <td>Provide residential & commercial solar power options</td>
            <td>High; increasing demand in urban high-rises</td>
        </tr>
        <tr>
            <td>Eco-Friendly Packaging</td>
            <td>Biodegegradable paper and plant fiber containers</td>
            <td>Very High; spurred by legislative plastic bans</td>
        </tr>
    </table>
    <div class="chart-container">
        <img class="chart-img" src="data:image/png;base64,{chart_sustain}" />
    </div>
</div>

<!-- PAGE 4: HEALTHCARE INITIATIVES -->
<div class="page">
    <h2>3. Digital Healthcare & Telehealth Networks</h2>
    <p>
        Known historically as the healthcare capital of India, Chennai features world-class medical institutions. Startups have a unique opportunity to build specialized digital systems, remote monitoring apps, and automated diagnostic clinics that bridge the gap between rural patients and urban super-specialists.
    </p>
    <div class="callout">
        Strategic Integration: Access to Chennai's existing medical networks provides telehealth startups with a ready-made ecosystem for validation and clinical trials.
    </div>
    <div class="chart-container">
        <img class="chart-img" src="data:image/png;base64,{chart_health}" />
    </div>
</div>

<!-- PAGE 5: EDUCATION TECHNOLOGIES -->
<div class="page">
    <h2>4. Specialized EdTech & Skill Acquisition</h2>
    <p>
        Traditional school curriculums are failing to keep pace with rapid technology demands. Chennai's high literacy rates support a strong willingness from parents and students to invest in additional skill acquisition platforms. Startups focused on localized language tutoring, advanced coding academies, and job-placement vocational training are witnessing hyper-growth.
    </p>
    <div class="chart-container">
        <img class="chart-img" src="data:image/png;base64,{chart_edtech}" />
    </div>
</div>

<!-- PAGE 6: FINANCIAL INVESTMENT & SUMMARY -->
<div class="page">
    <h2>5. Venture Capital Outlook & Conclusion</h2>
    <p>
        Chennai's startup ecosystem has reached an inflection point. Financial inflow into local startups is expected to grow dramatically over the next two years, driven by national venture capital funds looking for stable, capital-efficient SaaS and deep-tech models.
    </p>
    <p>
        Entrepreneurs prioritizing execution speed, proper product-market fit, and efficient capital allocation will be best positioned to capture these opportunities and dominate India's next-generation economy.
    </p>
    <div class="chart-container">
        <img class="chart-img" src="data:image/png;base64,{chart_invest}" />
    </div>
</div>

</body>
</html>
"""

# Save to destination
sys.path.insert(0, '/home/ubuntu/aarkaai3b')
from skills.html.docs_generator import generate_pdf
generate_pdf(html_content, 'workspace/business_report.pdf')
print("PDF generated successfully.")
