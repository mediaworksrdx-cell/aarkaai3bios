# -*- coding: utf-8 -*-
"""
AARKAAI – Gamma-Style Chart Generator (Premium Edition)
Generates 5 distinct premium matplotlib charts with Gamma-level aesthetics:
  1. Vertical bar chart (growth/revenue)
  2. Multi-line trend chart (performance over time)
  3. Donut/pie chart (sector allocation)
  4. Horizontal bar chart (benchmark comparison)
  5. Stacked area chart (risk/cumulative)
Also supports Aarka Vision Stable Diffusion illustrations for cover pages.
All charts return base64 data URLs for self-contained HTML embedding.
"""
import os
import base64
import logging
import random
from io import BytesIO
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    from matplotlib.patches import FancyBboxPatch
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    logger.warning("matplotlib not found, falling back to SVG charts")
    HAS_MATPLOTLIB = False

# ─── Premium colour palettes ──────────────────────────────────────────────────
PALETTE_INDIGO = ['#6366F1', '#818CF8', '#A5B4FC', '#C7D2FE', '#E0E7FF']
PALETTE_MULTI  = ['#6366F1', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4']
PALETTE_DONUT  = ['#6366F1', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#EC4899']
GRADIENT_AREA  = ['#6366F180', '#10B98180', '#F59E0B80']

def _apply_gamma_style(ax, fig, title: str, transparent: bool = True):
    """Apply premium Gamma styling to a matplotlib axes."""
    # Read output background theme parameter dynamically from environment or global layout context
    import os
    is_dark = os.getenv("AARKAAI_THEME", "light").lower() == "dark"
    text_color = '#F3F4F6' if is_dark else '#0F172A'
    grid_color = '#1F2937' if is_dark else '#E2E8F0'
    spine_color = '#374151' if is_dark else '#CBD5E1'
    tick_color = '#9CA3AF' if is_dark else '#64748B'

    if transparent:
        fig.patch.set_alpha(0)
        ax.set_facecolor('none')
    ax.set_title(title.upper(), fontsize=9, fontweight='bold', color=text_color,
                 pad=12, loc='left', fontfamily='sans-serif')
    ax.tick_params(colors=tick_color, labelsize=7, length=3, width=0.6)
    ax.grid(True, axis='y', linestyle='--', color=grid_color, alpha=0.6, linewidth=0.5)
    ax.grid(False, axis='x')
    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)
    for spine in ('left', 'bottom'):
        ax.spines[spine].set_color(spine_color)
        ax.spines[spine].set_linewidth(0.6)

def _chart_to_base64(fig, name_prefix: str, output_dir: Path) -> dict:
    """Save a matplotlib figure as PNG, return base64 data URL dict."""
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{name_prefix}.png"
    fig.savefig(file_path, format='png', dpi=220, bbox_inches='tight',
                transparent=True, pad_inches=0.15)
    plt.close(fig)
    with open(file_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    logger.info(f"Saved premium chart to {file_path} ({os.path.getsize(file_path)/1024:.0f} KB)")
    return {
        "type": "png",
        "url": f"data:image/png;base64,{b64}",
        "svg_xml": "",
        "file_path": str(file_path)
    }

# ─── Chart 1: Vertical Bar Chart (Revenue / Growth) ─────────────────────────
def generate_bar_chart(topic: str, output_dir: Path, domain: str = None) -> dict:
    """Premium vertical bar chart showing quarterly/yearly growth."""
    from modules.gamma_domains import DOMAIN_REGISTRY
    
    cfg = None
    if domain and domain in DOMAIN_REGISTRY:
        cfg = DOMAIN_REGISTRY[domain]["charts"]["bar"]
        
    title = cfg["title"] if cfg else f"{topic} – Annual Revenue Growth"
    ylabel = cfg["ylabel"] if cfg else 'Revenue ($ Millions)'
    
    # Decouple domain-specific data points
    if domain == "options":
        labels = ['Q1 25', 'Q2 25', 'Q3 25', 'Q4 25', 'Q1 26 (P)']
        values = [85.0, 120.0, 165.0, 210.0, 260.0]
    elif domain == "ml":
        labels = ['v1.0', 'v1.5', 'v2.0', 'v3.0', 'v3.5 (P)']
        values = [1.2, 4.5, 12.8, 48.5, 120.0]
    elif domain == "crypto":
        labels = ['2022', '2023', '2024', '2025', '2026 (P)']
        values = [12.0, 28.0, 48.0, 72.0, 95.0]
    elif domain == "macro":
        labels = ['2022', '2023', '2024', '2025', '2026 (P)']
        values = [1.8, 2.1, 2.4, 2.5, 2.8]
    elif domain == "esg":
        labels = ['2022', '2023', '2024', '2025', '2026 (P)']
        values = [240.0, 480.0, 850.0, 1200.0, 1500.0]
    elif domain in ["healthcare", "pharma"]:
        labels = ['Phase I', 'Phase II', 'Phase III', 'NDA Filed', 'Approved']
        values = [120.0, 85.0, 42.0, 18.0, 8.0]
    elif domain == "energy":
        labels = ['2022', '2023', '2024', '2025', '2026 (P)']
        values = [4.2, 6.8, 9.4, 11.2, 12.4]
    elif domain == "general":
        labels = ['2018', '2020', '2022', '2024', '2026 (P)']
        values = [5.2, 3.1, 7.8, 12.4, 15.0]
    else:
        labels = ['FY 2021', 'FY 2022', 'FY 2023', 'FY 2024', 'FY 2025 (P)']
        values = [110.0, 185.0, 310.0, 540.0, 780.0]

    colors = _get_domain_colors(domain)
    
    if not HAS_MATPLOTLIB:
        return _svg_fallback(labels, values, title, output_dir, "chart_bar")
    
    fig, ax = plt.subplots(figsize=(6.5, 3.2), dpi=220)
    bars = ax.bar(labels, values, color=colors[:len(labels)], width=0.55,
                  edgecolor='none', zorder=3)
    
    # Value annotations
    unit = '%' if domain == 'macro' else ('B' if domain in ['crypto', 'realestate'] else ('GW' if domain == 'energy' else 'M'))
    prefix = '$' if domain not in ['macro', 'ml', 'energy', 'healthcare', 'pharma', 'general'] else ''
    
    import os
    is_dark = os.getenv("AARKAAI_THEME", "light").lower() == "dark"
    label_color = '#E2E8F0' if is_dark else '#1E293B'

    for b in bars:
        h = b.get_height()
        ax.annotate(f'{prefix}{h:.1f}{unit}' if h < 15 else f'{prefix}{int(h)}{unit}', 
                    xy=(b.get_x() + b.get_width()/2, h),
                    xytext=(0, 5), textcoords='offset points',
                    ha='center', va='bottom', fontsize=7, fontweight='bold', color=label_color)
                    
    _apply_gamma_style(ax, fig, title)
    ax.set_ylabel(ylabel, fontsize=7, color='#64748B')
    plt.tight_layout()
    return _chart_to_base64(fig, "chart_bar", output_dir)

# ─── Chart 2: Multi-Line Trend Chart (Performance Over Time) ─────────────────
def generate_line_chart(topic: str, output_dir: Path, domain: str = None) -> dict:
    """Premium multi-line chart showing multiple KPI trends."""
    from modules.gamma_domains import DOMAIN_REGISTRY
    
    cfg = None
    if domain and domain in DOMAIN_REGISTRY:
        cfg = DOMAIN_REGISTRY[domain]["charts"]["line"]
        
    title = cfg["title"] if cfg else f"{topic} – KPI Performance Trends"
    quarters = ['Q1 24', 'Q2 24', 'Q3 24', 'Q4 24', 'Q1 25', 'Q2 25', 'Q3 25', 'Q4 25']
    
    # Define domain-specific series
    if domain == "options":
        series = {
            'Implied Vol (IV)': [32, 28, 24, 38, 42, 35, 28, 30],
            'Realized Vol (RV)': [24, 22, 21, 30, 32, 28, 22, 24],
            'IV Skew (%)': [14, 12, 11, 16, 18, 15, 12, 13]
        }
    elif domain == "ml":
        series = {
            'Training Loss': [3.5, 2.8, 2.2, 1.8, 1.5, 1.3, 1.1, 0.9],
            'Validation Loss': [3.8, 3.1, 2.5, 2.1, 1.8, 1.6, 1.4, 1.25],
            'Accuracy (%)': [45, 62, 74, 82, 88, 92, 94, 96]
        }
    elif domain == "crypto":
        series = {
            'Throughput (TPS)': [12, 18, 35, 42, 85, 110, 124, 145],
            'Gas Fee ($)': [2.5, 1.8, 1.2, 0.8, 0.05, 0.03, 0.02, 0.02],
            'Active Wallets (k)': [40, 52, 65, 80, 110, 135, 150, 180]
        }
    elif domain == "cybersecurity":
        series = {
            'Blocked Threats (k)': [12, 18, 24, 32, 45, 62, 80, 98],
            'Mean Detect Time (s)': [85, 62, 42, 28, 18, 14, 12, 12],
            'Phish Resilient (%)': [65, 74, 82, 88, 92, 95, 98, 98.5]
        }
    elif domain == "healthcare":
        series = {
            'Patient Count (k)': [24, 32, 42, 55, 72, 88, 105, 120],
            'Avg Stay (Days)': [6.8, 6.4, 5.8, 5.2, 4.8, 4.5, 4.2, 4.2],
            'Quality Score (%)': [78, 82, 85, 88, 90, 92, 92, 94]
        }
    elif domain == "general":
        series = {
            'Structural Integrity (%)': [92, 90, 88, 85, 91, 93, 94, 96],
            'Restoration Progress (%)': [10, 25, 40, 55, 70, 82, 90, 95],
            'Visitor Satisfaction (%)': [78, 80, 82, 85, 87, 89, 91, 93]
        }
    else:
        series = {
            'Revenue ($M)': [40, 52, 68, 85, 110, 135, 160, 185],
            'Active Users (k)': [28, 38, 45, 62, 78, 95, 115, 140],
            'Operating Margin (%)': [12, 14, 15, 16, 18, 18, 20, 22]
        }
        
    colors = _get_domain_colors(domain)
    
    if not HAS_MATPLOTLIB:
        return _svg_fallback(quarters, list(series.values())[0], title, output_dir, "chart_line")
        
    fig, ax = plt.subplots(figsize=(6.5, 3.2), dpi=220)
    markers = ['o', 's', 'D']
    
    for i, (name, vals) in enumerate(series.items()):
        ax.plot(quarters, vals, marker=markers[i % len(markers)], color=colors[i % len(colors)],
                linewidth=2, markersize=4.5, markerfacecolor='white',
                markeredgewidth=1.5, markeredgecolor=colors[i % len(colors)], label=name, zorder=3)
                
    # Shade the background of the primary metric
    first_key = list(series.keys())[0]
    ax.fill_between(quarters, series[first_key], alpha=0.06, color=colors[0])
    
    _apply_gamma_style(ax, fig, title)
    import os
    is_dark = os.getenv("AARKAAI_THEME", "light").lower() == "dark"
    legend_label_color = '#CBD5E1' if is_dark else '#475569'

    ax.legend(fontsize=6.5, frameon=False, loc='upper left', labelcolor=legend_label_color)
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()
    return _chart_to_base64(fig, "chart_line", output_dir)

# ─── Chart 3: Donut / Pie Chart (Sector Allocation) ─────────────────────────
def generate_donut_chart(topic: str, output_dir: Path, domain: str = None) -> dict:
    """Premium donut chart showing sector/asset allocation."""
    from modules.gamma_domains import DOMAIN_REGISTRY
    
    cfg = None
    if domain and domain in DOMAIN_REGISTRY:
        cfg = DOMAIN_REGISTRY[domain]["charts"]["donut"]
        
    title = cfg["title"] if cfg else f"{topic} – Sector Allocation"
    
    # Define domain-specific segmentation
    if domain == "options":
        segments = ['Index Options', 'Equity Options', 'Future Options', 'ETF Options', 'Volatility VIX']
        sizes = [42, 28, 15, 10, 5]
    elif domain == "ml":
        segments = ['Attention Layer', 'Feed Forward', 'LayerNorm', 'Residual Connection', 'Linear Projection']
        sizes = [38, 32, 12, 10, 8]
    elif domain == "crypto":
        segments = ['Layer-1 Protocol', 'Layer-2 Rollups', 'DeFi Liquidity', 'Web3 / Gaming', 'Infrastructure']
        sizes = [48, 22, 18, 8, 4]
    elif domain in ["healthcare", "pharma"]:
        segments = ['Clinical Ops', 'Therapeutics', 'Diagnostics', 'Digital Care', 'Administrative']
        sizes = [42, 28, 18, 8, 4]
    elif domain == "cybersecurity":
        segments = ['Cloud Defense', 'Endpoint Security', 'Identity Access', 'Network Gateway', 'Risk & Audit']
        sizes = [38, 28, 18, 10, 6]
    elif domain == "esg":
        segments = ['Solar Power', 'Offshore Wind', 'Battery Storage', 'Bioenergy', 'Grid-Tech']
        sizes = [42, 28, 15, 10, 5]
    elif domain == "general":
        segments = ['Heritage Pilgrims', 'Cultural Tourists', 'Academic Researchers', 'Local Devotees', 'Foreign Visitors']
        sizes = [45, 25, 12, 10, 8]
    else:
        segments = ['Enterprise SaaS', 'Consumer tech', 'Fintech Platform', 'DeepTech core', 'AdTech / Market']
        sizes = [38, 24, 18, 12, 8]
        
    colors = _get_domain_colors(domain)
    
    if not HAS_MATPLOTLIB:
        return _svg_fallback(segments, sizes, title, output_dir, "chart_donut")
        
    fig, ax = plt.subplots(figsize=(4.5, 3.5), dpi=220)
    fig.patch.set_alpha(0)
    
    wedges, texts, autotexts = ax.pie(
        sizes, labels=segments, colors=colors[:len(segments)],
        autopct='%1.1f%%', startangle=140, pctdistance=0.78,
        wedgeprops=dict(width=0.42, edgecolor='white', linewidth=1.5)
    )
    
    import os
    is_dark = os.getenv("AARKAAI_THEME", "light").lower() == "dark"
    label_color = '#CBD5E1' if is_dark else '#475569'
    auto_text_color = '#E2E8F0' if is_dark else '#1E293B'
    title_color = '#F3F4F6' if is_dark else '#0F172A'
    
    for t in texts:
        t.set_fontsize(6.5)
        t.set_color(label_color)
    for t in autotexts:
        t.set_fontsize(6)
        t.set_fontweight('bold')
        t.set_color(auto_text_color)
        
    ax.set_title(title.upper(), fontsize=9, fontweight='bold',
                 color=title_color, pad=14, loc='left', fontfamily='sans-serif')
    plt.tight_layout()
    return _chart_to_base64(fig, "chart_donut", output_dir)

# ─── Chart 4: Horizontal Bar Chart (Benchmark Comparison) ───────────────────
def generate_hbar_chart(topic: str, output_dir: Path, domain: str = None) -> dict:
    """Premium horizontal bar chart for benchmark/efficiency metrics."""
    from modules.gamma_domains import DOMAIN_REGISTRY
    
    cfg = None
    if domain and domain in DOMAIN_REGISTRY:
        cfg = DOMAIN_REGISTRY[domain]["charts"]["hbar"]
        
    title = cfg["title"] if cfg else f"{topic} – Operational Efficiency Benchmarks"
    
    # Define domain-specific benchmarks
    if domain == "options":
        metrics = ['Theta Decay\nEfficiency', 'Execution\nSlippage', 'Margin\nUtilization',
                   'Delta Hedging\nSpeed', 'Volatility Skew\nCapture']
        scores = [88, 92, 74, 85, 90]
    elif domain == "ml":
        metrics = ['Attention\nKernel Uptime', 'Quantization\nThroughput', 'VRAM Bandwidth\nUtilization',
                   'KV-Cache\nSavings', 'Inference\nCompilation']
        scores = [95, 92, 88, 78, 90]
    elif domain == "crypto":
        metrics = ['Consensus\nUptime', 'Layer-2 Gas\nSavings', 'Smart Contract\nAudit Score',
                   'Node Sync\nVelocity', 'Tx Processing\nSpeed']
        scores = [99, 95, 92, 84, 90]
    elif domain == "cybersecurity":
        metrics = ['Intrusion\nBlock Rate', 'Incident Response\nVelocity', 'Patch Deployment\nSpeed',
                   'Phishing Training\nResilience', 'Compliance\nAudit Score']
        scores = [99, 85, 92, 98, 95]
    elif domain == "esg":
        metrics = ['Carbon Abatement\nIndex', 'Water Recycle\nEfficiency', 'Renewable Generation\nYield',
                   'Supply Chain Green\nTaxonomy', 'Waste Recovery\nRate']
        scores = [88, 84, 92, 78, 90]
    elif domain == "general":
        metrics = ['Stone Conservation\nIndex', 'Foundation Stability\nIndex', 'Seismic Resilience\nScore',
                   'Archival Documentation\nCoverage', 'Visitor Safety\nRating']
        scores = [94, 91, 88, 95, 92]
    else:
        metrics = ['Infrastructure\nEfficiency', 'Cost\nOptimization', 'Supply Chain\nResilience',
                   'Workforce\nProductivity', 'Digital\nTransformation']
        scores = [78, 85, 72, 91, 88]
        
    # Sort together
    paired = sorted(zip(scores, metrics))
    scores, metrics = [list(t) for t in zip(*paired)]
    
    colors = _get_domain_colors(domain)
    
    if not HAS_MATPLOTLIB:
        return _svg_fallback(metrics, scores, title, output_dir, "chart_hbar")
        
    fig, ax = plt.subplots(figsize=(6.5, 3.2), dpi=220)
    bar_colors = [colors[i % len(colors)] for i in range(len(metrics))]
    bars = ax.barh(metrics, scores, color=bar_colors, height=0.55, edgecolor='none', zorder=3)
    
    import os
    is_dark = os.getenv("AARKAAI_THEME", "light").lower() == "dark"
    score_color = '#E2E8F0' if is_dark else '#1E293B'
    grid_color = '#1F2937' if is_dark else '#E2E8F0'

    for b, s in zip(bars, scores):
        ax.text(b.get_width() + 1.5, b.get_y() + b.get_height()/2,
                f'{s}%', va='center', ha='left', fontsize=7, fontweight='bold', color=score_color)
                
    _apply_gamma_style(ax, fig, title)
    ax.grid(True, axis='x', linestyle='--', color=grid_color, alpha=0.6, linewidth=0.5)
    ax.grid(False, axis='y')
    ax.set_xlim(0, 110)
    ax.set_xlabel('Score (%)', fontsize=7, color='#64748B')
    ax.invert_yaxis()
    plt.tight_layout()
    return _chart_to_base64(fig, "chart_hbar", output_dir)

# ─── Chart 5: Stacked Area Chart (Risk / Cumulative) ────────────────────────
def generate_area_chart(topic: str, output_dir: Path, domain: str = None) -> dict:
    """Premium stacked area chart showing risk exposure or cumulative trends."""
    from modules.gamma_domains import DOMAIN_REGISTRY
    
    cfg = None
    if domain and domain in DOMAIN_REGISTRY:
        cfg = DOMAIN_REGISTRY[domain]["charts"]["area"]
        
    title = cfg["title"] if cfg else f"{topic} – Cumulative Risk Exposure"
    years = ['2021', '2022', '2023', '2024', '2025', '2026']
    
    # Define domain-specific risk categories
    if domain == "options":
        labels = ['Gamma Risk', 'Vega Volatility', 'Theta Slippage']
        y1 = [8, 12, 18, 22, 28, 35]
        y2 = [15, 20, 24, 28, 32, 40]
        y3 = [5, 8, 10, 12, 15, 18]
    elif domain == "ml":
        labels = ['VRAM Overload', 'Quantization Loss', 'Compute Overheating']
        y1 = [12, 18, 22, 28, 35, 42]
        y2 = [10, 14, 18, 22, 26, 30]
        y3 = [5, 6, 8, 10, 12, 14]
    elif domain == "crypto":
        labels = ['Smart Contract exploit', 'Consensus Forfeits', 'Liquidity Slippage']
        y1 = [15, 22, 28, 24, 18, 12]
        y2 = [8, 12, 15, 18, 20, 22]
        y3 = [12, 15, 18, 22, 25, 28]
    elif domain == "cybersecurity":
        labels = ['Ransomware Injections', 'Phishing compromises', 'Cloud Misconfigs']
        y1 = [18, 24, 32, 28, 22, 14]
        y2 = [14, 18, 22, 25, 20, 15]
        y3 = [8, 12, 15, 18, 22, 24]
    elif domain == "general":
        labels = ['Weathering Wear', 'Structural Fatigue', 'High Crowd Impact']
        y1 = [10, 12, 15, 18, 22, 25]
        y2 = [8, 10, 12, 14, 13, 11]
        y3 = [4, 6, 9, 12, 15, 18]
    else:
        labels = ['Regulatory Risk', 'Market Volatility', 'Operational Risk']
        y1 = [10, 14, 18, 22, 26, 32]
        y2 = [15, 20, 24, 28, 32, 38]
        y3 = [6, 8, 10, 12, 15, 18]
        
    colors = _get_domain_colors(domain)
    
    if not HAS_MATPLOTLIB:
        return _svg_fallback(years, [a+b+c for a,b,c in zip(y1,y2,y3)], title, output_dir, "chart_area")
        
    fig, ax = plt.subplots(figsize=(6.5, 3.2), dpi=220)
    ax.stackplot(years, y1, y2, y3, labels=labels, colors=colors[:3], alpha=0.75, zorder=3)
    
    total = [a+b+c for a,b,c in zip(y1, y2, y3)]
    ax.plot(years, total, color='#EF4444', linewidth=1.5, linestyle='--', label='Total Exposure', zorder=4)
    
    _apply_gamma_style(ax, fig, title)
    import os
    is_dark = os.getenv("AARKAAI_THEME", "light").lower() == "dark"
    legend_label_color = '#CBD5E1' if is_dark else '#475569'

    ax.legend(fontsize=6, frameon=False, loc='upper left', labelcolor=legend_label_color)
    ax.set_ylabel('Risk Index Score', fontsize=7, color='#64748B')
    plt.tight_layout()
    return _chart_to_base64(fig, "chart_area", output_dir)

def _get_domain_colors(domain: str = None):
    """Return a premium color palette matching the domain's aesthetic."""
    if not domain:
        return ['#6366F1', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4']
        
    themes = {
        "vc": ['#0D9488', '#10B981', '#F59E0B', '#3B82F6', '#8B5CF6'],
        "equity": ['#6366F1', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'],
        "options": ['#8B5CF6', '#F59E0B', '#EF4444', '#10B981', '#6366F1'],
        "ml": ['#8B5CF6', '#0D9488', '#F59E0B', '#EF4444', '#3B82F6'],
        "crypto": ['#8B5CF6', '#F59E0B', '#10B981', '#EF4444', '#6366F1'],
        "macro": ['#6366F1', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'],
        "healthcare": ['#0D9488', '#3B82F6', '#F59E0B', '#EF4444', '#10B981'],
        "cybersecurity": ['#E53E3E', '#3B82F6', '#10B981', '#8B5CF6', '#F59E0B'],
        "esg": ['#0D9488', '#10B981', '#3B82F6', '#8B5CF6', '#F59E0B'],
        "realestate": ['#D97706', '#B45309', '#10B981', '#3B82F6', '#EF4444'],
        "manufacturing": ['#6366F1', '#10B981', '#EF4444', '#8B5CF6', '#06B6D4'],
        "supplychain": ['#6366F1', '#10B981', '#EF4444', '#8B5CF6', '#06B6D4'],
        "pharma": ['#E53E3E', '#DD6B20', '#3B82F6', '#10B981', '#8B5CF6'],
        "energy": ['#D97706', '#10B981', '#B45309', '#3B82F6', '#EF4444'],
        "general": ['#4F46E5', '#06B6D4', '#F59E0B', '#EF4444', '#10B981']
    }
    return themes.get(domain, ['#6366F1', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'])

# ─── SVG Fallback (when matplotlib is unavailable) ───────────────────────────
def compile_svg_string(x, y, title, chart_type='line', color='#6366F1') -> str:
    """Helper to compile raw SVG XML string."""
    max_val = max(y) if y else 100
    min_val = min(y) if y else 0
    val_range = (max_val - min_val) if max_val != min_val else 100
    
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 180" width="400" height="180" style="background:none; width:100%; height:180px;">')
    svg.append(f'<text x="200" y="20" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="bold" fill="#0F172A">{title.upper()}</text>')
    for i in range(1, 5):
        y_pos = 25 + i * 30
        svg.append(f'<line x1="40" y1="{y_pos}" x2="360" y2="{y_pos}" stroke="#E2E8F0" stroke-width="0.5" stroke-dasharray="2,2"/>')
    num_pts = len(x)
    x_step = 320 / (num_pts - 1) if num_pts > 1 else 320
    points = []
    for idx, (val_x, val_y) in enumerate(zip(x, y)):
        px = 40 + idx * x_step
        py = 145 - ((val_y - min_val) / val_range) * 110
        points.append((px, py))
    if chart_type == 'bar':
        bar_width = min(25, 200 / num_pts)
        for idx, (px, py) in enumerate(points):
            bar_h = 145 - py
            svg.append(f'<rect x="{px - bar_width/2}" y="{py}" width="{bar_width}" height="{bar_h}" rx="2" fill="{color}" fill-opacity="0.85"/>')
            svg.append(f'<text x="{px}" y="{py - 4}" text-anchor="middle" font-family="sans-serif" font-size="7" font-weight="bold" fill="#1E293B">{format(y[idx], ",.0f")}</text>')
    else:
        path_coords = " ".join(f"{px},{py}" for px, py in points)
        area_coords = f"40,145 {path_coords} {points[-1][0]},145"
        svg.append(f'<polygon points="{area_coords}" fill="{color}" fill-opacity="0.08"/>')
        svg.append(f'<polyline points="{path_coords}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
        for px, py in points:
            svg.append(f'<circle cx="{px}" cy="{py}" r="3.5" fill="#FFFFFF" stroke="{color}" stroke-width="1.5"/>')
    svg.append(f'<line x1="40" y1="145" x2="360" y2="145" stroke="#CBD5E1" stroke-width="0.8"/>')
    for idx, px in enumerate(points):
        svg.append(f'<text x="{px[0]}" y="160" text-anchor="middle" font-family="sans-serif" font-size="7" fill="#64748B">{x[idx]}</text>')
    svg.append('</svg>')
    return "".join(svg)

def _svg_fallback(x, y, title, output_dir, name_prefix):
    """Generate an SVG fallback chart resource."""
    svg_content = compile_svg_string(x, y, title, 'bar', '#6366F1')
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{name_prefix}.svg"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    b64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
    return {
        "type": "svg",
        "url": f"data:image/svg+xml;base64,{b64}",
        "svg_xml": svg_content,
        "file_path": str(file_path)
    }

# ─── Legacy compatibility: get_chart_resource ────────────────────────────────
def get_chart_resource(x, y, title, chart_type='line', color='#6366F1', name_prefix='chart', output_dir=None) -> dict:
    """Generate a chart resource (legacy API – kept for backward compat)."""
    if not output_dir:
        from config import SAFE_WORK_DIR
        output_dir = Path(SAFE_WORK_DIR) / "charts"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if HAS_MATPLOTLIB:
        try:
            fig, ax = plt.subplots(figsize=(6.5, 3.0), dpi=220, facecolor='none')
            ax.set_facecolor('none')
            if chart_type == 'bar':
                bars = ax.bar(x, y, color=color, alpha=0.85, width=0.5, edgecolor='none')
                for b in bars:
                    height = b.get_height()
                    ax.annotate(format(height, ",.0f"),
                                xy=(b.get_x() + b.get_width()/2, height),
                                xytext=(0, 3), textcoords="offset points",
                                ha='center', va='bottom', fontsize=6, fontweight='bold', color='#1E293B')
            else:
                ax.plot(x, y, marker='o', color=color, linewidth=2.0, markersize=4,
                        markerfacecolor='#FFFFFF', markeredgewidth=1.5)
                ax.fill_between(x, y, color=color, alpha=0.1)
            _apply_gamma_style(ax, fig, title)
            plt.tight_layout()
            return _chart_to_base64(fig, name_prefix, output_dir)
        except Exception as e:
            logger.error(f"Matplotlib chart creation failed: {e}. Falling back to SVG.")
    return _svg_fallback(x, y, title, output_dir, name_prefix)

# ─── Aarka Vision Stable Diffusion image generator ──────────────────────────
_sd_pipeline_cached = None

def get_aarkavision_image_resource(prompt: str, name_prefix: str, output_dir=None) -> dict:
    """
    Generate a premium illustration using the Aarka Vision model.
    Returns:
        dict containing:
            - "type": "png"
            - "url": base64 Data URL
            - "file_path": path to the saved file
    """
    import torch
    from diffusers import StableDiffusionPipeline
    
    if not output_dir:
        from config import SAFE_WORK_DIR
        output_dir = Path(SAFE_WORK_DIR) / "charts"
    else:
        output_dir = Path(output_dir)
        
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{name_prefix}.png"
    
    global _sd_pipeline_cached
    logger.info(f"Generating Aarka Vision image for prompt: {prompt}")
    
    try:
        if _sd_pipeline_cached is None:
            standalone_model_path = "/workspace/aarkaai3b/aarkaa-vision-standalone"
            if os.path.exists(standalone_model_path):
                logger.info(f"Loading standalone AARKAA-VISION model from {standalone_model_path}...")
                pipe = StableDiffusionPipeline.from_pretrained(
                    standalone_model_path,
                    torch_dtype=torch.float16,
                    use_safetensors=True
                )
            else:
                logger.info("Standalone model not found. Falling back to dynamic base + LoRA loading...")
                token = os.environ.get("HF_TOKEN")
                base_model = "CompVis/stable-diffusion-v1-4"
                lora_model = "rthshr/aarkaa-ai-vision"
                pipe = StableDiffusionPipeline.from_pretrained(
                    base_model,
                    torch_dtype=torch.float16,
                    use_safetensors=True
                )
                if token:
                    pipe.load_lora_weights(lora_model, token=token)
                else:
                    pipe.load_lora_weights(lora_model)
            
            pipe.to("cuda")
            _sd_pipeline_cached = pipe
            logger.info("AARKAA-VISION standalone pipeline initialized successfully on GPU.")
            
        # Generate the image
        image = _sd_pipeline_cached(prompt, num_inference_steps=30).images[0]
        image.save(file_path)
        
        with open(file_path, "rb") as f:
            b64_str = "data:image/png;base64," + base64.b64encode(f.read()).decode('utf-8')
            
        logger.info(f"Saved Aarka Vision image to: {file_path}")
        return {
            "type": "png",
            "url": b64_str,
            "file_path": str(file_path)
        }
    except Exception as e:
        logger.error(f"Aarka Vision image generation failed: {e}. Falling back to default chart.")
        # Fallback to a dummy matplotlib style chart if SD fails
        return get_chart_resource(['A', 'B', 'C'], [50, 70, 90], f"Asset Trend ({name_prefix})", "line", "#6366F1", name_prefix, output_dir)
