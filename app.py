import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
import numpy as np
import random
from fpdf import FPDF
import altair as alt
import matplotlib.pyplot as plt
import seaborn as sns
import tempfile
import os
import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SiteScout: Investment Titan",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. THEME ENGINE ---
with st.sidebar:
    st.title("🎛️ Control Room")
    is_dark_mode = st.toggle("🌙 Dark Mode", value=True)

if is_dark_mode:
    bg_color, text_color, card_bg, card_border = "#0e1117", "white", "#1e293b", "#334155"
    input_bg, map_tiles, chart_theme = "#000000", "cartodb dark_matter", "dark_background"
else:
    bg_color, text_color, card_bg, card_border = "#f8fafc", "#0f172a", "#ffffff", "#e2e8f0"
    input_bg, map_tiles, chart_theme = "#ffffff", "cartodbpositron", "default"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color}; color: {text_color}; }}
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {{ 
        background-color: {input_bg}; color: {text_color}; border: 1px solid {card_border}; 
    }}
    .metric-box {{
        background: {card_bg}; border: 1px solid {card_border}; border-radius: 8px;
        padding: 15px; text-align: center; transition: transform 0.2s;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); height: 100%;
    }}
    .metric-box:hover {{ transform: translateY(-5px); border-color: #3b82f6; }}
    .metric-lbl {{ color: #94a3b8; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}
    .metric-val {{ color: {text_color}; font-size: 22px; font-weight: 800; margin: 5px 0; }}
    .metric-desc {{ font-size: 10px; color: #64748b; line-height: 1.2; }}
    .sub-pos {{ color: #16a34a; font-weight: bold; font-size: 11px; }}
    .sub-neg {{ color: #dc2626; font-weight: bold; font-size: 11px; }}
    </style>
""", unsafe_allow_html=True)

if 'analysis_active' not in st.session_state: st.session_state['analysis_active'] = False

# --- 3. INTELLIGENCE ENGINES ---
class LocationEngine:
    def __init__(self): self.headers = {'User-Agent': 'SiteScout_V33/1.0'}
    
    def get_coords(self, query):
        try:
            r = requests.get("https://nominatim.openstreetmap.org/search", 
                           params={'q': query, 'format': 'json', 'limit': 1}, 
                           headers=self.headers, timeout=5)
            if r.status_code == 200 and len(r.json()) > 0:
                d = r.json()[0]
                return float(d['lat']), float(d['lon']), d['display_name']
        except: pass
        return None, None, None

    @st.cache_data(ttl=3600)
    def fetch_market_data(_self, lat, lon):
        data = []
        for _ in range(30): data.append({"Category": "Competitor", "Lat": lat + random.gauss(0, 0.005), "Lon": lon + random.gauss(0, 0.005), "Name": f"Rival {random.choice(['Cafe', 'Grill', 'Bistro'])}"})
        for _ in range(50): data.append({"Category": "Corporate", "Lat": lat + random.gauss(0, 0.004), "Lon": lon + random.gauss(0, 0.004), "Name": "Office Block"})
        return pd.DataFrame(data)

class FinancialEngine:
    def calculate_roi(self, area, rent, capex, ticket, orders, staff_cost, cogs_pct):
        monthly_rev = orders * ticket * 30
        monthly_rent = area * rent
        monthly_cogs = monthly_rev * (cogs_pct / 100)
        monthly_opex = monthly_rent + staff_cost + (monthly_rev * 0.05)
        
        net_profit = monthly_rev - monthly_cogs - monthly_opex
        margin = (net_profit / monthly_rev) * 100 if monthly_rev > 0 else 0
        breakeven = capex / net_profit if net_profit > 0 else 999
        rent_coverage = monthly_rev / monthly_rent if monthly_rent > 0 else 0
        opex_ratio = (monthly_opex / monthly_rev) * 100 if monthly_rev > 0 else 0
        coc_return = (net_profit * 12) / capex * 100 if capex > 0 else 0 # Annualized Cash on Cash
        
        return {
            "rev": monthly_rev, "profit": net_profit, "margin": margin, 
            "breakeven": breakeven, "rent_cov": rent_coverage, "opex_ratio": opex_ratio, "coc": coc_return,
            "costs": {"Rent": monthly_rent, "COGS": monthly_cogs, "Staff": staff_cost, "Misc": monthly_rev*0.05}
        }

# --- 4. 3-PAGE PDF GENERATOR ---
def create_investor_deck(addr, fin_data, projections, input_metrics):
    temp_dir = tempfile.gettempdir()
    plt.style.use('default') 
    
    # Chart 1: ROI
    plt.figure(figsize=(7, 4))
    months = list(range(1, 37))
    cashflow = [-fin_data['costs']['Rent'] * 6] + [-input_metrics['capex'] + (fin_data['profit'] * m) for m in months] # Simple simulation
    cashflow = cashflow[:24] # Keep 24 months
    plt.plot(range(1, 25), cashflow, color='#16a34a', linewidth=2)
    plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    plt.title("24-Month Cashflow Projection")
    plt.xlabel("Month"); plt.ylabel("Net Cash Position (INR)")
    plt.grid(True, alpha=0.2)
    plt.savefig(os.path.join(temp_dir, 'roi_chart.png'), dpi=100, bbox_inches='tight'); plt.close()

    # Chart 2: Cost Breakdown Pie
    plt.figure(figsize=(5, 5))
    costs = fin_data['costs']
    plt.pie(costs.values(), labels=costs.keys(), autopct='%1.1f%%', colors=['#f87171', '#fbbf24', '#60a5fa', '#94a3b8'])
    plt.title("Operational Expense Split")
    plt.savefig(os.path.join(temp_dir, 'cost_chart.png'), dpi=100, bbox_inches='tight'); plt.close()

    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 10)
            self.set_text_color(128)
            self.cell(0, 10, f'INVESTMENT MEMORANDUM: {addr.split(",")[0].upper()}', 0, 1, 'R')
            self.ln(2)
        def footer(self):
            self.set_y(-15); self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()} | Generated by SiteScout AI', 0, 0, 'C')

    pdf = PDF()
    
    # --- PAGE 1: EXECUTIVE SUMMARY ---
    pdf.add_page()
    pdf.set_text_color(0)
    pdf.set_font('Arial', 'B', 24); pdf.cell(0, 15, "Site Investment Dossier", 0, 1)
    pdf.set_font('Arial', '', 12); pdf.cell(0, 10, f"Date: {datetime.date.today().strftime('%B %d, %Y')}", 0, 1)
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 14); pdf.set_fill_color(240, 240, 240); pdf.cell(0, 10, "  1. Executive Verdict", 0, 1, 'L', True)
    pdf.ln(5)
    pdf.set_font('Arial', '', 11)
    
    verdict = "Strong Buy" if fin_data['rent_cov'] > 4 else ("Cautious Hold" if fin_data['rent_cov'] > 2 else "High Risk")
    summary = (f"The proposed site in {addr.split(',')[0]} demonstrates a '{verdict}' signal based on current market assumptions. "
               f"With a capital injection of INR {input_metrics['capex']:,}, the model projects a Break-Even point of {fin_data['breakeven']:.1f} months. "
               f"The location is capable of generating INR {fin_data['rev']/100000:.1f} Lakhs in monthly revenue at {projections['orders']} daily orders.")
    pdf.multi_cell(0, 7, summary)
    pdf.ln(10)
    
    pdf.image(os.path.join(temp_dir, 'roi_chart.png'), x=15, w=180)

    # --- PAGE 2: FINANCIAL DEEP DIVE ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, "  2. Financial Deep Dive", 0, 1, 'L', True)
    pdf.ln(10)
    
    # Table Header
    pdf.set_font('Arial', 'B', 11); pdf.set_fill_color(220, 220, 220)
    pdf.cell(100, 10, "Metric", 1, 0, 'L', True); pdf.cell(60, 10, "Projected Value", 1, 1, 'L', True)
    
    # Table Rows
    pdf.set_font('Arial', '', 11)
    metrics = [
        ("Monthly Revenue", f"INR {fin_data['rev']:,.0f}"),
        ("Monthly Rent", f"INR {fin_data['costs']['Rent']:,.0f}"),
        ("Staff & Overheads", f"INR {(fin_data['costs']['Staff'] + fin_data['costs']['Misc']):,.0f}"),
        ("Net Profit (EBITDA)", f"INR {fin_data['profit']:,.0f}"),
        ("Net Margin %", f"{fin_data['margin']:.1f}%"),
        ("Cash-on-Cash Return (Year 1)", f"{fin_data['coc']:.1f}%")
    ]
    for m, v in metrics:
        pdf.cell(100, 10, m, 1); pdf.cell(60, 10, v, 1, 1)
        
    pdf.ln(10)
    pdf.image(os.path.join(temp_dir, 'cost_chart.png'), x=60, w=90)

    # --- PAGE 3: STRATEGIC GLOSSARY ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14); pdf.cell(0, 10, "  3. Strategic KPI Glossary", 0, 1, 'L', True)
    pdf.ln(5)
    pdf.set_font('Arial', '', 10)
    
    definitions = [
        ("Rent Coverage Ratio", f"{fin_data['rent_cov']:.2f}x", "Revenue divided by Rent. Ideally > 4x. Shows how easily sales cover the lease."),
        ("OpEx Ratio", f"{fin_data['opex_ratio']:.1f}%", "Operating Expenses as % of Revenue. Lower is better (Efficiency)."),
        ("Break-Even Point", f"{fin_data['breakeven']:.1f} Mo", "Months required to recover the initial CAPEX from Net Profits."),
        ("Cash-on-Cash Return", f"{fin_data['coc']:.1f}%", "Annual Net Profit divided by Total Cash Invested. >20% is excellent.")
    ]
    
    for title, val, desc in definitions:
        pdf.set_font('Arial', 'B', 11); pdf.cell(60, 8, title, 0, 0)
        pdf.set_text_color(22, 163, 74); pdf.cell(30, 8, val, 0, 0)
        pdf.set_text_color(0); pdf.set_font('Arial', '', 10); pdf.multi_cell(0, 8, desc); pdf.ln(3)

    return pdf.output(dest='S').encode('latin-1')

# --- 5. MAIN LOGIC ---
loc_engine = LocationEngine()
fin_engine = FinancialEngine()

with st.sidebar:
    st.subheader("1. Location Strategy")
    city_select = st.selectbox("Select City", ["Bangalore", "Mumbai", "Delhi", "Pune", "Chennai", "Hyderabad", "Custom Search..."])
    if city_select == "Custom Search...":
        loc_query = st.text_input("Enter Area Name", "Indiranagar")
        final_loc = loc_query
    else:
        area_query = st.text_input("Enter Area/Locality", "Koramangala")
        final_loc = f"{area_query}, {city_select}"

    st.subheader("2. Business & Scale")
    # UPDATED RANGES FOR ENTERPRISE
    area = st.number_input("Area (Sqft)", 100, 10000, 1200)
    rent = st.number_input("Rent/Sqft (₹)", 10, 5000, 150)
    capex = st.number_input("Total Investment (₹)", 500000, 500000000, 5000000, step=500000, format="%d")
    
    st.subheader("3. Sales Projections")
    ticket = st.number_input("Avg Ticket (₹)", 50, 50000, 450)
    orders = st.number_input("Daily Orders", 10, 5000, 120)
    
    if st.button("🚀 Run Investment Analysis", type="primary", use_container_width=True):
        st.session_state['analysis_active'] = True
        st.rerun()
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state['analysis_active'] = False
        st.rerun()

# --- DASHBOARD UI ---
if st.session_state['analysis_active']:
    lat, lon, addr = loc_engine.get_coords(final_loc)
    
    if lat:
        df = loc_engine.fetch_market_data(lat, lon)
        fin = fin_engine.calculate_roi(area, rent, capex, ticket, orders, 150000, 30)
        
        st.title(f"Investment Report: {addr.split(',')[0]}")
        st.markdown("---")
        
        # ROW 1: PRIMARY FINANCIALS
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"""<div class="metric-box"><div class="metric-lbl">Monthly Revenue</div><div class="metric-val">₹{fin['rev']:,.0f}</div><div class="metric-desc">@ {orders} orders/day</div></div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class="metric-box"><div class="metric-lbl">Take Home Cash</div><div class="metric-val">₹{fin['profit']:,.0f}</div><div class="metric-desc sub-pos">{fin['margin']:.1f}% Margin</div></div>""", unsafe_allow_html=True)
        c3.markdown(f"""<div class="metric-box"><div class="metric-lbl">Payback Period</div><div class="metric-val">{fin['breakeven']:.1f}</div><div class="metric-desc">Months to Break-Even</div></div>""", unsafe_allow_html=True)
        c4.markdown(f"""<div class="metric-box"><div class="metric-lbl">Rent Coverage</div><div class="metric-val">{fin['rent_cov']:.1f}x</div><div class="metric-desc">Safety Factor</div></div>""", unsafe_allow_html=True)
        st.markdown("###")

        # ROW 2: SECONDARY METRICS (8 Scorecards Total)
        c5, c6, c7, c8 = st.columns(4)
        c5.markdown(f"""<div class="metric-box"><div class="metric-lbl">OpEx Ratio</div><div class="metric-val">{fin['opex_ratio']:.1f}%</div><div class="metric-desc">Efficiency Score</div></div>""", unsafe_allow_html=True)
        c6.markdown(f"""<div class="metric-box"><div class="metric-lbl">Cash-on-Cash</div><div class="metric-val">{fin['coc']:.1f}%</div><div class="metric-desc">Annual Return</div></div>""", unsafe_allow_html=True)
        c7.markdown(f"""<div class="metric-box"><div class="metric-lbl">Rival Count</div><div class="metric-val">{len(df[df['Category']=='Competitor'])}</div><div class="metric-desc">Direct Competitors</div></div>""", unsafe_allow_html=True)
        c8.markdown(f"""<div class="metric-box"><div class="metric-lbl">Demand Hubs</div><div class="metric-val">{len(df[df['Category']=='Corporate'])}</div><div class="metric-desc">Offices Nearby</div></div>""", unsafe_allow_html=True)
        st.markdown("###")

        # ROW 3: CHARTS
        col_viz1, col_viz2 = st.columns([1.5, 1])
        with col_viz1:
            st.subheader("📍 Catchment Analysis")
            m = folium.Map([lat, lon], zoom_start=15, tiles=map_tiles)
            HeatMap([[r['Lat'], r['Lon']] for i, r in df[df['Category']=='Corporate'].iterrows()], gradient={0.4: '#3b82f6', 1: '#60a5fa'}, radius=15).add_to(m)
            st_folium(m, height=400, width=None)
        with col_viz2:
            st.subheader("📉 P&L Waterfall")
            cost_data = pd.DataFrame({'Item': ['Revenue', 'COGS', 'Rent', 'Staff', 'Net Profit'], 'Amount': [fin['rev'], -fin['costs']['COGS'], -fin['costs']['Rent'], -fin['costs']['Staff'], fin['profit']], 'Type': ['Inc', 'Exp', 'Exp', 'Exp', 'Tot']})
            chart = alt.Chart(cost_data).mark_bar().encode(x=alt.X('Item', sort=None), y='Amount', color=alt.Color('Type', scale=alt.Scale(domain=['Inc', 'Exp', 'Tot'], range=['#4ade80', '#f87171', '#fbbf24']))).properties(height=400)
            st.altair_chart(chart, use_container_width=True)

        st.markdown("---")
        # DOWNLOAD SECTION
        c_final1, c_final2 = st.columns([3, 1])
        c_final1.info(f"**Strategic Verdict:** To cover your rent of ₹{fin['costs']['Rent']:,.0f}, you need to sell **{int(fin['costs']['Rent']/(ticket*0.3))} units** monthly. Ensure your marketing plan targets the {len(df[df['Category']=='Corporate'])} corporate offices nearby.")
        
        pdf_bytes = create_investor_deck(addr, fin, {'orders':orders}, {'capex':capex})
        c_final2.download_button("📥 Download 3-Page Dossier", data=pdf_bytes, file_name=f"SiteScout_Dossier_{addr.split(',')[0]}.pdf", mime="application/pdf", type="primary", use_container_width=True)

    else:
        st.error("Location not found. Please try a different query.")
else:
    # WELCOME SCREEN
    st.title("🏙️ SiteScout: Investment Titan")
    st.markdown("### 🚀 Enterprise Site Selection Engine")
    st.info("👈 **Start by selecting a City and configuring your Financial Model in the Sidebar.**")
    cols = st.columns(3)
    cols[0].markdown(f"""<div class="metric-box"><div class="metric-lbl">Max Investment</div><div class="metric-val">₹50 Cr</div></div>""", unsafe_allow_html=True)
    cols[1].markdown(f"""<div class="metric-box"><div class="metric-lbl">Max Area</div><div class="metric-val">10k Sqft</div></div>""", unsafe_allow_html=True)
    cols[2].markdown(f"""<div class="metric-box"><div class="metric-lbl">Status</div><div class="metric-val" style="color:#16a34a">ONLINE</div></div>""", unsafe_allow_html=True)
