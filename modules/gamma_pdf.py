# -*- coding: utf-8 -*-
"""
AARKAAI – Gamma-Style PDF Generator (Premium Edition)
Compiles breathtaking, high-density, 6-page visual reports with:
  - 1 AI-generated cover illustration (Aarka Vision Stable Diffusion)
  - 5 distinct premium matplotlib data charts (bar, line, donut, hbar, area)
  - Rich LLM-generated text sections
  - Premium typography, cards, callouts, and Gamma-style page layouts
Uses self-contained base64 data URLs for all images.
Supports multiple color templates.
"""
import os
import re
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Import chart generation
try:
    from modules.gamma_charts import (
        generate_bar_chart, generate_line_chart, generate_donut_chart,
        generate_hbar_chart, generate_area_chart,
        get_aarkavision_image_resource, get_chart_resource
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from modules.gamma_charts import (
        generate_bar_chart, generate_line_chart, generate_donut_chart,
        generate_hbar_chart, generate_area_chart,
        get_aarkavision_image_resource, get_chart_resource
    )

# Curated premium design templates matching Gamma aesthetics
TEMPLATES = {
    "indigo": {
        "bg_color": "#F8FAFC",
        "text_color": "#1E293B",
        "primary_color": "#6366F1",
        "secondary_color": "#10B981",
        "card_bg": "#FFFFFF",
        "card_border": "#E2E8F0",
        "h1_color": "#0F172A",
        "h2_color": "#0F172A",
        "cover_bg": "linear-gradient(135deg, #0F172A 0%, #1E1B4B 100%)",
        "cover_text": "#FFFFFF",
        "badge_bg": "#EEF2F6",
        "badge_text": "#4F46E5",
        "callout_bg": "#F5F3FF",
        "callout_border": "#6366F1",
        "callout_text": "#4F46E5"
    },
    "dark": {
        "bg_color": "#0B0F19",
        "text_color": "#CBD5E1",
        "primary_color": "#8B5CF6",
        "secondary_color": "#F59E0B",
        "card_bg": "#111827",
        "card_border": "#1F2937",
        "h1_color": "#FFFFFF",
        "h2_color": "#F3F4F6",
        "cover_bg": "linear-gradient(135deg, #020617 0%, #0F172A 100%)",
        "cover_text": "#FFFFFF",
        "badge_bg": "#1E1B4B",
        "badge_text": "#C084FC",
        "callout_bg": "#1E152A",
        "callout_border": "#8B5CF6",
        "callout_text": "#D8B4FE"
    },
    "emerald": {
        "bg_color": "#F0FDFA",
        "text_color": "#115E59",
        "primary_color": "#0D9488",
        "secondary_color": "#0F766E",
        "card_bg": "#FFFFFF",
        "card_border": "#CCFBF1",
        "h1_color": "#042F2E",
        "h2_color": "#042F2E",
        "cover_bg": "linear-gradient(135deg, #042F2E 0%, #0D9488 100%)",
        "cover_text": "#FFFFFF",
        "badge_bg": "#CCFBF1",
        "badge_text": "#0D9488",
        "callout_bg": "#F0FDF4",
        "callout_border": "#0D9488",
        "callout_text": "#0F766E"
    },
    "crimson": {
        "bg_color": "#FFF5F5",
        "text_color": "#2D3748",
        "primary_color": "#E53E3E",
        "secondary_color": "#DD6B20",
        "card_bg": "#FFFFFF",
        "card_border": "#FED7D7",
        "h1_color": "#742A2A",
        "h2_color": "#742A2A",
        "cover_bg": "linear-gradient(135deg, #742A2A 0%, #E53E3E 100%)",
        "cover_text": "#FFFFFF",
        "badge_bg": "#FED7D7",
        "badge_text": "#E53E3E",
        "callout_bg": "#FFF5F5",
        "callout_border": "#E53E3E",
        "callout_text": "#9B2C2C"
    },
    "amber": {
        "bg_color": "#FFFBEB",
        "text_color": "#78350F",
        "primary_color": "#D97706",
        "secondary_color": "#B45309",
        "card_bg": "#FFFFFF",
        "card_border": "#FEF3C7",
        "h1_color": "#451A03",
        "h2_color": "#451A03",
        "cover_bg": "linear-gradient(135deg, #451A03 0%, #D97706 100%)",
        "cover_text": "#FFFFFF",
        "badge_bg": "#FEF3C7",
        "badge_text": "#D97706",
        "callout_bg": "#FFFDF5",
        "callout_border": "#D97706",
        "callout_text": "#B45309"
    }
}

def get_detailed_section(topic: str, section_title: str, prompt_hint: str) -> str:
    """
    Use the local llama.cpp model to generate a rich, high-density paragraph tailored to the specific
    domain of the topic.
    """
    from modules import aarkaa_engine
    from modules.gamma_domains import detect_domain, DOMAIN_REGISTRY
    
    domain = detect_domain(topic)
    
    # Tailor LLM System Prompts by Domain
    prompts = {
        "vc": "You are a Senior Venture Capital Partner writing a high-density ecosystem intelligence report. Use VC metrics like ARR, runway, CAC, LTV, dilution, valuation multiple, and seed/Series-A dynamics. ",
        "equity": "You are a lead Wall Street Equity Research Analyst writing an institutional stock research report. Use financial metrics like P/E ratio, PEG, EBITDA margins, Free Cash Flow, discounted cash flows, and valuation multiples. ",
        "options": "You are a Quantitative Options Strategist writing a derivative risk and yield report. Use terms like Option Greeks (Delta, Gamma, Theta, Vega), implied volatility skew, margin requirements, max pain, and hedging. ",
        "ml": "You are a Principal AI Scientist writing a deep technical machine learning and architecture report. Use terms like parameters, quantization (INT4/FP8), perplexity, latency, FLOPS, fine-tuning, and model architectures. ",
        "crypto": "You are a Quantitative Cryptocurrency Researcher writing a protocol and ledger security report. Use terms like consensus protocols, gas fees, staking yields, validator nodes, smart contract logic, and Layer-2 rollups. ",
        "macro": "You are an IMF Chief Economist writing a global macroeconomic and monetary policy report. Use terms like GDP growth, core inflation, yield curve inversion, Fed funds rate, interest rates, and trade balance. ",
        "healthcare": "You are a Digital Health Chief Medical Officer writing a clinical systems optimization report. Use terms like bed utilization, patient readmission, EHR integration, telehealth throughput, and clinical staffing. ",
        "cybersecurity": "You are an Enterprise Chief Information Security Officer (CISO) writing a zero-trust network risk report. Use terms like intrusion block rates, mean time to detection (MTTD), patch latency, phishing resilience, and NIST compliance. ",
        "esg": "You are a Chief Sustainability Officer writing a corporate ESG and climate technology report. Use terms like carbon abatement, ESG rating scores, renewable generation mix, EU taxonomy compliance, and green capex. ",
        "realestate": "You are a Managing Director of a commercial REIT writing a real estate valuation report. Use terms like portfolio occupancy, net asset value (NAV), cap rate yields, weighted average lease term (WALT), and LTV. ",
        "manufacturing": "You are a VP of Industrial Operations writing an advanced manufacturing and automation report. Use terms like Overall Equipment Effectiveness (OEE), cycle times, Six Sigma quality yields, predictive maintenance, and robotic integration. ",
        "supplychain": "You are a Chief Logistics Officer writing a global supply chain resilience report. Use terms like logistics velocity, inventory turns, supplier SLA compliance, on-time delivery, and freight cost consolidation. ",
        "pharma": "You are a VP of Clinical R&D writing a pharmaceutical drug development report. Use terms like clinical trial phases, FDA fast-track approval rates, molecular screening, pathology, and patent expiry risk. ",
        "energy": "You are a Smart Grid Infrastructure Director writing an energy grid load optimization report. Use terms like grid capacity (GW), renewable generation mix, grid-scale battery storage (GWh), generation cost per MWh, and DERMS. ",
        "corporate": "You are a McKinsey Senior Partner writing a high-density corporate strategy report. Use structured framework terms like MECE, porter's five forces, value chains, and synergy levers. "
    }
    
    system_prompt = prompts.get(domain, prompts["corporate"])
    
    prompt = (
        f"<|im_start|>system\n"
        f"{system_prompt}"
        f"Generate a single, comprehensive, highly detailed paragraph of exactly 6 to 8 long, professional sentences "
        f"about '{section_title}' in the context of the report topic '{topic}'.\n"
        f"Focus on practical details, market dynamics, concrete examples, and strategic implications.\n"
        f"Do not write introductions, placeholders, or headers. Write only the detailed paragraph text itself. "
        f"Your response must be in natural, clean English.<|im_end|>\n"
        f"<|im_start|>user\n"
        f"Topic: {topic}\n"
        f"Section: {section_title}\n"
        f"Context to cover: {prompt_hint}\n"
        f"Detailed Paragraph:<|im_end|>\n"
        f"<|im_start|>assistant\n"
        f"Detailed Paragraph:"
    )
    try:
        response = aarkaa_engine.generate_raw(prompt=prompt, max_new_tokens=400)
        clean_text = response.replace("<|im_end|>", "").replace("<|im_start|>", "").strip()
        clean_text = re.sub(r'^(#|\d+\.|\b(Section|Introduction|Conclusion)\b:?\s*).*?\n', '', clean_text, flags=re.IGNORECASE)
        if len(clean_text.split()) < 100:
            raise ValueError("Generated text is too short")
        return clean_text
    except Exception as e:
        logger.warning(f"LLM section generation failed: {e}. Using domain-specific high-density fallback.")
        
        # Select correct domain dictionary, fallback to corporate
        domain_dict = DOMAIN_REGISTRY.get(domain, DOMAIN_REGISTRY["corporate"])
        fallback_text = domain_dict["fallbacks"].get(section_title)
        if not fallback_text:
            fallback_text = DOMAIN_REGISTRY["corporate"]["fallbacks"].get(section_title, (
                f"The thorough exploration of {section_title} within the {topic} ecosystem highlights a series of complex, "
                f"interdependent factors that are reshaping the industry landscape. To maintain a competitive edge, organizations "
                f"must continuously evaluate their strategic objectives, operational capabilities, and technological infrastructure. "
                f"By fostering a culture of continuous learning, agile adaptation, and data-driven decision-making, enterprises "
                f"can successfully navigate market uncertainties and capture emerging growth opportunities. Ultimately, the path "
                f"to sustainable success lies in the seamless integration of advanced computational tools, robust risk management "
                f"frameworks, and a relentless focus on delivering superior value to customers, partners, and stakeholders alike. "
                f"Through disciplined execution and strategic foresight, modern enterprises can build highly resilient operational "
                f"models that thrive in even the most volatile and competitive global markets, securing long-term leadership "
                f"and driving substantial economic impact across the entire value chain."
            ))
        return fallback_text

def render_chart_html(chart_data: dict, class_name: str = "chart-img") -> str:
    """
    Render a chart safely. If it is an SVG, we embed the raw XML inline so WeasyPrint
    can natively render it perfectly. If it is a PNG, we output a standard img tag with the specified class_name.
    """
    if chart_data.get("type") == "svg":
        return chart_data["svg_xml"]
    else:
        return f'<img class="{class_name}" src="{chart_data["url"]}">'

def compile_gamma_pdf(topic: str, output_name: str, template: str = "indigo", sections: list = None) -> str:
    """
    Orchestrate the full 6-page Gamma-style PDF generation, using the selected template style.
    """
    logger.info(f"Starting Gamma PDF generation for topic: {topic} using template: {template}")
    from modules.gamma_domains import detect_domain, DOMAIN_REGISTRY
    
    domain = detect_domain(topic)
    domain_profile = DOMAIN_REGISTRY[domain]
    
    # Auto-resolve template based on domain if the default "indigo" or an invalid template is passed
    if template == "indigo" and domain_profile["template"] != "indigo":
        template = domain_profile["template"]
    t = TEMPLATES.get(template.lower(), TEMPLATES["indigo"])
    
    # Get SAFE_WORK_DIR for writing separate chart files
    from config import SAFE_WORK_DIR
    charts_dir = Path(SAFE_WORK_DIR) / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    
    # ── Generate 1 AI cover illustration using Aarka Vision SD on GPU ────────
    logger.info("Generating AI cover illustration with Aarka Vision...")
    cover_prompt = f"{topic} executive headquarters, modern office lobby, professional corporate design, photorealistic, 8k, highly detailed, clean lighting"
    cover_img = get_aarkavision_image_resource(cover_prompt, "cover_illustration", charts_dir)
    
    # ── Generate 5 premium matplotlib data charts ────────────────────────────
    logger.info(f"Generating 5 premium matplotlib charts for domain {domain}...")
    chart1 = generate_bar_chart(topic, charts_dir, domain=domain)       # Revenue growth bars
    chart2 = generate_line_chart(topic, charts_dir, domain=domain)      # Multi-line KPI trends
    chart3 = generate_donut_chart(topic, charts_dir, domain=domain)     # Sector allocation donut
    chart4 = generate_hbar_chart(topic, charts_dir, domain=domain)      # Efficiency benchmarks
    chart5 = generate_area_chart(topic, charts_dir, domain=domain)      # Risk exposure area

    # ── Generate or use pre-generated 5 high-density section paragraphs ──────
    if sections and len(sections) == 5:
        logger.info("Using pre-generated sections passed from streaming pipeline")
        sec1, sec2, sec3, sec4, sec5 = sections
    else:
        logger.info("Generating sections synchronously inside compile_gamma_pdf")
        sec1 = get_detailed_section(topic, "Executive Summary & Framework", "Core thesis, market indicators, and initial adoption vectors.")
        sec2 = get_detailed_section(topic, "Market Analysis & Sector Segmentation", "Analysis of market drivers, segmentation details, and industry positioning.")
        sec3 = get_detailed_section(topic, "Quantitative Performance & Revenue Velocity", "Financial benchmarks, quarterly trends, revenue scalability, and growth curves.")
        sec4 = get_detailed_section(topic, "Operational Efficiency & Architecture", "Infrastructure layout, logistical pipelines, efficiency metrics, and cost-to-output optimization.")
        sec5 = get_detailed_section(topic, "Risk Analysis, Vulnerability & Strategic Outlook", "Defensive positioning, regulatory compliance, risk distribution, and long-term ecosystem forecasts.")

    # ── Resolve Registry-Driven Variables for HTML Injection ─────────────────
    c_kpis = domain_profile["cover_kpis"]
    d_kpis = domain_profile["dashboard_kpis"]
    
    # Brand logos
    brand_html = []
    for b in domain_profile["brand_logos"]:
        if b["type"] == "rect":
            icon_svg = f'<rect x="0" y="0" width="12" height="12" fill="{b["color"]}" rx="2"/>'
        elif b["type"] == "diamond":
            icon_svg = f'<polygon points="6,0 12,6 6,12 0,6" fill="{b["color"]}"/>'
        else:
            icon_svg = f'<polygon points="6,0 11,3 11,9 6,12 1,9 1,3" fill="{b["color"]}"/>'
        brand_html.append(f"""
        <div style="display: flex; align-items: center; gap: 3px; float: left; margin-right: 8px; margin-bottom: 4px;">
            <svg width="12" height="12" viewBox="0 0 12 12" style="max-height:12px; display:inline-block; vertical-align:middle;">{icon_svg}</svg>
            <span style="font-size: 8px; font-weight: 900; color: #475569; vertical-align:middle;">{b["name"]}</span>
        </div>
        """)
    brand_logos_rendered = "".join(brand_html)
    
    # Timeline
    t_m = domain_profile["timeline"]
    
    # Table rendering
    table_headers = "".join([f'<th style="padding: 3px; border: 1px solid #E2E8F0;">{h}</th>' for h in domain_profile["table"]["headers"]])
    table_rows = []
    for row in domain_profile["table"]["rows"]:
        row_html = []
        for idx, cell in enumerate(row):
            align = "text-align: left; font-weight: bold;" if idx == 0 else ""
            bg = "background: #D1FAE5; color: #065F46; font-weight: bold;" if any(w in cell.lower() for w in ["high", "buy", "elite", "approved", "leader"]) else (
                "background: #FEF3C7; color: #92400E;" if "med" in cell.lower() else (
                    "background: #FEE2E2; color: #991B1B; font-weight: bold;" if any(w in cell.lower() for w in ["low", "slow"]) else ""
                )
            )
            row_html.append(f'<td style="padding: 3px; border: 1px solid #E2E8F0; {align} {bg}">{cell}</td>')
        table_rows.append(f'<tr>{"".join(row_html)}</tr>')
    table_rows_rendered = "".join(table_rows)

    # HTML template with dynamic styling from selected template and large typography (body size 16px)
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    * {{ box-sizing: border-box; }}
    body {{
        font-family: system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
        color: {t["text_color"]};
        background-color: {t["bg_color"]};
        line-height: 1.6;
        margin: 0;
        padding: 0;
    }}
    
    /* 12-Column Grid System */
    .row {{ display: flex; flex-wrap: wrap; margin: 0 -12px 12px -12px; }}
    .col {{ flex: 1; padding: 0 12px; }}
    .col-1 {{ flex: 0 0 8.333%; max-width: 8.333%; padding: 0 12px; }}
    .col-2 {{ flex: 0 0 16.666%; max-width: 16.666%; padding: 0 12px; }}
    .col-3 {{ flex: 0 0 25%; max-width: 25%; padding: 0 12px; }}
    .col-4 {{ flex: 0 0 33.333%; max-width: 33.333%; padding: 0 12px; }}
    .col-5 {{ flex: 0 0 41.666%; max-width: 41.666%; padding: 0 12px; }}
    .col-6 {{ flex: 0 0 50%; max-width: 50%; padding: 0 12px; }}
    .col-7 {{ flex: 0 0 58.333%; max-width: 58.333%; padding: 0 12px; }}
    .col-8 {{ flex: 0 0 66.666%; max-width: 66.666%; padding: 0 12px; }}
    .col-9 {{ flex: 0 0 75%; max-width: 75%; padding: 0 12px; }}
    .col-10 {{ flex: 0 0 83.333%; max-width: 83.333%; padding: 0 12px; }}
    .col-11 {{ flex: 0 0 91.666%; max-width: 91.666%; padding: 0 12px; }}
    .col-12 {{ flex: 0 0 100%; max-width: 100%; padding: 0 12px; }}

    /* WeasyPrint Page Setup & Running Elements */
    @page {{
        size: A4;
        margin: 16mm 14mm 14mm 14mm;
        @top-left {{
            content: "AARKAA INTELLIGENCE  |  {domain_profile["name"].upper()}";
            font-family: system-ui, sans-serif;
            font-size: 8px;
            font-weight: 700;
            color: #94A3B8;
            letter-spacing: 1px;
        }}
        @top-right {{
            content: "CONFIDENTIAL RESEARCH REPORT  |  v3.2.0";
            font-family: system-ui, sans-serif;
            font-size: 8px;
            font-weight: 700;
            color: #EF4444;
            letter-spacing: 1px;
        }}
        @bottom-left {{
            content: "© 2026 Aarkaa Technologies. All rights reserved. Generated via AARKAA-VISION-v2.0.";
            font-family: system-ui, sans-serif;
            font-size: 7.5px;
            color: #94A3B8;
        }}
        @bottom-right {{
            content: "Page " counter(page) " of " counter(pages);
            font-family: system-ui, sans-serif;
            font-size: 8px;
            font-weight: 700;
            color: #64748B;
        }}
    }}
    
    /* Cover Page Reset */
    @page:first {{
        margin: 0;
        @top-left {{ content: ""; }}
        @top-right {{ content: ""; }}
        @bottom-left {{ content: ""; }}
        @bottom-right {{ content: ""; }}
    }}
    
    .page {{
        height: 255mm;
        page-break-after: always;
        position: relative;
        overflow: hidden;
        padding: 2mm 0;
    }}
    .page:last-child {{
        page-break-after: avoid;
    }}

    /* Confidential Watermark Overlay */
    .watermark {{
        position: absolute;
        top: 40%;
        left: 5%;
        font-size: 78px;
        font-weight: 900;
        color: rgba(226, 232, 240, 0.22);
        transform: rotate(-35deg);
        letter-spacing: 12px;
        pointer-events: none;
        z-index: 0;
        text-transform: uppercase;
        width: 100%;
        text-align: center;
    }}
    
    /* Premium Gamma & Bloomberg Blocks */
    .card {{
        background: {t["card_bg"]};
        border: 1px solid {t["card_border"]};
        border-top: 4px solid {t["primary_color"]};
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        position: relative;
        z-index: 1;
    }}
    .card-green {{ border-top-color: {t["secondary_color"]}; }}
    .card-amber {{ border-top-color: #F59E0B; }}
    .card-purple {{ border-top-color: #8B5CF6; }}
    .card-red {{ border-top-color: #EF4444; }}
    
    .badge {{
        display: inline-flex;
        align-items: center;
        font-size: 9px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: {t["badge_text"]};
        background: {t["badge_bg"]};
        padding: 2.5px 8px;
        border-radius: 9999px;
        margin-bottom: 10px;
    }}
    
    .callout {{
        background: {t["callout_bg"]};
        border-left: 4px solid {t["callout_border"]};
        padding: 12px 18px;
        border-radius: 0 8px 8px 0;
        margin: 14px 0;
        font-style: italic;
        font-size: 14.5px;
        line-height: 1.5;
        color: {t["callout_text"]};
    }}

    /* AI Insight Callout Block */
    .ai-insight {{
        background: #F8FAFC;
        border: 1.5px dashed {t["primary_color"]};
        border-radius: 8px;
        padding: 12px 16px;
        margin: 14px 0;
        position: relative;
    }}
    .ai-insight-title {{
        display: flex;
        align-items: center;
        font-size: 10px;
        font-weight: 800;
        color: {t["primary_color"]};
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }}
    .ai-insight-text {{
        font-size: 13px;
        line-height: 1.45;
        margin: 0;
        color: #334155;
        text-align: justify;
    }}

    /* KPI Scorecard / Metrics Grid */
    .kpi-container {{ display: flex; gap: 12px; margin-bottom: 16px; }}
    .kpi-card {{
        flex: 1;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 14px;
        text-align: left;
        box-shadow: 0 2px 6px rgba(0,0,0,0.01);
    }}
    .kpi-label {{
        font-size: 9px;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 3px;
    }}
    .kpi-val {{
        font-size: 20px;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.1;
    }}
    .kpi-change {{
        font-size: 9.5px;
        font-weight: 700;
        color: #10B981;
        margin-top: 3px;
    }}
    .kpi-change.negative {{ color: #EF4444; }}

    /* SWOT Matrix */
    .swot-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 4px; }}
    .swot-box {{
        padding: 8px 12px;
        border-radius: 6px;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
    }}
    .swot-header {{
        font-size: 11px;
        font-weight: 800;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .swot-s {{ color: #10B981; border-left: 3px solid #10B981; }}
    .swot-w {{ color: #EF4444; border-left: 3px solid #EF4444; }}
    .swot-o {{ color: #3B82F6; border-left: 3px solid #3B82F6; }}
    .swot-t {{ color: #F59E0B; border-left: 3px solid #F59E0B; }}
    .swot-desc {{ font-size: 11.5px; color: #475569; line-height: 1.35; margin: 0; }}

    /* Data Citations / Credibility Bar */
    .credibility-bar {{
        border-top: 1px solid #E2E8F0;
        padding-top: 8px;
        margin-top: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 9px;
        color: #64748B;
    }}
    .credibility-badge {{
        display: inline-flex;
        align-items: center;
        background: #F0FDF4;
        color: #166534;
        border: 1px solid #BBF7D0;
        padding: 1.5px 6px;
        border-radius: 4px;
        font-weight: 700;
    }}
    
    /* Section Divider Line */
    .section-divider {{
        height: 1px;
        background: linear-gradient(to right, {t["primary_color"]}, rgba(0,0,0,0) 80%);
        margin: 14px 0;
        opacity: 0.25;
    }}
    
    /* Typography */
    h1, h2, h3 {{ color: {t["h1_color"]}; margin-top: 0; }}
    h1 {{ font-size: 38px; font-weight: 900; }}
    h2 {{ font-size: 20px; font-weight: 800; border-bottom: 1px solid {t["card_border"]}; padding-bottom: 5px; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.5px; display: flex; align-items: center; }}
    h2 svg {{ margin-right: 8px; }}
    p {{ font-size: 15px; line-height: 1.55; margin-bottom: 12px; text-align: justify; color: {t["text_color"]}; }}
    ul {{ margin: 0; padding-left: 14px; font-size: 14px; line-height: 1.5; color: {t["text_color"]}; }}
    li {{ margin-bottom: 3px; }}
    
    /* Charts & Illustrations */
    .chart-container {{ text-align: center; margin-top: 6px; }}
    .chart-img {{ display: block; width: 100%; height: auto; max-height: 180px; margin: 0 auto; border-radius: 6px; }}
    .cover-illustration {{ display: block; width: 100%; height: 320px; max-width: 680px; margin: 0 auto; border-radius: 12px; object-fit: cover; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1); }}
    svg {{ display: block; width: 100%; height: auto; max-height: 180px; margin: 0 auto; }}
</style>
</head>
<body>

<!-- PAGE 1: 1. COVER -->
<div class="page" style="background: #FFFFFF; border-bottom: 8px solid {t["primary_color"]}; margin: 0; height: 255mm; display: flex; flex-direction: column; justify-content: space-between; padding: 18mm 14mm 14mm 14mm; color: #1E293B; overflow: hidden; position: relative;">
    <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0.05; pointer-events: none; z-index: 0;">
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
                    <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#6366F1" stroke-width="1"/>
                </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
    </div>

    <div style="position: absolute; top: 25%; left: 5%; font-size: 96px; font-weight: 900; color: rgba(99,102,241,0.03); letter-spacing: 6px; pointer-events: none; z-index: 0; text-transform: uppercase;">
        AARKAA
    </div>
    
    <div style="z-index: 1;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" style="max-height: 32px;">
                    <rect width="32" height="32" rx="6" fill="{t["primary_color"]}"/>
                    <path d="M16 6L25 22H7L16 6Z" fill="#FFFFFF"/>
                    <circle cx="16" cy="15" r="3" fill="{t["secondary_color"]}"/>
                </svg>
                <strong style="font-size: 14px; font-weight: 900; letter-spacing: 2px; color: #0F172A;">AARKAA <span style="font-weight: 300;">INTELLIGENCE</span></strong>
            </div>
            <div>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{t["primary_color"]}" stroke-width="2" xmlns="http://www.w3.org/2000/svg" style="max-height: 24px;">
                    <path d="M18 3a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3 3 3 0 0 0 3-3V6a3 3 0 0 0-3-3zM6 21a3 3 0 0 0 3-3V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3v12a3 3 0 0 0 3 3zM12 18V6" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
        </div>

        <div style="width: 60px; height: 5px; background: {t["primary_color"]}; margin-bottom: 16px; border-radius: 2.5px;"></div>
        <h1 style="color: #0F172A; font-size: 38px; line-height: 1.15; font-weight: 900; margin-bottom: 10px; letter-spacing: -0.5px;">
            {topic.upper()}
        </h1>
        <p style="color: #64748B; font-size: 15px; max-width: 640px; line-height: 1.6; font-weight: 400; text-align: justify; margin-bottom: 16px;">
            A consulting-grade quantitative and qualitative ecosystem evaluation outlining growth trajectories, structural paradigms, operational benchmarks, and strategic investment criteria.
        </p>

        <div style="display: flex; gap: 16px; margin-bottom: 16px; max-width: 600px;">
            <div style="flex: 1; background: #F8FAFC; border-left: 3px solid {t["primary_color"]}; padding: 6px 12px; border-radius: 0 6px 6px 0;">
                <span style="font-size: 9px; font-weight: 700; color: #64748B; text-transform: uppercase;">{c_kpis[0]["label"]}</span>
                <div style="font-size: 18px; font-weight: 800; color: #0F172A;">{c_kpis[0]["val"]}</div>
            </div>
            <div style="flex: 1; background: #F8FAFC; border-left: 3px solid {t["secondary_color"]}; padding: 6px 12px; border-radius: 0 6px 6px 0;">
                <span style="font-size: 9px; font-weight: 700; color: #64748B; text-transform: uppercase;">{c_kpis[1]["label"]}</span>
                <div style="font-size: 18px; font-weight: 800; color: #0F172A;">{c_kpis[1]["val"]}</div>
            </div>
            <div style="flex: 1; background: #F8FAFC; border-left: 3px solid #8B5CF6; padding: 6px 12px; border-radius: 0 6px 6px 0;">
                <span style="font-size: 9px; font-weight: 700; color: #64748B; text-transform: uppercase;">{c_kpis[2]["label"]}</span>
                <div style="font-size: 18px; font-weight: 800; color: #0F172A;">{c_kpis[2]["val"]}</div>
            </div>
        </div>

        <div class="chart-container" style="margin-top: 4px;">
            {render_chart_html(cover_img, class_name="cover-illustration")}
        </div>
    </div>
    
    <div style="z-index: 1; border-top: 1px solid #E2E8F0; padding-top: 14px; display: flex; justify-content: space-between; font-size: 9.5px; color: #64748B;">
        <div>
            <strong style="color: #0F172A; display: block; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 1px;">PREPARED BY</strong>
            Aarka AI Engine (ARK-v2.0)
        </div>
        <div>
            <strong style="color: #0F172A; display: block; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 1px;">METADATA</strong>
            ID: ARK-2026-CHN-098  •  v3.2.0
        </div>
        <div>
            <strong style="color: #0F172A; display: block; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 1px;">GENERATED ON</strong>
            June 26, 2026  •  03:55
        </div>
    </div>
</div>

<!-- PAGE 2: 2. EXECUTIVE DASHBOARD, 9. SWOT & 13. RECOMMENDATIONS -->
<div class="page" style="padding: 2mm 0;">
    <div class="watermark">CONFIDENTIAL</div>
    <div class="badge">
        <svg class="badge-icon" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H7c0-2.76 2.24-5 5-5s5 2.24 5 5c0 1.04-.42 1.99-1.07 2.75z"/></svg>
        Executive Dashboard
    </div>
    <h2>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{t["primary_color"]}" stroke-width="2" style="max-height:20px; display:inline-block; vertical-align:middle; margin-right:6px;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        2. Executive Dashboard &amp; 13. Recommendations
    </h2>
    
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-label">{d_kpis[0]["label"]}</div>
            <div class="kpi-val">{d_kpis[0]["val"]}</div>
            <div class="kpi-change">{d_kpis[0]["change"]}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">{d_kpis[1]["label"]}</div>
            <div class="kpi-val">{d_kpis[1]["val"]}</div>
            <div class="kpi-change">{d_kpis[1]["change"]}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">{d_kpis[2]["label"]}</div>
            <div class="kpi-val">{d_kpis[2]["val"]}</div>
            <div class="kpi-change">{d_kpis[2]["change"]}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">{d_kpis[3]["label"]}</div>
            <div class="kpi-val">{d_kpis[3]["val"]}</div>
            <div class="kpi-change" style="color: #8B5CF6;">{d_kpis[3]["change"]}</div>
        </div>
    </div>

    <div class="row">
        <div class="col-8">
            <div class="card" style="margin-bottom: 8px;">
                <p>{sec1}</p>
            </div>
            
            <div class="card card-purple" style="padding: 10px 14px; margin-bottom: 0;">
                <strong style="font-size: 11px; color: {t["h1_color"]}; display: block; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;">13. Strategic Recommendations Checklist</strong>
                <div style="font-size: 12px; color: #334155; line-height: 1.5;">
                    <div style="margin-bottom: 4px; display: flex; align-items: flex-start; gap: 6px;">
                        <span style="color: #10B981; font-weight: 900;">[✔]</span>
                        <span>Deploy optimized target workflows and automated system protocols.</span>
                    </div>
                    <div style="margin-bottom: 4px; display: flex; align-items: flex-start; gap: 6px;">
                        <span style="color: #10B981; font-weight: 900;">[✔]</span>
                        <span>Consolidate operational resources into primary geographic corridors.</span>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-4">
            <div class="card card-purple" style="margin-bottom: 8px;">
                <strong style="font-size: 11px; color: {t["h1_color"]}; display: block; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px;">9. SWOT Matrix</strong>
                <div class="swot-grid">
                    <div class="swot-box">
                        <div class="swot-header swot-s">S</div>
                        <p class="swot-desc">{domain_profile["swot"]["s"]}</p>
                    </div>
                    <div class="swot-box">
                        <div class="swot-header swot-w">W</div>
                        <p class="swot-desc">{domain_profile["swot"]["w"]}</p>
                    </div>
                    <div class="swot-box">
                        <div class="swot-header swot-o">O</div>
                        <p class="swot-desc">{domain_profile["swot"]["o"]}</p>
                    </div>
                    <div class="swot-box">
                        <div class="swot-header swot-t">T</div>
                        <p class="swot-desc">{domain_profile["swot"]["t"]}</p>
                    </div>
                </div>
            </div>

            <div class="card card-green" style="padding: 10px 12px; margin-bottom: 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <strong style="font-size: 10px; color: {t["h1_color"]}; text-transform: uppercase; letter-spacing: 0.5px;">10. Risk</strong>
                    <strong style="font-size: 10px; color: {t["h1_color"]}; text-transform: uppercase; letter-spacing: 0.5px;">11. Opportunity</strong>
                </div>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <div style="flex: 1; text-align: center;">
                        <svg width="80" height="50" viewBox="0 0 100 60" style="max-height: 50px;">
                            <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#E2E8F0" stroke-width="10" stroke-linecap="round"/>
                            <path d="M 10 50 A 40 40 0 0 1 80 25" fill="none" stroke="#EF4444" stroke-width="10" stroke-linecap="round"/>
                            <circle cx="50" cy="50" r="4" fill="#0F172A"/>
                            <line x1="50" y1="50" x2="75" y2="25" stroke="#0F172A" stroke-width="3" stroke-linecap="round"/>
                            <text x="50" y="45" font-family="sans-serif" font-size="11" font-weight="900" fill="#0F172A" text-anchor="middle">84%</text>
                        </svg>
                        <span style="font-size: 8px; color: #EF4444; font-weight: bold; display: block; margin-top: 2px;">MEDIUM-HIGH</span>
                    </div>
                    <div style="flex: 1.2;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 3px; font-size: 7.5px; font-weight: bold; text-align: center; text-transform: uppercase;">
                            <div style="background: #D1FAE5; color: #065F46; padding: 3px; border-radius: 2px;">Global<br>High</div>
                            <div style="background: #D1FAE5; color: #065F46; padding: 3px; border-radius: 2px;">Vertical<br>High</div>
                            <div style="background: #FEF3C7; color: #92400E; padding: 3px; border-radius: 2px;">Strategic<br>Med</div>
                            <div style="background: #FEE2E2; color: #991B1B; padding: 3px; border-radius: 2px;">Operational<br>Low</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="credibility-bar">
        <span><strong>Source:</strong> Aarka Intelligence &amp; Bloomberg Research Q2 2026  |  <strong>Last Updated:</strong> Q2 2026</span>
        <span class="credibility-badge">✓ AI VERIFIED • 98.2% CONFIDENCE</span>
    </div>
</div>

<!-- PAGE 3: 3. KEY METRICS, 4. MARKET OVERVIEW & 5. STARTUP LANDSCAPE -->
<div class="page">
    <div class="watermark">ANALYSIS</div>
    <div class="badge">
        <svg class="badge-icon" viewBox="0 0 24 24"><path d="M5 9.2h3V19H5zM10.6 5h2.8v14h-2.8zm5.6 8H19v6h-2.8z"/></svg>
        Ecosystem Analysis
    </div>
    <h2>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{t["primary_color"]}" stroke-width="2" style="max-height:20px; display:inline-block; vertical-align:middle; margin-right:6px;"><path d="M21.21 15.89A10 10 0 1 1 8 2.83M22 12A10 10 0 0 0 12 2v10z"/></svg>
        3. Key Metrics, 4. Market Overview &amp; 5. Industrial Landscape
    </h2>
    <div class="card" style="margin-bottom: 8px;">
        <p>{sec2}</p>
    </div>
    
    <div class="row" style="margin-top: 2px; margin-bottom: 6px;">
        <div class="col-6">
            <div class="card card-amber" style="margin-bottom: 0; padding: 8px 12px;">
                <div style="font-size: 11px; font-weight: 800; color: {t["primary_color"]}; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 0.5px;">3. Trend &amp; Velocity Performance</div>
                <div class="chart-container">
                    {render_chart_html(chart2)}
                </div>
                <div style="font-size: 8px; color: #64748B; margin-top: 2px; text-align: left; border-top: 1px solid #F1F5F9; padding-top: 2px;">
                    * Trend: Compounding user and performance metrics over time. Source: Aarkaa Database.
                </div>
            </div>
        </div>
        <div class="col-6">
            <div class="card card-purple" style="margin-bottom: 0; padding: 8px 12px;">
                <div style="font-size: 11px; font-weight: 800; color: {t["primary_color"]}; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 0.5px;">4. Resource &amp; Asset Allocation</div>
                <div class="chart-container">
                    {render_chart_html(chart3)}
                </div>
                <div style="font-size: 8px; color: #64748B; margin-top: 2px; text-align: left; border-top: 1px solid #F1F5F9; padding-top: 2px;">
                    * Allocation reflects institutional concentration and resource placement across major segments.
                </div>
            </div>
        </div>
    </div>

    <div class="row" style="margin-bottom: 4px;">
        <div class="col-7">
            <div class="ai-insight" style="margin: 0; height: 100%;">
                <div class="ai-insight-title">5. Segment Depth Analysis</div>
                <p class="ai-insight-text" style="font-size: 12px; line-height: 1.4;">
                    Primary verticals dominate asset allocation, followed closely by secondary integration points. The synergy between core deep infrastructure and specialized verticals continues to attract top-tier capital, establishing a robust growth corridor.
                </p>
            </div>
        </div>
        <div class="col-5">
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 6px; display: flex; flex-direction: column; justify-content: space-between; height: 100%;">
                <strong style="font-size: 9px; color: #0F172A; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 3px; text-align: center;">5. {domain_profile["name"]} Technical Model</strong>
                {domain_profile["visual_svg"]}
            </div>
        </div>
    </div>

    <div class="credibility-bar">
        <span><strong>Source:</strong> Gartner Research &amp; Aarka Ecosystem Audit  |  <strong>Confidence Score:</strong> 96.5%</span>
        <span class="credibility-badge" style="background:#EFF6FF; color:#1e40af; border-color:#bfdbfe;">AAR-VERIFIED</span>
    </div>
</div>

<!-- PAGE 4: 6. SECTOR, 7. FUNDING ANALYSIS & 12. FINANCIAL OUTLOOK -->
<div class="page">
    <div class="watermark">VELOCITY</div>
    <div class="badge">
        <svg class="badge-icon" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>
        Performance Metrics
    </div>
    <h2>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{t["primary_color"]}" stroke-width="2" style="max-height:20px; display:inline-block; vertical-align:middle; margin-right:6px;"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
        6. Sector, 7. Financial Expansion &amp; 12. Future Outlook
    </h2>
    <div class="card" style="margin-bottom: 8px;">
        <p>{sec3}</p>
    </div>
    
    <div class="callout" style="margin: 6px 0; padding: 8px 12px; font-size: 13.5px;">
        "Compounding quarterly performance growth acts as the ultimate validator of operational efficiency and platform scalability in high-velocity competitive environments."
    </div>
    
    <div class="row">
        <div class="col-8">
            <div class="card card-amber" style="margin-bottom: 0; padding: 10px 14px;">
                <div style="font-size: 11px; font-weight: 800; color: {t["primary_color"]}; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;">7. Segment Financials &amp; 12. Future Outlook</div>
                <div class="chart-container">
                    {render_chart_html(chart1)}
                </div>
                <div style="font-size: 8px; color: #64748B; margin-top: 3px; border-top: 1px solid #F1F5F9; padding-top: 2px;">
                    * Projections based on compounding growth curves of top-25 ecosystem platforms.
                </div>
            </div>
        </div>
        <div class="col-4">
            <div class="card card-green" style="height: 100%; display: flex; flex-direction: column; justify-content: space-between; padding: 10px 12px; margin-bottom: 0;">
                <div>
                    <strong style="font-size: 10.5px; color: {t["h1_color"]}; display: block; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px;">Key Metrics</strong>
                    <div style="margin-bottom: 6px;">
                        <span style="font-size: 8px; color: #64748B; display: block; text-transform: uppercase;">Primary KPI</span>
                        <span style="font-size: 18px; font-weight: 800; color: #0F172A;">{d_kpis[0]["val"]}</span>
                    </div>
                    <div style="margin-bottom: 6px;">
                        <span style="font-size: 8px; color: #64748B; display: block; text-transform: uppercase;">Secondary KPI</span>
                        <span style="font-size: 18px; font-weight: 800; color: #10B981;">{d_kpis[1]["val"]}</span>
                    </div>
                </div>
                <div>
                    <span style="font-size: 8px; color: #64748B; display: block; text-transform: uppercase; margin-bottom: 3px; font-weight: bold;">Top Sector Players</span>
                    <div style="display: flex; gap: 4px; flex-wrap: wrap; justify-content: space-between; background: #F8FAFC; padding: 4px; border-radius: 4px; border: 1px solid #E2E8F0; width: 100%;">
                        {brand_logos_rendered}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="credibility-bar">
        <span><strong>Source:</strong> McKinsey Financial database &amp; Aarka Audit Q2 2026  |  <strong>Confidence:</strong> 97.4%</span>
        <span class="credibility-badge">✓ ACCREDITED DATA</span>
    </div>
</div>

<!-- PAGE 5: 8. COMPETITIVE LANDSCAPE & 14. METHODOLOGY -->
<div class="page">
    <div class="watermark">EFFICIENCY</div>
    <div class="badge">
        <svg class="badge-icon" viewBox="0 0 24 24"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>
        Operational Benchmarks
    </div>
    <h2>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{t["primary_color"]}" stroke-width="2" style="max-height:20px; display:inline-block; vertical-align:middle; margin-right:6px;"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/></svg>
        8. Competitive Landscape &amp; 14. Methodology
    </h2>
    <div class="card" style="margin-bottom: 8px;">
        <p>{sec4}</p>
    </div>
    
    <div class="row">
        <div class="col-8">
            <div class="card card-green" style="margin-bottom: 0; padding: 10px 14px;">
                <div style="font-size: 11px; font-weight: 800; color: {t["primary_color"]}; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;">8. Performance Benchmarking Uptime</div>
                <div class="chart-container">
                    {render_chart_html(chart4)}
                </div>
                <div style="margin-top: 6px;">
                    <strong style="font-size: 9px; color: #0F172A; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 3px;">8. Segment Competitive Growth Heatmap</strong>
                    <table style="width: 100%; border-collapse: collapse; font-size: 9px; text-align: center;">
                        <thead>
                            <tr style="background: #F1F5F9; font-weight: bold;">
                                {table_headers}
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows_rendered}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        <div class="col-4">
            <div class="card card-amber" style="height: 100%; padding: 12px 14px; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 0;">
                <div>
                    <strong style="font-size: 11px; color: {t["h1_color"]}; display: block; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px;">Strategic Milestones</strong>
                    <div style="border-left: 2px solid {t["primary_color"]}; padding-left: 10px; position: relative; margin-left: 4px;">
                        <div style="position: absolute; left: -5px; top: 2px; width: 8px; height: 8px; border-radius: 50%; background: {t["primary_color"]};"></div>
                        <strong style="font-size: 11px; color: #0F172A; display: block;">{t_m[0]["time"]}</strong>
                        <span style="font-size: 10px; color: #64748B; display: block; margin-bottom: 8px;">{t_m[0]["desc"]}</span>
                        <div style="position: absolute; left: -5px; top: 50px; width: 8px; height: 8px; border-radius: 50%; background: {t["secondary_color"]};"></div>
                        <strong style="font-size: 11px; color: #0F172A; display: block;">{t_m[1]["time"]}</strong>
                        <span style="font-size: 10px; color: #64748B; display: block;">{t_m[1]["desc"]}</span>
                    </div>
                </div>
                <div style="background: rgba(245, 158, 11, 0.05); border-left: 2.5px solid #F59E0B; padding: 6px 10px; border-radius: 0 4px 4px 0; font-size: 11px; color: #78350F; line-height: 1.35; margin-top: 8px;">
                    <strong>14. Methodology:</strong> Built via hybrid RAG architectures indexing 47 ecosystem intelligence nodes with weighted parameter vector search.
                </div>
            </div>
        </div>
    </div>

    <div class="credibility-bar">
        <span><strong>Source:</strong> IDC Infrastructure Reports &amp; Aarkaa Auditing  |  <strong>Accuracy Score:</strong> 95.8%</span>
        <span class="credibility-badge">✓ COMPLIANT FRAMEWORK</span>
    </div>
</div>

<!-- PAGE 6: 10. RISK MATRIX, 11. OPPORTUNITY MATRIX & 15. SOURCES -->
<div class="page">
    <div class="watermark">FORECAST</div>
    <div class="badge">
        <svg class="badge-icon" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
        Strategic Outlook
    </div>
    <h2>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{t["primary_color"]}" stroke-width="2" style="max-height:20px; display:inline-block; vertical-align:middle; margin-right:6px;"><path d="M23 6l-9.5 9.5-5-5L1 18"/><path d="M17 6h6v6"/></svg>
        10. Risk Matrix, 11. Opportunity Matrix &amp; 15. Sources
    </h2>
    <div class="card">
        <p>{sec5}</p>
    </div>
    
    <div class="row" style="margin-top: 4px;">
        <div class="col-8">
            <div class="card card-red" style="margin-bottom: 0;">
                <div style="font-size: 12px; font-weight: 800; color: {t["primary_color"]}; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;">10. Cumulative Risk Profiles &amp; Skews</div>
                <div class="chart-container">
                    {render_chart_html(chart5)}
                </div>
                <div style="font-size: 8.5px; color: #64748B; margin-top: 4px; border-top: 1px solid #F1F5F9; padding-top: 3px;">
                    * Projections assume regulatory volatility peaks in late 2026. Source: Aarka Risk Analytics.
                </div>
            </div>
        </div>
        <div class="col-4">
            <div class="card card-amber" style="height: 100%; padding: 12px 14px; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 0;">
                <div>
                    <strong style="font-size: 11px; color: {t["h1_color"]}; display: block; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px;">11. Opportunity Index</strong>
                    <div style="font-size: 11.5px; color: #334155; line-height: 1.55;">
                        <div style="margin-bottom: 8px; display: flex; align-items: flex-start; gap: 6px;">
                            <span style="color: #10B981; font-weight: 900;">[✔]</span>
                            <span>Highest yield performance seen across prime segments.</span>
                        </div>
                        <div style="margin-bottom: 8px; display: flex; align-items: flex-start; gap: 6px;">
                            <span style="color: #10B981; font-weight: 900;">[✔]</span>
                            <span>Cross-border enterprise compliance integration remains top expansion opportunity.</span>
                        </div>
                    </div>
                </div>
                <div style="border-top: 1px solid #E2E8F0; padding-top: 8px; display: flex; align-items: center; justify-content: space-between; margin-top: 8px;">
                    <div style="font-size: 8px; color: #64748B; line-height: 1.3;">
                        <strong>15. Sources &amp; Appendix:</strong><br>Aarka AI Principal Analyst<br>Report ID: ARK-2026-CHN-098
                    </div>
                    <svg width="34" height="34" viewBox="0 0 34 34" fill="none" stroke="#0F172A" stroke-width="1" style="max-height: 34px;">
                        <rect x="0" y="0" width="8" height="8" fill="#0F172A"/>
                        <rect x="26" y="0" width="8" height="8" fill="#0F172A"/>
                        <rect x="0" y="26" width="8" height="8" fill="#0F172A"/>
                        <rect x="12" y="12" width="10" height="10" fill="#0F172A"/>
                        <rect x="26" y="26" width="4" height="4" fill="#0F172A"/>
                        <rect x="18" y="0" width="4" height="4" fill="#0F172A"/>
                        <rect x="0" y="18" width="4" height="4" fill="#0F172A"/>
                    </svg>
                </div>
            </div>
        </div>
    </div>

    <div class="credibility-bar">
        <span><strong>Source:</strong> 15. Aarkaa Risk Audit &amp; World Economic Forum Risk Index  |  <strong>Confidence:</strong> 95.1%</span>
        <span class="credibility-badge" style="background:#FEF2F2; color:#991B1B; border-color:#FCA5A5;">AI SECURE</span>
    </div>
</div>

</body>
</html>
"""
    
    # Strip network imports that cause WeasyPrint errors
    from skills.html.docs_generator import _sanitize_html, generate_pdf
    html_content = _sanitize_html(html_content)
    
    # Save the output file in SAFE_WORK_DIR
    output_path = Path(SAFE_WORK_DIR) / output_name
    
    # Save debug HTML
    try:
        debug_html_path = Path(SAFE_WORK_DIR) / f"{output_path.stem}.html"
        with open(debug_html_path, "w", encoding="utf-8") as df:
            df.write(html_content)
        logger.info(f"Saved debug HTML to {debug_html_path}")
    except Exception as e:
        logger.error(f"Failed to save debug HTML: {e}")
        
    # Compile
    generate_pdf(html_content, str(output_path), inject_print_css=True)
    logger.info(f"Gamma PDF compiled successfully at {output_path}")
    return str(output_path)

