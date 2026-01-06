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

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SiteScout: Investment Commander",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. THEME ENGINE (LIGHT / DARK TOGGLE) ---
# We use a toggle in the sidebar to control the visual stack
with st.sidebar:
    st.title("🎛️ Control Room")
    is_dark_mode = st.toggle("🌙 Dark Mode", value=True)

# Define Color Palettes
if is_dark_mode:
    # DARK THEME (COMMANDER)
    bg_color = "#0e1117"
    text_color = "white"
    card_bg = "#1e293b"
    card_border = "#334155"
    input_bg = "#000000" # Requested: Pure Black Inputs
    map_tiles = "cartodb dark_matter"
    chart_theme = "dark_background"
    
else:
    # LIGHT THEME (BOARDROOM)
    bg_color = "#f8fafc"
    text_color = "#0f172a"
    card_bg = "#ffffff"
    card_border = "#e2e8f0"
    input_bg = "#ffffff"
    map_tiles = "cartodbpositron"
    chart_theme = "default"

# Inject Dynamic CSS
st.markdown(f"""
    <style>
    /* Global App Background */
    .stApp {{ background-color: {bg_color}; color: {text_color}; }}
    
    /* Inputs (Location Strategy -> Black in Dark Mode) */
    .stTextInput>div>div>input {{ 
        background-color: {input_bg}; 
        color: {text_color}; 
        border: 1px solid {card_border};
    }}
    .stNumberInput>div>div>input {{
        background-color: {input_bg}; 
        color: {text_color};
        border: 1px solid {card_border};
    }}
    .stSelectbox>div>div>div {{
        background-color: {input_bg};
        color: {text_color};
    }}
    
    /* Metrics Cards */
    .metric-box {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        transition: transform 0.2s;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}
    .metric-box:hover {{ transform: translateY(-5px); border-color: #3b82f6; }}
    
    /* Typography */
    .metric-lbl {{ color: #94a3b8; font-size: 12px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; }}
    .metric-val {{ color: {text_color}; font-size: 28px; font-weight: 800; margin: 8px 0; }}
    .metric-sub {{ font-size: 11px; font-weight: 600; padding: 4px 8px; border-radius: 4px; display: inline-block; }}
    
    /* Headers */
    h1, h2, h3 {{ color: {text_color} !important; }}
    p, li {{ color: {text_color}; }}
    
    /* Tags */
    .sub-pos {{ background: rgba(34, 197, 94, 0.2); color: #16a34a; }}
    .sub-neg {{ background: rgba(239, 68, 68, 0.2); color: #dc2626; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'analysis_active' not in st.session_state:
    st.session_state['analysis_active'] = False

# --- 4. INTELLIGENCE ENGINES ---
class LocationEngine:
    def __init__(self):
        self.headers = {'User-Agent': 'SiteScout_V32/1.0'}
    
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
        # Simulate Data Points
        for _ in range(30): 
            data.append({"Category": "Competitor", "Lat": lat + random.gauss(0, 0.005), "Lon": lon + random.gauss(0, 0.005), "Name": f"Rival {random.choice(['Cafe', 'Bistro', 'Grill'])} {random.randint(1,99)}"})
        for _ in range(40): 
            data.append({"Category": "Corporate", "Lat": lat + random.gauss(0, 0.004), "Lon": lon + random.gauss(0, 0.004), "Name": "Corporate Office"})
        for _ in range(15): 
            data.append({"Category": "Premium", "Lat": lat + random.gauss(0, 0.006), "Lon": lon + random.gauss(0, 0.006), "Name": "Premium Anchor"})
        
        df = pd.DataFrame(data)
        df['Dist'] = np.sqrt((df['Lat']-lat)**2 + (df['Lon']-lon)**2) * 111
        return df

class FinancialEngine:
    def calculate_roi(self, area_sqft, rent_psf, capex, avg_ticket, daily_orders, staff_cost, cogs_pct):
        monthly_revenue = daily_orders * avg_ticket * 30
        monthly_rent = area_sqft * rent_psf
        monthly_cogs = monthly_revenue * (cogs_pct / 100)
        monthly_opex = monthly_rent + staff_cost + (monthly_revenue * 0.05)
        
        net_profit = monthly_revenue - monthly_cogs - monthly_opex
        margin = (net_profit / monthly_revenue) * 100 if monthly_revenue > 0 else 0
        breakeven_months = capex / net_profit if net_profit > 0 else 999
        
        return {
            "rev": monthly_revenue,
            "profit": net_profit,
            "margin": margin,
            "breakeven": breakeven_months,
            "costs": {"Rent": monthly_rent, "COGS": monthly_cogs, "Staff": staff_cost, "Misc": monthly_revenue*0.05}
        }

# --- 5. PDF GENERATOR ---
def create_investor_deck(addr, market_df, fin_data, projections):
    temp_dir = tempfile.gettempdir()
    
    # We always use a WHITE background for PDFs because printing black ink is bad
    plt.style.use('default') 
    
    plt.figure(figsize=(7, 4))
    months = list(range(1, 25))
    cumulative_cashflow = [-fin_data['capex'] + (fin_data['profit'] * m) for m in months]
    plt.plot(months, cumulative_cashflow, color='#16a34a', linewidth=2)
    plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    plt.title("24-Month ROI Projection")
    plt.grid(True, alpha=0.2)
    plt.xlabel("Months")
    plt.ylabel("Cashflow")
    plt.savefig(os.path.join(temp_dir, 'roi_chart.png'), dpi=100, bbox_inches='tight')
    plt.close()

    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.set_text_color(150)
            self.cell(0, 10, f'CONFIDENTIAL: INVESTMENT MEMO - {addr.split(",")[0]}', 0, 1, 'R')
            self.ln(5)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 24)
    pdf.set_text_color(0)
    pdf.cell(0, 20, "Site Feasibility & Financial Model", 0, 1, 'L')
    
    pdf.set_font('Arial', '', 11)
    summary = f"Location Analysis for {addr.split(',')[0]}.\n\nBased on the input capital of INR {fin_data['capex']:,} and projected daily footfall of {projections['orders']} pax, this site is projected to generate INR {fin_data['rev']:,.0f} in monthly revenue. The estimated break-even period is {fin_data['breakeven']:.1f} months."
    pdf.multi_cell(0, 8, summary)
    pdf.ln(10)

    pdf.image(os.path.join(temp_dir, 'roi_chart.png'), x=10, w=190)
    return pdf.output(dest='S').encode('latin-1')

# --- 6. APP LAYOUT & SIDEBAR ---
loc_engine = LocationEngine()
fin_engine = FinancialEngine()

with st.sidebar:
    st.subheader("1. Location Strategy")
    # These inputs will be Black in Dark Mode, White in Light Mode via CSS
    loc_input = st.text_input("Search Market", "Indiranagar, Bangalore")
    
    st.subheader("2. Business Assumptions")
    biz_type = st.selectbox("Business Model", ["Premium Cafe", "QSR / Fast Food", "Fine Dining", "Retail Store"])
    col_s1, col_s2 = st.columns(2)
    area = col_s1.number_input("Area (Sqft)", 500, 5000, 1200)
    rent = col_s2.number_input("Rent/Sqft (₹)", 50, 500, 150)
    capex = st.number_input("Total Investment (₹)", 1000000, 50000000, 2500000, step=100000)
    
    st.subheader("3. Revenue Drivers")
    col_s3, col_s4 = st.columns(2)
    ticket = col_s3.number_input("Avg Ticket (₹)", 100, 5000, 450)
    orders = col_s4.number_input("Daily Orders", 10, 1000, 85)
    
    if st.button("🚀 Run Investment Analysis", type="primary", use_container_width=True):
        st.session_state['analysis_active'] = True
        st.rerun()

    if st.button("🔄 Reset Dashboard", use_container_width=True):
        st.session_state['analysis_active'] = False
        st.rerun()

# --- MAIN SCREEN ---
if not st.session_state['analysis_active']:
    # WELCOME SCREEN
    st.title("🏙️ SiteScout: Investment Commander")
    st.markdown("### Ready to Analyze?")
    st.info("👈 **Configure your business model in the Sidebar and click 'Run Investment Analysis'.**")
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"""<div class="metric-box"><div class="metric-lbl">System Status</div><div class="metric-val" style="color:#16a34a">ONLINE</div></div>""", unsafe_allow_html=True)
    c2.markdown(f"""<div class="metric-box"><div class="metric-lbl">Financial Engine</div><div class="metric-val" style="color:#3b82f6">READY</div></div>""", unsafe_allow_html=True)
    c3.markdown(f"""<div class="metric-box"><div class="metric-lbl">Market Data</div><div class="metric-val" style="color:#facc15">CONNECTED</div></div>""", unsafe_allow_html=True)

else:
    # ANALYSIS DASHBOARD
    lat, lon, addr = loc_engine.get_coords(loc_input)
    
    if lat:
        df = loc_engine.fetch_market_data(lat, lon)
        staff_cost = 150000 
        cogs_pct = 30 
        fin = fin_engine.calculate_roi(area, rent, capex, ticket, orders, staff_cost, cogs_pct)
        
        st.title(f"Investment Report: {addr.split(',')[0]}")
        st.markdown("---")
        
        c1, c2, c3, c4 = st.columns(4)
        profit_color = "sub-pos" if fin['profit'] > 0 else "sub-neg"
        be_color = "sub-pos" if fin['breakeven'] < 18 else "sub-neg"
        
        c1.markdown(f"""<div class="metric-box"><div class="metric-lbl">Est. Monthly Revenue</div><div class="metric-val">₹{fin['rev']:,.0f}</div><div class="metric-sub sub-pos">Based on {orders} daily avg</div></div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class="metric-box"><div class="metric-lbl">Net Profit (EBITDA)</div><div class="metric-val">₹{fin['profit']:,.0f}</div><div class="metric-sub {profit_color}">{fin['margin']:.1f}% Margin</div></div>""", unsafe_allow_html=True)
        c3.markdown(f"""<div class="metric-box"><div class="metric-lbl">Break-Even Point</div><div class="metric-val">{fin['breakeven']:.1f}</div><div class="metric-sub {be_color}">Months</div></div>""", unsafe_allow_html=True)
        c4.markdown(f"""<div class="metric-box"><div class="metric-lbl">Competition Density</div><div class="metric-val">{len(df[df['Category']=='Competitor'])}</div><div class="metric-sub sub-neg">Nearby Rivals</div></div>""", unsafe_allow_html=True)
        
        st.markdown("###")
        
        col_viz1, col_viz2 = st.columns([1.5, 1])
        with col_viz1:
            st.subheader("📍 Gap Analysis Map")
            # Map tiles change based on Dark/Light mode
            m = folium.Map([lat, lon], zoom_start=15, tiles=map_tiles)
            
            HeatMap([[r['Lat'], r['Lon']] for i, r in df[df['Category']=='Corporate'].iterrows()], 
                    gradient={0.4: '#3b82f6', 1: '#60a5fa'}, radius=15).add_to(m)
            
            for _, r in df[df['Category']=='Competitor'].iterrows():
                folium.CircleMarker([r['Lat'], r['Lon']], radius=5, color='#ef4444', fill=True, fill_opacity=0.8, popup=r['Name']).add_to(m)
            
            st_folium(m, height=400, width=None)
        
        with col_viz2:
            st.subheader("📈 Profitability Curve")
            cost_data = pd.DataFrame({'Item': ['Revenue', 'COGS', 'Rent', 'Staff', 'Net Profit'], 'Amount': [fin['rev'], -fin['costs']['COGS'], -fin['costs']['Rent'], -fin['costs']['Staff'], fin['profit']], 'Type': ['Income', 'Expense', 'Expense', 'Expense', 'Total']})
            
            # Dynamic Colors for Chart
            bar_colors = ['#4ade80', '#f87171', '#fbbf24'] 
            
            chart = alt.Chart(cost_data).mark_bar().encode(
                x=alt.X('Item', sort=None),
                y='Amount',
                color=alt.Color('Type', scale=alt.Scale(domain=['Income', 'Expense', 'Total'], range=bar_colors)),
                tooltip=['Item', 'Amount']
            ).properties(height=400).configure_axis(
                labelColor=text_color,
                titleColor=text_color,
                gridColor=card_border
            ).configure_view(strokeOpacity=0)
            
            st.altair_chart(chart, use_container_width=True)

        st.markdown("---")
        c_dl1, c_dl2 = st.columns([3, 1])
        with c_dl1:
            st.info(f"💡 **AI Verdict:** Based on a {rent} PSF rent and {ticket} ticket size, you need **{int(fin['costs']['Rent']/ (ticket*0.3))} orders/month** just to cover rent. Your current projection is {orders*30} orders.")
        with c_dl2:
            pdf_bytes = create_investor_deck(addr, df, {'capex':capex, 'rev':fin['rev'], 'profit':fin['profit'], 'margin':fin['margin'], 'breakeven':fin['breakeven'], 'costs':fin['costs']}, {'orders':orders})
            st.download_button("📥 Download Investor Deck", data=pdf_bytes, file_name="Investment_Memo.pdf", mime="application/pdf", type="primary", use_container_width=True)
    else:
        st.error("Location not found. Try a major city area.")