import streamlit as st
import pandas as pd
import numpy as np

# Add new imports for formatted tables
import polars as pl
from great_tables import GT, loc, style


# Replace the generate_pdf_from_html function with this improved version:


# PDF generation function
def create_html_download(table, title):
    """Create downloadable HTML file from great_tables"""
    html_content = table._repr_html_()
    
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{title}</title>
        <style>
            body {{ 
                margin: 20px; 
                padding: 20px; 
                font-family: Arial, sans-serif; 
                background-color: white;
            }}
            table {{ 
                border-collapse: collapse; 
                width: 100%; 
                page-break-inside: avoid; 
            }}
            @media print {{
                body {{ margin: 0.5in; }}
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    return full_html.encode('utf-8')
    
def create_formatted_tables(df_filtered, district_name):
    """Create formatted GT tables for HTML export"""
    
    # Prepare operations data
    df_operations = df_filtered[['School Name', 
                                'Operational Budget FY25',
                                'Operations 7% Cut',
                                'Operations 15% Cut',
                                'Positions', 
                                'Positions 7% Cut', 
                                'Positions 15% Cut', 
                                'SPED Positions',
                                'SPED Positions 7% Cut',
                                'SPED Positions 15% Cut']].copy()
    
    # Prepare capital data
    df_capital = df_filtered[['School Name',
                             'Immediate Capital Needs',
                             'Total Capital Needs']].copy()
    df_capital.columns = ['School Name', 'Immediate (within 5 years)', 'Total']
    
    # ADD DISTRICT TOTALS ROW TO OPERATIONS
    operations_totals = {}
    operations_totals['School Name'] = f'{district_name} TOTAL'
    operations_numeric_cols = [col for col in df_operations.columns if col != 'School Name']
    for col in operations_numeric_cols:
        operations_totals[col] = df_operations[col].sum()
    
    operations_totals_df = pd.DataFrame([operations_totals])
    df_operations = pd.concat([df_operations, operations_totals_df], ignore_index=True)
    
    # ADD DISTRICT TOTALS ROW TO CAPITAL
    capital_totals = {}
    capital_totals['School Name'] = f'{district_name} TOTAL'
    capital_totals['Immediate (within 5 years)'] = df_capital['Immediate (within 5 years)'].sum()
    capital_totals['Total'] = df_capital['Total'].sum()
    
    capital_totals_df = pd.DataFrame([capital_totals])
    df_capital = pd.concat([df_capital, capital_totals_df], ignore_index=True)
    
    # Convert to polars
    df_operations_pl = pl.from_pandas(df_operations)
    df_capital_pl = pl.from_pandas(df_capital)
    
    # Define column groups
    budget_cols = ["Operational Budget FY25", "Operations 7% Cut", "Operations 15% Cut"]
    position_cols = ["Positions", "Positions 7% Cut", "Positions 15% Cut"]
    sped_cols = ["SPED Positions", "SPED Positions 7% Cut", "SPED Positions 15% Cut"]
    cuts_cols = ["Operations 7% Cut", "Operations 15% Cut", "Positions 7% Cut", "Positions 15% Cut", "SPED Positions 7% Cut", "SPED Positions 15% Cut"]
    
    # Create operations table
    operations_table = (
        GT(df_operations_pl)
        .tab_header(f"{district_name} - CPS School-Level Budget Cut Impacts")
        .tab_spanner(label="Operations Budget Impact", columns=budget_cols)
        .tab_spanner(label="Positions Impact", columns=position_cols)
        .tab_spanner(label="SPED Positions Impact", columns=sped_cols)
        .cols_label(
            **{
                "Operational Budget FY25": "FY25 Budget",
                "Operations 7% Cut": "7% Cuts",
                "Operations 15% Cut": "15% Cuts",
                "Positions 7% Cut": "7% Cuts",
                "Positions 15% Cut": "15% Cuts",
                "SPED Positions 7% Cut": "7% Cuts",
                "SPED Positions 15% Cut": "15% Cuts"
            }
        )
        .fmt_currency(columns=budget_cols, decimals=0)
        .fmt_number(columns=position_cols + sped_cols, decimals=1)
        .sub_missing(missing_text="")
        .tab_style(style=style.text(color="red"), locations=loc.body(columns=cuts_cols))
        .tab_style(style=style.text(weight="bold"), locations=loc.body(rows=pl.col("School Name").str.contains("TOTAL")))
    )
    
    # Create capital table
    capital_table = (
        GT(df_capital_pl)
        .tab_header(f"{district_name} - CPS School Capital Needs")
        .fmt_currency(columns=["Immediate (within 5 years)", "Total"], decimals=0)
        .sub_missing(missing_text="")
        .tab_style(style=style.text(weight="bold"), locations=loc.body(rows=pl.col("School Name").str.contains("TOTAL")))
        .cols_width({
            "School Name": "250px",
            "Immediate (within 5 years)": "150px",
            "Total": "150px"
        })
    )
    
    return operations_table, capital_table

# Load data
@st.cache_data
def load_data():
    """Load the CPS budget stakes dataset"""
    try:
        df = pd.read_csv(r"cps_budget_stakes_dataset_stacked_2025-06-23.csv")
        return df
    except FileNotFoundError:
        st.error("Data file not found. Please ensure the CSV file is in the correct location.")
        return None

# Main app
def main():
    st.title("🏫 CPS Budget Stakes Dashboard")
    st.markdown("**Filter schools by legislative district to view capital needs and the impact of budget cuts**")
 
 # Replace your entire st.markdown CSS block with this:

    st.markdown("""
    <style>
    .stApp {
        background-color: white !important;
        color: black !important;
    }
    
        /* FIX APP HEADER - MAKE WHITE ON MOBILE */
    .stAppHeader {
        background-color: white !important;
        color: black !important;
    }
    
    .stAppHeader > div {
        background-color: white !important;
        color: black !important;
    }
    
    /* Fix header text and elements */
    .stAppHeader * {
        background-color: white !important;
        color: black !important;
    }
    
    /* Target header specifically for mobile */
    [data-testid="stHeader"] {
        background-color: white !important;
        color: black !important;
    }
    
    [data-testid="stHeader"] > div {
        background-color: white !important;
        color: black !important;
    }
    
        /* TARGET MAIN CONTENT AREA SPECIFICALLY - RESPONSIVE */
    .main .block-container {
        padding-left: 4rem !important;
        padding-right: 4rem !important;
        max-width: none !important;
        width: 100% !important;
    }
    
    /* Use stMain to target main content - DESKTOP */
    .stMain .block-container {
        padding-left: 6rem !important;
        padding-right: 6rem !important;
        max-width: none !important;
    }
    
    /* MOBILE RESPONSIVE - Reduce padding on small screens */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        
        .stMain .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
    
    /* Force all text to be black */
    .stMarkdown, .stText, .stCaption, .stSubheader, .stHeader, .stTitle {
        color: black !important;
    }
    
    /* Fix tab labels specifically */
    .stTabs [data-baseweb="tab-list"] button {
        color: black !important;
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: black !important;
        font-weight: bold !important;
    }
    
    /* Fix subheaders in tabs */
    .stTabs [data-baseweb="tab-panel"] h3 {
        color: black !important;
    }
    
        /* Fix tab labels specifically */
    .stTabs [data-baseweb="tab-list"] button {
        color: black !important;
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: black !important;
        font-weight: bold !important;
    }
    
    /* Fix subheaders in tabs */
    .stTabs [data-baseweb="tab-panel"] h3 {
        color: black !important;
    }
    
    /* REMOVE TAB BORDERS ON MOBILE */
    .stTabs [data-baseweb="tab-list"] {
        border: none !important;
        border-bottom: none !important;
    }
    
    .stTabs [data-baseweb="tab-list"] button {
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        border: none !important;
        border-top: none !important;
        box-shadow: none !important;
    }
    
    /* Mobile specific tab border removal */
    @media (max-width: 768px) {
        .stTabs [data-baseweb="tab-list"] {
            border: none !important;
            outline: none !important;
        }
        
        .stTabs [data-baseweb="tab-list"] button {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }
        
        .stTabs [data-baseweb="tab-panel"] {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }
    }
    
    /* Force all headers to be black */
    h1, h2, h3, h4, h5, h6 {
        color: black !important;
    }
    
    /* Fix metric labels and values */
    .stMetric > div > div {
        color: black !important;
    }
    
    .stMetric label {
        color: black !important;
    }
    
    .stMetric > div > div > div {
        color: black !important;
    }
    
    /* Fix all metric text */
    [data-testid="metric-container"] {
        color: black !important;
    }
    
    [data-testid="metric-container"] > div {
        color: black !important;
    }
    
    [data-testid="metric-container"] label {
        color: black !important;
    }
    
        /* INCREASE METRIC FONT SIZE */
    .stMetric {
        font-size: 1.3rem !important;
    }
    
    .stMetric label {
        font-size: 1.2rem !important;
        font-weight: 700 !important;
    }
    
    .stMetric [data-testid="metric-value"] {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
    }
    
    .stMetric [data-testid="metric-delta"] {
        font-size: 1.3rem !important;
    }
    
    /* Additional metric targeting */
    [data-testid="metric-container"] label {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
    }
    
    [data-testid="metric-container"] div[data-testid="metric-value"] {
        font-size: 2.8rem !important;
        font-weight: 800 !important;
    }
    
       /* Additional metric targeting */
    [data-testid="metric-container"] label {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
    }
    
    [data-testid="metric-container"] div[data-testid="metric-value"] {
        font-size: 2.8rem !important;
        font-weight: 800 !important;
    }
    
        /* TARGET METRIC LABELS SPECIFICALLY - EXACT STRUCTURE */
    [data-testid="stMetricLabel"] p {
        font-size: 1.5rem !important;
        font-weight: 500 !important;
        color: black !important;
    }
    
    /* Target the markdown container inside metric labels */
    [data-testid="stMetricLabel"] [data-testid="stMarkdownContainer"] p {
        font-size: 1.5rem !important;
        font-weight: 500 !important;
        color: black !important;
    }
    
    /* Nuclear option for metric label paragraphs */
    label[data-testid="stMetricLabel"] p,
    .st-emotion-cache-15jn9ue p,
    .st-emotion-cache-bfgnao p {
        font-size: 1.5rem !important;
        font-weight: 500 !important;
        color: black !important;
    }
    
    /* Ensure metric values stay large */
    [data-testid="metric-container"] div[data-testid="metric-value"],
    .stMetric [data-testid="metric-value"] {
        font-size: 2.8rem !important;
        font-weight: 800 !important;
    }
    
    /* Target metric text content directly */
    div[data-testid="metric-container"] div:first-child {
        font-size: 1.5rem !important;
        font-weight: 500 !important;
        color: black !important;
    }
    
    /* TARGET METRIC VALUES SPECIFICALLY */
    [data-testid="stMetricValue"] {
        font-size: 2.3rem !important;
        font-weight: 700 !important;
        color: black !important;
    }
    
    /* TARGET METRIC DELTA SPECIFICALLY */
    [data-testid="stMetricDelta"] {
        font-size: 1.3rem !important;
        color: black !important;
    }
    
    /* Nuclear option for metric elements */
    div[data-testid*="metric"] {
        font-size: inherit !important;
        color: black !important;
    }
    
    /* Ensure sidebar is also light */
    .css-1d391kg {
        background-color: #f0f2f6 !important;
    }
    
     /* FIX MOBILE SIDEBAR - Add these new rules */
    .stSidebar {
        background-color: #f0f2f6 !important;
    }
        
    .stSidebar > div {
        background-color: #f0f2f6 !important;
    }
    
    /* Target mobile sidebar specifically */
    .stSidebar .stMarkdown {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    /* Fix mobile sidebar container */
    section[data-testid="stSidebar"] {
        background-color: #f0f2f6 !important;
    }
    
    section[data-testid="stSidebar"] > div {
        background-color: #f0f2f6 !important;
    }
    
    /* Ensure sidebar is also light */
    .css-1d391kg {
        background-color: #f0f2f6 !important;
    }
    
    /* FIX MOBILE SIDEBAR BACKGROUND AND TEXT */
    .stSidebar {
        background-color: #f0f2f6 !important;
    }
    
    .stSidebar > div {
        background-color: #f0f2f6 !important;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #f0f2f6 !important;
    }
    
    section[data-testid="stSidebar"] > div {
        background-color: #f0f2f6 !important;
    }
    
    .stSidebar .element-container {
        background-color: #f0f2f6 !important;
    }
    
    /* FIX SIDEBAR TEXT COLOR */
    .stSidebar .stMarkdown {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    .stSidebar .stMarkdown p {
        color: black !important;
    }
    
    .stSidebar .stMarkdown h1, 
    .stSidebar .stMarkdown h2, 
    .stSidebar .stMarkdown h3, 
    .stSidebar .stMarkdown h4 {
        color: black !important;
    }
    
    /* Fix sidebar selectbox text */
    .stSidebar .stSelectbox label {
        color: black !important;
    }
    
    .stSidebar .stRadio label {
        color: black !important;
    }
    
    /* Fix sidebar info/success messages */
    .stSidebar .element-container div {
        color: black !important;
    }
       
    /* FIX DOWNLOAD AND REGULAR BUTTONS - White background, black text */
    .stDownloadButton > button {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
    }
    
    .stDownloadButton > button:hover {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    /* Fix all button types - White background, black text */
    .stButton > button {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
    }
    
    .stButton > button:hover {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    /* Fix sidebar buttons specifically */
    .stSidebar .stButton > button {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
    }
    
        /* Fix radio buttons background - Container light gray */
    .stRadio > div {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    /* Fix radio button labels - Container light gray */
    .stRadio > div > label {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    /* Fix radio button options container - Light gray */
    .stRadio > div > div {
        background-color: #f0f2f6 !important;
    }
    
    /* Fix the actual radio button circles - Make them white */
    .stRadio input[type="radio"] {
        background-color: white !important;
    }
    
    /* Fix sidebar radio buttons specifically - Container light gray */
    .stSidebar .stRadio > div {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    .stSidebar .stRadio > div > label {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    /* Fix sidebar radio button circles - White */
    .stSidebar .stRadio input[type="radio"] {
        background-color: white !important;
    }
    
    /* Fix selectbox (dropdown) containers - Make them white */
    .stSelectbox > div > div {
        background-color: white !important;
        color: black !important;
    }
    
    .stSelectbox > div > div > div {
        background-color: white !important;
        color: black !important;
    }
    
    /* Fix sidebar selectbox specifically */
    .stSidebar .stSelectbox > div > div {
        background-color: white !important;
        color: black !important;
    }
    
    .stSidebar .stSelectbox > div > div > div {
        background-color: white !important;
        color: black !important;
    }
    
    /* Fix selectbox input field */
    .stSelectbox input {
        background-color: white !important;
        color: black !important;
    }
    
    /* FORCE DOWNLOAD BUTTONS TO WHITE BACKGROUND */
    .stDownloadButton > button {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
    }
    
    .stDownloadButton > button:hover {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    /* Force sidebar download buttons to white */
    .stSidebar .stDownloadButton > button {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
    }
    
    .stSidebar .stDownloadButton > button:hover {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    /* Target the CSV download button specifically */
    .stSidebar [data-testid="stDownloadButton"] button {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
    }
    
    .stSidebar [data-testid="stDownloadButton"] button:hover {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    /* Nuclear option for all sidebar buttons */
    section[data-testid="stSidebar"] button {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
    }
    
    section[data-testid="stSidebar"] button:hover {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    /* FIX SIDEBAR COLLAPSE BUTTON - MAKE WHITE */
    .css-1v0mbdj {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
    }
    
    .css-1v0mbdj:hover {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    /* Alternative sidebar button selectors */
    [data-testid="collapsedControl"] {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
    }
    
    [data-testid="collapsedControl"]:hover {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    /* Sidebar toggle button */
    .st-emotion-cache-1v0mbdj {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
    }
    
    .st-emotion-cache-1v0mbdj:hover {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    /* NUCLEAR OPTION - Force ALL buttons to white background */
    button {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
    }
    
        /* FIX SIDEBAR EXPAND BUTTON - MAKE WHITE */
    [data-testid="stSidebarNav"] button {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
    }
    
    [data-testid="stSidebarNav"] button:hover {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    /* Alternative selector for sidebar expand button */
    .css-1lcbmhc {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
    }
    
    .css-1lcbmhc:hover {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    button:hover {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
        /* Sidebar expand/collapse button - Additional selectors */
    [data-testid="stSidebarNavSeparator"] + div button {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
    }
    
    [data-testid="stSidebarNavSeparator"] + div button:hover {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    /* Force arrow icons to be black */
    [data-testid="stSidebarNav"] button svg {
        color: black !important;
        fill: black !important;
    }
    
    .css-1lcbmhc svg {
        color: black !important;
        fill: black !important;
    }
    
    /* Additional arrow icon selectors */
    button[data-testid="stSidebarNavSeparator"] + div button svg {
        color: black !important;
        fill: black !important;
    }
    
    /* Catch any remaining arrow icons */
    section[data-testid="stSidebar"] svg {
        color: black !important;
        fill: black !important;
    }
    
        /* FORCE SIDEBAR ARROW ICONS TO BE BLACK - FINAL OVERRIDE */
    button svg, button svg path {
        color: black !important;
        fill: black !important;
        stroke: black !important;
    }
    
    /* Specific targeting for sidebar expand/collapse arrows */
    [data-testid="stSidebarNav"] svg,
    [data-testid="stSidebarNav"] svg path,
    .css-1lcbmhc svg,
    .css-1lcbmhc svg path,
    section[data-testid="stSidebar"] svg,
    section[data-testid="stSidebar"] svg path {
        color: black !important;
        fill: black !important;
        stroke: black !important;
    }
    
    /* Target any keyboard arrow icons specifically */
    button[title*="Expand"] svg,
    button[title*="Collapse"] svg,
    button[aria-label*="sidebar"] svg {
        color: black !important;
        fill: black !important;
        stroke: black !important;
    }
    
       /* NUCLEAR OPTION FOR ALL ICONS - FORCE BLACK */
    * svg, * svg path, * svg g, * svg polygon, * svg circle, * svg rect {
        color: black !important;
        fill: black !important;
        stroke: black !important;
    }
    
    /* Target specific arrow characters if they're text */
    button::before, button::after {
        color: black !important;
    }
    
    /* Force any pseudo-elements to be black */
    button * {
        color: black !important;
    }
    
    /* If arrows are Unicode characters */
    [data-testid*="sidebar"] button, 
    [data-testid*="Sidebar"] button,
    button[title*="expand"],
    button[title*="collapse"] {
        color: black !important;
    }
    
    </style>
    """, unsafe_allow_html=True)
    
    # Load data
    df = load_data()
    if df is None:
        return
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Filter options
    filter_type = st.sidebar.radio(
        "Filter by:",
        ["Chamber & District", "Legislator"]
    )
    
    if filter_type == "Chamber & District":
        # Chamber selection
        chambers = sorted(df['Chamber'].unique())
        selected_chamber = st.sidebar.selectbox("Select Chamber:", chambers)
        
        # District selection (filtered by chamber)
        available_districts = sorted(df[df['Chamber'] == selected_chamber]['District'].unique())
        selected_district = st.sidebar.selectbox("Select District:", available_districts)
        
        # Filter data
        filtered_df = df[(df['Chamber'] == selected_chamber) & (df['District'] == selected_district)]
        
        # Display selection
        st.subheader(f"📊 {selected_chamber} - District {selected_district}")
        
    else:  # Filter by Legislator
        # Legislator selection
        legislators = sorted(df['Legislator'].dropna().unique())
        selected_legislator = st.sidebar.selectbox("Select Legislator:", legislators)
        
        # Filter data
        filtered_df = df[df['Legislator'] == selected_legislator]
        
        # Display selection
        legislator_info = filtered_df.iloc[0]
        st.subheader(f"📊 {selected_legislator} ({legislator_info['Chamber']} - District {legislator_info['District']})")
    
    # Define columns to display
    display_columns = [
        'School Name',
        'Immediate Capital Needs',
        'Total Capital Needs', 
        'Operational Budget FY25',
        'Operations 7% Cut',
        'Operations 15% Cut',
        'Positions',
        'Positions 7% Cut',
        'Positions 15% Cut',
        'SPED Positions',
        'SPED Positions 7% Cut',
        'SPED Positions 15% Cut'
    ]
    

    
    # CONSOLIDATED DOWNLOAD SECTION
    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 Download Data")
    
    if len(filtered_df) > 0:
        # Prepare data for downloads
        all_data_df = filtered_df[display_columns].copy()
        
        # Create district name for files
        if filter_type == "Chamber & District":
            district_name = f"{selected_chamber} District {selected_district}"
            filename_prefix = f"{selected_chamber.replace(' ', '_')}_District_{selected_district}"
        else:
            # Get chamber and district info from filtered data
            legislator_info = filtered_df.iloc[0]
            district_name = f"{legislator_info['Chamber']} District {legislator_info['District']}"
            filename_prefix = f"{legislator_info['Chamber'].replace(' ', '_')}_District_{legislator_info['District']}"
        
        # CSV download of all data (NO COLUMNS - just direct sidebar)
        all_csv = all_data_df.to_csv(index=False)
        st.sidebar.download_button(
            label="📊 Download District Data (CSV)",
            data=all_csv,
            file_name=f"{filename_prefix}_all_data.csv",
            mime="text/csv",
            help="Download all capital and operations data as CSV"
        )
        
        if st.sidebar.button("📊 Generate Capital Report", help="Create formatted HTML report of capital needs data"):
            with st.spinner("Generating Capital Report..."):
                try:
                    # Add district total row to filtered_df
                    capital_df_with_total = filtered_df[['School Name', 'Immediate Capital Needs', 'Total Capital Needs']].copy()
                    
                    # Create district total row
                    total_row = pd.DataFrame([[
                        f"{district_name} Total",
                        capital_df_with_total['Immediate Capital Needs'].sum(),
                        capital_df_with_total['Total Capital Needs'].sum()
                    ]])
                    total_row.columns = capital_df_with_total.columns
                    capital_df_with_total = pd.concat([capital_df_with_total, total_row], ignore_index=True)
                    
                    # Rename columns for great_tables
                    capital_df_with_total.columns = ['School Name', 'Immediate (within 5 years)', 'Total']
                    
                    # Convert to polars for great_tables
                    capital_df_pl = pl.from_pandas(capital_df_with_total)
                    
                    # Create great_tables capital table
                    capital_table = (
                        GT(capital_df_pl)
                        .tab_header(f"{district_name} - CPS School Capital Needs")
                        .fmt_currency(
                            columns=["Immediate (within 5 years)", "Total"],
                            decimals=0,
                        )
                        .sub_missing(missing_text="")
                        .tab_style(
                            style=style.text(weight="bold"),
                            locations=loc.body(rows=pl.col("School Name").str.contains("Total"))
                        )
                        .cols_width({
                            "School Name": "250px",
                            "Immediate (within 5 years)": "150px",
                            "Total": "150px"
                        })
                    )
                    
                    # Get HTML content from great_tables
                    html_content = capital_table._repr_html_()
                    
                    # Create complete HTML document
                    full_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>Capital Needs Report - {filename_prefix}</title>
                        <style>
                            body {{ 
                                margin: 0; 
                                padding: 20px; 
                                font-family: Arial, sans-serif; 
                                background-color: white;
                                color: black;
                            }}
                            table {{ 
                                page-break-inside: auto; 
                                width: 100%;
                            }}
                            @media print {{
                                body {{ 
                                    margin: 0.25in; 
                                    -webkit-print-color-adjust: exact;
                                    print-color-adjust: exact;
                                }}
                                table {{ 
                                    width: 8.5in !important;
                                    max-width: 8.5in !important;
                                    font-size: 10px; 
                                    zoom: 1;
                                    table-layout: fixed;
                                    page-break-inside: auto;
                                }}
                                /* Allow table rows to break across pages */
                                tr {{
                                    page-break-inside: avoid;
                                }}
                                /* Keep header on each page */
                                thead {{
                                    display: table-header-group;
                                }}
                                @page {{
                                    size: letter portrait;
                                    margin: 0.25in;
                                }}
                            }}
                        </style>
                    </head>
                    <body>
                        {html_content}
                        <div style="margin-top: 30px; font-size: 12px; color: #666;">
                            Report generated on {pd.Timestamp.now().strftime('%B %d, %Y at %I:%M %p')}
                        </div>
                    </body>
                    </html>
                    """
                    
                    # Create download button for HTML
                    st.sidebar.download_button(
                        label="⬇️ Download Capital Report (HTML)",
                        data=full_html.encode('utf-8'),
                        file_name=f"{filename_prefix}_capital_report.html",
                        mime="text/html",
                        help="Download as HTML file (can be printed to PDF from browser)"
                    )
                    
                    # Also provide CSV option
                    csv_data = capital_df_with_total.to_csv(index=False)
                    st.sidebar.download_button(
                        label="📊 Download Capital Data (CSV)",
                        data=csv_data,
                        file_name=f"{filename_prefix}_capital.csv",
                        mime="text/csv"
                    )
                    
                    st.sidebar.success("✅ Capital report generated successfully!")
                    st.sidebar.info("💡 Tip: Open the HTML file in your browser and use 'Print to PDF' for a PDF version")

                except Exception as e:
                    st.sidebar.error(f"❌ Error generating report: {str(e)}")

        if st.sidebar.button("📋 Generate Operations Report", help="Create formatted HTML report of operations data"):
            with st.spinner("Generating Operations Report..."):
                try:
                    # Create operations dataframe with totals
                    operations_df_with_total = filtered_df[['School Name', 'Operational Budget FY25', 'Operations 7% Cut', 'Operations 15% Cut',
                                                           'Positions', 'Positions 7% Cut', 'Positions 15% Cut',
                                                           'SPED Positions', 'SPED Positions 7% Cut', 'SPED Positions 15% Cut']].copy()
                    
                    # Create district total row
                    numeric_cols = ['Operational Budget FY25', 'Operations 7% Cut', 'Operations 15% Cut',
                                   'Positions', 'Positions 7% Cut', 'Positions 15% Cut',
                                   'SPED Positions', 'SPED Positions 7% Cut', 'SPED Positions 15% Cut']
                    
                    total_row = pd.DataFrame([[f"{district_name} Total"] + 
                                            operations_df_with_total[numeric_cols].sum().tolist()])
                    total_row.columns = operations_df_with_total.columns
                    operations_df_with_total = pd.concat([operations_df_with_total, total_row], ignore_index=True)
                    
                    # Convert to polars for great_tables
                    operations_df_pl = pl.from_pandas(operations_df_with_total)
                    
                    # Define column groups for spanners
                    budget_cols = ["Operational Budget FY25", "Operations 7% Cut", "Operations 15% Cut"]
                    position_cols = ["Positions", "Positions 7% Cut", "Positions 15% Cut"]
                    sped_cols = ["SPED Positions", "SPED Positions 7% Cut", "SPED Positions 15% Cut"]
                    cuts_cols = ["Operations 7% Cut", "Operations 15% Cut", "Positions 7% Cut", "Positions 15% Cut", "SPED Positions 7% Cut", "SPED Positions 15% Cut"]
                    
                    # Create great_tables operations table
                    operations_table = (
                        GT(operations_df_pl)
                        .tab_header(f"{district_name} - CPS School-Level Budget Cut Impacts")
                        .tab_spanner(label="Operations Budget Impact", columns=budget_cols)
                        .tab_spanner(label="Positions Impact", columns=position_cols)
                        .tab_spanner(label="SPED Positions Impact", columns=sped_cols)
                        .cols_label(
                            **{
                                "Operational Budget FY25": "FY25 Budget",
                                "Operations 7% Cut": "7% Cuts",
                                "Operations 15% Cut": "15% Cuts",
                                "Positions 7% Cut": "7% Cuts",
                                "Positions 15% Cut": "15% Cuts",
                                "SPED Positions 7% Cut": "7% Cuts",
                                "SPED Positions 15% Cut": "15% Cuts"
                            }
                        )
                        .fmt_currency(
                            columns=budget_cols,
                            decimals=0,
                        )
                        .fmt_number(
                            columns=position_cols + sped_cols,
                            decimals=1,
                        )
                        .sub_missing(missing_text="")
                        # Styling ----
                        .tab_style(
                            style=style.text(color="red"),
                            locations=loc.body(columns=cuts_cols)
                        )
                        .tab_style(
                            style=style.text(weight="bold"),
                            locations=loc.body(rows=pl.col("School Name").str.contains("Total"))
                        )
                    )
                    
                    # Get HTML content from great_tables
                    html_content = operations_table._repr_html_()
                    
                    # Create complete HTML document

                    full_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>Operations Report - {filename_prefix}</title>
                        <style>
                            body {{ 
                                margin: 0; 
                                padding: 20px; 
                                font-family: Arial, sans-serif; 
                                background-color: white;
                                color: black;
                            }}
                            table {{ 
                                page-break-inside: auto; 
                                width: 100%;
                            }}
                            @media print {{
                                body {{ 
                                    margin: 0.5in; 
                                    -webkit-print-color-adjust: exact;
                                    print-color-adjust: exact;
                                }}
                                table {{ 
                                    width: 7.5in !important;
                                    max-width: 7.5in !important;
                                    font-size: 10px; 
                                    zoom: 1;
                                    table-layout: fixed;
                                    page-break-inside: auto;
                                }}
                                /* Allow table rows to break across pages */
                                tr {{
                                    page-break-inside: avoid;
                                }}
                                /* Keep header on each page */
                                thead {{
                                    display: table-header-group;
                                }}
                                @page {{
                                    size: letter portrait;
                                    margin: 0.1in;
                                }}
                            }}
                        </style>
                    </head>
                    <body>
                        {html_content}
                        <div style="margin-top: 30px; font-size: 12px; color: #666;">
                            Report generated on {pd.Timestamp.now().strftime('%B %d, %Y at %I:%M %p')}
                        </div>
                    </body>
                    </html>
                    """
                    
                    # Create download button for HTML
                    st.sidebar.download_button(
                        label="⬇️ Download Operations Report (HTML)",
                        data=full_html.encode('utf-8'),
                        file_name=f"{filename_prefix}_operations_report.html",
                        mime="text/html",
                        help="Download as HTML file (can be printed to PDF from browser)"
                    )
                    
                    # Also provide CSV option
                    csv_data = operations_df_with_total.to_csv(index=False)
                    st.sidebar.download_button(
                        label="📋 Download Operations Data (CSV)",
                        data=csv_data,
                        file_name=f"{filename_prefix}_operations.csv",
                        mime="text/csv"
                    )
                    
                    st.sidebar.success("✅ Operations report generated successfully!")
                    st.sidebar.info("💡 Tip: Open the HTML file in your browser and use 'Print to PDF' for a PDF version")

                except Exception as e:
                    st.sidebar.error(f"❌ Error generating report: {str(e)}")
    
    # Create display dataframe
    display_df = filtered_df[display_columns].copy()
    
    display_df.columns = [
        'School Name',
        'Immediate (within 5 years)',
        'Total Capital Needs', 
        'FY25 Budget',
        'Budget Cut (7%)',
        'Budget Cut (15%)',
        'Total Positions',
        'Position Loss (7%)',
        'Position Loss (15%)',
        'SPED Positions',
        'SPED Loss (7%)',
        'SPED Loss (15%)'
    ]   

    # Create tabs for data display
    tab1, tab2 = st.tabs(["💰 Capital Needs ", " 🏢 Operations & Positions "])
    
    # Format currency and numbers functions
    def format_currency(val):
        if pd.isna(val):
            return ""
        return f"${val:,.0f}"
    
    def format_positions(val):
        if pd.isna(val):
            return ""
        return f"{val:.1f}"
    
    with tab1:
        st.subheader("Capital Needs by School")
        
        # Define capital columns
        capital_columns = [
            'School Name',
            'Immediate Capital Needs',
            'Total Capital Needs'
        ]
        
        # Create capital display dataframe
        capital_df = filtered_df[capital_columns].copy()
        
        # Rename columns for display
        capital_df.columns = [
            "School Name",
            "Immediate (within 5 years)",
            "Total Capital Needs"
        ]
        
        # Calculate totals for capital
        capital_totals = {}
        capital_totals['School Name'] = 'TOTAL'
        capital_totals['Immediate (within 5 years)'] = capital_df['Immediate (within 5 years)'].sum()
        capital_totals['Total Capital Needs'] = capital_df['Total Capital Needs'].sum()
        
        # Add totals row
        capital_totals_df = pd.DataFrame([capital_totals])
        capital_final_df = pd.concat([capital_df, capital_totals_df], ignore_index=True)
        
        # Format currency
        for col in ['Immediate (within 5 years)', 'Total Capital Needs']:
            capital_final_df[col] = capital_final_df[col].apply(format_currency)
        
        # Display capital metrics
        if len(filtered_df) > 0:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Schools", len(filtered_df))
            with col2:
                st.metric("Immediate Capital Needs", format_currency(capital_totals['Immediate (within 5 years)']))
            with col3:
                st.metric("Total Capital Needs", format_currency(capital_totals['Total Capital Needs']))
        
        if len(filtered_df) > 0:
            # Create custom HTML table for capital data
            def create_html_table_capital(df):
                html = """
                <style>
                .custom-table-capital {
                    border-collapse: collapse;
                    width: 100%;
                    font-family: 'Source Sans Pro', sans-serif;
                    font-size: 14px;
                    margin: 0 !important;
                }
                .custom-table-capital thead {
                    position: sticky;
                    top: 0;
                    z-index: 10;
                    background-color: white;
                }
                .custom-table-capital th {
                    background-color: white !important;
                    font-weight: bold !important;
                    text-align: center !important;
                    padding: 10px;
                    border: 1px solid #ddd;
                    color: black !important;
                    position: sticky;
                    top: 0;
                }
                .custom-table-capital td {
                    padding: 8px 10px;
                    border: 1px solid #ddd;
                    text-align: center;
                }
                .custom-table-capital td:first-child {
                    text-align: left;
                }
                .custom-table-capital tr:last-child {
                    background-color: #f0f0f0;
                    font-weight: bold;
                }
                </style>
                <div style="max-height: 400px; overflow-y: auto; border: 1px solid #ddd; width: 100%;">
                <table class="custom-table-capital">
                <thead><tr>
                """
                
                # Add headers
                for col in df.columns:
                    html += f"<th>{col}</th>"
                html += "</tr></thead><tbody>"
                
                # Add data rows
                for idx, row in df.iterrows():
                    html += "<tr>"
                    for col in df.columns:
                        value = row[col]
                        html += f'<td>{value}</td>'
                    html += "</tr>"
                
                html += "</tbody></table></div>"
                return html
            
            # Display custom HTML table for CAPITAL data
            st.markdown(create_html_table_capital(capital_final_df), unsafe_allow_html=True)
            
        else:
            st.warning("No schools found for the selected criteria.")
    
    with tab2:
        st.subheader("Operations & Positions by School")
        
        # Define operations columns
        operations_columns = [
            'School Name',
            'Operational Budget FY25',
            'Operations 7% Cut',
            'Operations 15% Cut',
            'Positions',
            'Positions 7% Cut',
            'Positions 15% Cut',
            'SPED Positions',
            'SPED Positions 7% Cut',
            'SPED Positions 15% Cut'
        ]
        
        # Create operations display dataframe
        operations_df = filtered_df[operations_columns].copy()
        
        # Rename columns for display
        operations_df.columns = [
            "School Name",
            "FY25 Budget",
            "Budget Cut (7%)",
            "Budget Cut (15%)",
            "Total Positions",
            "Position Loss (7%)",
            "Position Loss (15%)",
            "SPED Positions",
            "SPED Loss (7%)",
            "SPED Loss (15%)"
        ]
        
        # Calculate totals for operations
        operations_numeric_columns = [col for col in operations_df.columns if col != 'School Name']
        operations_totals = {}
        operations_totals['School Name'] = 'TOTAL'
        
        for col in operations_numeric_columns:
            operations_totals[col] = operations_df[col].sum()
        
        # Add totals row
        operations_totals_df = pd.DataFrame([operations_totals])
        operations_final_df = pd.concat([operations_df, operations_totals_df], ignore_index=True)
        
        # Format currency and positions
        currency_cols = ['FY25 Budget', 'Budget Cut (7%)', 'Budget Cut (15%)']
        position_cols = ['Total Positions', 'Position Loss (7%)', 'Position Loss (15%)', 'SPED Positions', 'SPED Loss (7%)', 'SPED Loss (15%)']
        
        formatted_operations_df = operations_final_df.copy()
        for col in currency_cols:
            formatted_operations_df[col] = formatted_operations_df[col].apply(format_currency)
        for col in position_cols:
            formatted_operations_df[col] = formatted_operations_df[col].apply(format_positions)
        
        # Display operations metrics
        if len(filtered_df) > 0:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Schools", len(filtered_df))
            with col2:
                st.metric("Total possible budget cuts", format_currency(operations_totals['Budget Cut (15%)']))
            with col3:
                st.metric("Loss of positions", format_positions(operations_totals['Position Loss (15%)']))
            with col4:
                st.metric("Loss of SPED positions", format_positions(operations_totals['SPED Loss (15%)']))
        
        if len(filtered_df) > 0:
            # Create custom HTML table for full control over styling
            def create_html_table(df):
                cut_columns = ['Budget Cut (7%)', 'Budget Cut (15%)', 'Position Loss (7%)', 'Position Loss (15%)', 'SPED Loss (7%)', 'SPED Loss (15%)']
                
                html = """
                <style>
                .custom-table {
                    border-collapse: collapse;
                    width: 100%;
                    font-family: 'Source Sans Pro', sans-serif;
                    font-size: 14px;
                    margin: 0 !important;
                }
                .custom-table thead {
                    position: sticky;
                    top: 0;
                    z-index: 10;
                    background-color: white;
                }
                .custom-table th {
                    background-color: white !important;
                    font-weight: bold !important;
                    text-align: center !important;
                    padding: 10px;
                    border: 1px solid #ddd;
                    color: black !important;
                    position: sticky;
                    top: 0;
                }
                .custom-table td {
                    padding: 8px 10px;
                    border: 1px solid #ddd;
                    text-align: center;
                }
                .custom-table td:first-child {
                    text-align: left;
                }
                .custom-table tr:last-child {
                    background-color: #f0f0f0;
                    font-weight: bold;
                }
                .cut-column {
                    color: red !important;
                    font-weight: bold;
                }
                </style>
                <div style="max-height: 400px; overflow-y: auto; border: 1px solid #ddd; width: 100%;">
                <table class="custom-table">
                <thead><tr>
                """
                
                # Add headers
                for col in df.columns:
                    html += f"<th>{col}</th>"
                html += "</tr></thead><tbody>"
                
                # Add data rows
                for idx, row in df.iterrows():
                    html += "<tr>"
                    for col in df.columns:
                        value = row[col]
                        css_class = "cut-column" if col in cut_columns else ""
                        html += f'<td class="{css_class}">{value}</td>'
                    html += "</tr>"
                
                html += "</tbody></table></div>"
                return html
            
            # Display custom HTML table
            st.markdown(create_html_table(formatted_operations_df), unsafe_allow_html=True)       
        else:
            st.warning("No schools found for the selected criteria.")


if __name__ == "__main__":
    main()