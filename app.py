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
    
    # Prepare budgeted cuts data
    # First check which columns are available
    cuts_columns = ['School Name', 'Position loss/gain (budgeted)', 'Position loss/gain (% of FY25 positions)', 
                   'CTU layoffs (budgeted)', 'CTU layoffs (% of CTU positions)', 
                   'SPED position loss/gain (budgeted)', 'SPED position loss/gain (% of FY25 SPED positions)']
    
    # Add baseline columns if they exist
    baseline_columns = ['Total FY25', 'Total CTU', 'Total SPED']
    for col in baseline_columns:
        if col in df_filtered.columns:
            cuts_columns.append(col)
    
    df_cuts = df_filtered[cuts_columns].copy()
    
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
    
    # ADD DISTRICT TOTALS ROW TO CUTS
    cuts_totals = {}
    cuts_totals['School Name'] = f'{district_name} TOTAL'
    
    # Sum the actual position numbers and baseline totals (but NOT the percentages)
    numeric_cols_to_sum = ['Position loss/gain (budgeted)', 'CTU layoffs (budgeted)', 'SPED position loss/gain (budgeted)']
    baseline_cols_to_sum = ['Total FY25', 'Total CTU', 'Total SPED']
    
    for col in df_cuts.columns:
        if col != 'School Name':
            if col in numeric_cols_to_sum or col in baseline_cols_to_sum:
                cuts_totals[col] = df_cuts[col].sum()
            else:
                # For percentage columns, we'll calculate them after, so set to 0 for now
                cuts_totals[col] = 0
    
    cuts_totals_df = pd.DataFrame([cuts_totals])
    df_cuts = pd.concat([df_cuts, cuts_totals_df], ignore_index=True)
    
    # Calculate percentages for TOTAL row using the summed totals
    total_idx = df_cuts[df_cuts['School Name'].str.contains("TOTAL")].index[0]
    
    # Position loss/gain percentage = Position loss/gain (budgeted) / Total FY25
    if 'Total FY25' in df_cuts.columns and 'Position loss/gain (budgeted)' in df_cuts.columns:
        total_fy25 = df_cuts.loc[total_idx, 'Total FY25']
        position_change = df_cuts.loc[total_idx, 'Position loss/gain (budgeted)']
        df_cuts.loc[total_idx, 'Position loss/gain (% of FY25 positions)'] = abs(position_change) / total_fy25 if total_fy25 != 0 else 0
    
    # CTU layoffs percentage = CTU layoffs (budgeted) / Total CTU
    if 'Total CTU' in df_cuts.columns and 'CTU layoffs (budgeted)' in df_cuts.columns:
        total_ctu = df_cuts.loc[total_idx, 'Total CTU']
        ctu_change = df_cuts.loc[total_idx, 'CTU layoffs (budgeted)']
        df_cuts.loc[total_idx, 'CTU layoffs (% of CTU positions)'] = abs(ctu_change) / total_ctu if total_ctu != 0 else 0
    
    # SPED position loss/gain percentage = SPED position loss/gain (budgeted) / Total SPED
    if 'Total SPED' in df_cuts.columns and 'SPED position loss/gain (budgeted)' in df_cuts.columns:
        total_sped = df_cuts.loc[total_idx, 'Total SPED']
        sped_change = df_cuts.loc[total_idx, 'SPED position loss/gain (budgeted)']
        df_cuts.loc[total_idx, 'SPED position loss/gain (% of FY25 SPED positions)'] = abs(sped_change) / total_sped if total_sped != 0 else 0

    # Remove unwanted columns from display
    columns_to_remove = ['Total FY25', 'Total CTU', 'Total SPED']
    df_cuts = df_cuts.drop(columns=[col for col in columns_to_remove if col in df_cuts.columns])

    # Convert to polars
    df_operations_pl = pl.from_pandas(df_operations)
    df_capital_pl = pl.from_pandas(df_capital)
    df_cuts_pl = pl.from_pandas(df_cuts)

    # Define column groups
    budget_cols = ["Operational Budget FY25", "Operations 7% Cut", "Operations 15% Cut"]
    position_cols = ["Positions", "Positions 7% Cut", "Positions 15% Cut"]
    sped_cols = ["SPED Positions", "SPED Positions 7% Cut", "SPED Positions 15% Cut"]
    cuts_cols = ['Position loss/gain (budgeted)','Position loss/gain (% of FY25 positions)', 
                 'CTU layoffs (budgeted)','CTU layoffs (% of CTU positions)','SPED position loss/gain (budgeted)',
                 'SPED position loss/gain (% of FY25 SPED positions)']
    
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
                "SPED Positions": "SPED Positions",
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
    
    cuts_table = (
        GT(df_cuts_pl)
        .tab_header(f"{district_name} - CPS School Budgeted Cuts")
        .fmt_number(columns=['Position loss/gain (budgeted)', 'CTU layoffs (budgeted)', 'SPED position loss/gain (budgeted)'], decimals=1)
        .fmt_percent(columns=['Position loss/gain (% of FY25 positions)', 'CTU layoffs (% of CTU positions)', 'SPED position loss/gain (% of FY25 SPED positions)'], decimals=0)
        .sub_missing(missing_text="")
        .tab_style(style=style.text(weight="bold"), locations=loc.body(rows=pl.col("School Name").str.contains("TOTAL")))
        )
    
    return operations_table, capital_table, cuts_table

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
        ["Chamber & District", "Legislator","Ward"]
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
        
    elif filter_type == "Legislator":  # Filter by Legislator
        # Legislator selection
        legislators = sorted(df['Legislator'].dropna().unique())
        selected_legislator = st.sidebar.selectbox("Select Legislator:", legislators)
        
        # Filter data
        filtered_df = df[df['Legislator'] == selected_legislator]
        
        # Display selection
        legislator_info = filtered_df.iloc[0]
        st.subheader(f"📊 {selected_legislator} ({legislator_info['Chamber']} - District {legislator_info['District']})")
    else:
        # Ward selection
        wards = sorted(df['Ward Number'].dropna().unique())
        selected_ward = st.sidebar.selectbox("Select Ward:", wards)
        
        # Filter data
        filtered_df = df[df['Ward Number'] == selected_ward]

        # Display selection
        st.subheader(f"📊 Ward {selected_ward}")
    # Define columns to display - only include baseline columns if they exist in filtered data
    base_display_columns = [
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
        'SPED Positions 15% Cut',
        "Total FY25",
        "Total CTU",
        "Total SPED",
        'Position loss/gain (budgeted)', 
        'Position loss/gain (% of FY25 positions)',
        'CTU layoffs (budgeted)',
        'CTU layoffs (% of CTU positions)',
        'SPED position loss/gain (budgeted)', 
        'SPED position loss/gain (% of FY25 SPED positions)'
    ]
    
    # Only add baseline columns if they exist in filtered data
    display_columns = base_display_columns.copy()
#    baseline_columns = ["Total FY25", 'Total CTU', 'Total SPED']
#    for col in baseline_columns:
#        if col in filtered_df.columns:
#            display_columns.append(col)
    

    
    # CONSOLIDATED DOWNLOAD SECTION
    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 Download Data")
    
    if len(filtered_df) > 0:
        # Prepare data for downloads
        all_data_df = filtered_df.copy()
        
        # Create district name for files
        if filter_type == "Chamber & District":
            district_name = f"{selected_chamber} District {selected_district}"
            filename_prefix = f"{selected_chamber.replace(' ', '_')}_District_{selected_district}"
        elif filter_type == "Legislator":
            # Get chamber and district info from filtered data
            legislator_info = filtered_df.iloc[0]
            district_name = f"{legislator_info['Chamber']} District {legislator_info['District']}"
            filename_prefix = f"{legislator_info['Chamber'].replace(' ', '_')}_District_{legislator_info['District']}"
        else:
            # Ward selection
            district_name = f"Ward {selected_ward}"
            filename_prefix = f"Ward_{selected_ward}"

        # CSV download of all data (NO COLUMNS - just direct sidebar)
        all_csv = all_data_df.to_csv(index=False)
        st.sidebar.download_button(
            label="📊 Download District Data (CSV)",
            data=all_csv,
            file_name=f"{filename_prefix}_all_data.csv",
            mime="text/csv",
            help="Download all capital and operations data as CSV"
        )
        
        if st.sidebar.button("📋 Generate Capital Needs Report", help="Create formatted report of capital needs data"):
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
                        <style>
                            body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
                            table {{ page-break-inside: avoid; }}
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
                        label="⬇️ Download Capital Report",
                        data=full_html.encode('utf-8'),
                        file_name=f"{filename_prefix}_capital_report.html",
                        mime="text/html"
                    )
                    
                    st.sidebar.success("✅ Capital report generated successfully!")
                    st.sidebar.info("💡 Tip: This will open in your browser. You can print from there.")

                except Exception as e:
                    st.sidebar.error(f"❌ Error generating report: {str(e)}")

        if st.sidebar.button("📋 Generate Operations Report", help="Create formatted report of operations data"):
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
                        <style>
                            body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
                            table {{ page-break-inside: avoid; }}
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
                        label="⬇️ Download Operations Report",
                        data=full_html.encode('utf-8'),
                        file_name=f"{filename_prefix}_operations_report.html",
                        mime="text/html"
                    )
                
                    
                    st.sidebar.success("✅ Operations report generated successfully!")
                    st.sidebar.info("💡 Tip: This will open in your browser. You can print from there.")

                except Exception as e:
                    st.sidebar.error(f"❌ Error generating report: {str(e)}")
        
        if st.sidebar.button("📋 Generate Budget Cuts Report", help="Create formatted report of budgeted cuts data"):
            with st.spinner("Generating Cuts Report..."):
                try:
                    # Create cuts dataframe with totals (need to include baseline columns)
                    # First check which columns are available
                    available_columns = ['School Name', 'Total FY25', 'Position loss/gain (budgeted)', 'Position loss/gain (% of FY25 positions)', 
                                       'Total CTU','CTU layoffs (budgeted)', 'CTU layoffs (% of CTU positions)', 
                                       'Total SPED','SPED position loss/gain (budgeted)', 'SPED position loss/gain (% of FY25 SPED positions)']
                    
                    # Create a totals row by summing all columns that aren't School Name
                    totals_row = filtered_df[available_columns].sum(numeric_only=True)
                    totals_row['School Name'] = f"{district_name} Total"
                    totals_row = pd.DataFrame(totals_row).T
                    # Recaululate percentages for totals
                    totals_row['Position loss/gain (% of FY25 positions)'] = abs(totals_row['Position loss/gain (budgeted)']) / totals_row['Total FY25']
                    totals_row['CTU layoffs (% of CTU positions)'] = abs(totals_row['CTU layoffs (budgeted)']) / totals_row['Total CTU']
                    totals_row['SPED position loss/gain (% of FY25 SPED positions)'] = abs(totals_row['SPED position loss/gain (budgeted)']) / totals_row['Total SPED']
                    cuts_df_with_total = pd.concat([filtered_df, totals_row], ignore_index=True)

                    
                    # Remove unwanted columns from display
                    cuts_df_with_total = cuts_df_with_total[[
                        'School Name',
                        'Position loss/gain (budgeted)',
                        'Position loss/gain (% of FY25 positions)',
                        'CTU layoffs (budgeted)',
                        'CTU layoffs (% of CTU positions)',
                        'SPED position loss/gain (budgeted)',
                        'SPED position loss/gain (% of FY25 SPED positions)'
                    ]]

                    # Convert to polars for great_tables
                    cuts_df_pl = pl.from_pandas(cuts_df_with_total)
                    
                    
                    
                    # Define column groups for spanners
                    position_cuts_cols = ["Position loss/gain (budgeted)", "Position loss/gain (% of FY25 positions)"]
                    ctu_cuts_cols = ["CTU layoffs (budgeted)", "CTU layoffs (% of CTU positions)"]
                    sped_cuts_cols = ["SPED position loss/gain (budgeted)", "SPED position loss/gain (% of FY25 SPED positions)"]
                    all_cuts_cols = position_cuts_cols + ctu_cuts_cols + sped_cuts_cols
                    
                    # Create great_tables cuts table
                    cuts_table = (
                        GT(cuts_df_pl)
                        .tab_header(f"{district_name} - CPS School Budgeted Position Cuts")
                        .tab_spanner(label="All Teachers and Paraprofessionals", columns=position_cuts_cols)
                        .tab_spanner(label="CTU Positions", columns=ctu_cuts_cols)
                        .tab_spanner(label="SPED Positions", columns=sped_cuts_cols)
                        .cols_label(
                            **{
                                "Position loss/gain (budgeted)": "Difference",
                                "Position loss/gain (% of FY25 positions)": "% of FY25 Positions",
                                "CTU layoffs (budgeted)": "Difference",
                                "CTU layoffs (% of CTU positions)": "% of CTU Positions",
                                "SPED position loss/gain (budgeted)": "Difference",
                                "SPED position loss/gain (% of FY25 SPED positions)": "% of SPED Positions"
                            }
                        )
                        .fmt_number(
                            columns=["Position loss/gain (budgeted)", "CTU layoffs (budgeted)", "SPED position loss/gain (budgeted)"],
                            decimals=0,
                        )
                        .fmt_percent(
                            columns=["Position loss/gain (% of FY25 positions)", "CTU layoffs (% of CTU positions)", "SPED position loss/gain (% of FY25 SPED positions)"],
                            decimals=1,
                        )
                        .sub_missing(missing_text="")
                        # Styling ----
                        .tab_style(
                            style=style.text(color="red"),
                            locations=loc.body(columns=all_cuts_cols)
                        )
                        .tab_style(
                            style=style.text(weight="bold"),
                            locations=loc.body(rows=pl.col("School Name").str.contains("Total"))
                        )
                    )
                    
                    # Get HTML content from great_tables
                    html_content = cuts_table._repr_html_()
                    
                    # Create complete HTML document
                    full_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <style>
                            body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
                            table {{ page-break-inside: avoid; }}
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
                        label="⬇️ Download Cuts Report",
                        data=full_html.encode('utf-8'),
                        file_name=f"{filename_prefix}_cuts_report.html",
                        mime="text/html"
                    )
                    
                    st.sidebar.success("✅ Cuts report generated successfully!")
                    st.sidebar.info("💡 Tip: This will open in your browser. You can print from there.")

                except Exception as e:
                    st.sidebar.error(f"❌ Error generating report: {str(e)}")
    
    # Create tabs for data display
    tab1, tab2, tab3 = st.tabs(["💰 Capital Needs ", " 🏢 Operations & Positions ", " ✂️ Cuts "])

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
    with tab3:
        st.subheader("Budgeted Cuts by School")
        # Define cuts columns        
        
        available_columns = ['School Name', 'Total FY25', 'Position loss/gain (budgeted)', 'Position loss/gain (% of FY25 positions)', 
                                       'Total CTU','CTU layoffs (budgeted)', 'CTU layoffs (% of CTU positions)', 
                                       'Total SPED','SPED position loss/gain (budgeted)', 'SPED position loss/gain (% of FY25 SPED positions)']
                    
        # Create a totals row by summing all columns that aren't School Name
        totals_row = filtered_df[available_columns].sum(numeric_only=True)
        totals_row['School Name'] = f"{district_name} Total"
        totals_row = pd.DataFrame(totals_row).T
        # Recaululate percentages for totals
        totals_row['Position loss/gain (% of FY25 positions)'] = abs(totals_row['Position loss/gain (budgeted)'] / totals_row['Total FY25'])
        totals_row['CTU layoffs (% of CTU positions)'] = abs(totals_row['CTU layoffs (budgeted)'] / totals_row['Total CTU'])
        totals_row['SPED position loss/gain (% of FY25 SPED positions)'] = abs(totals_row['SPED position loss/gain (budgeted)'] / totals_row['Total SPED'])
        cuts_df_with_total = pd.concat([filtered_df, totals_row], ignore_index=True)

        # Remove unwanted columns from display
        cuts_df_with_total = cuts_df_with_total[[
            'School Name',
            'Position loss/gain (budgeted)',
            'Position loss/gain (% of FY25 positions)',
            'CTU layoffs (budgeted)',
            'CTU layoffs (% of CTU positions)',
            'SPED position loss/gain (budgeted)',
            'SPED position loss/gain (% of FY25 SPED positions)'
        ]]
        
        # Format Position loss/gain (budgeted), CTU layoffs (budgeted), and SPED position loss/gain (budgeted) as integers. If missing than blank.
        number_cols = ['Position loss/gain (budgeted)', 'CTU layoffs (budgeted)', 'SPED position loss/gain (budgeted)']
        perc_cols = ['Position loss/gain (% of FY25 positions)', 'CTU layoffs (% of CTU positions)', 'SPED position loss/gain (% of FY25 SPED positions)']
        
        formatted_cuts_df = cuts_df_with_total.copy()
        for col in perc_cols:
            formatted_cuts_df[col] = formatted_cuts_df[col].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "")

        for col in number_cols:
            formatted_cuts_df[col] = formatted_cuts_df[col].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "")

        # Display cuts metrics (just sums)
        if len(filtered_df) > 0:
            col2, col3, col4, col5 = st.columns(4)
            with col2:
                position_change = cuts_df_with_total.iloc[-1]['Position loss/gain (budgeted)']
                st.metric("Total Position Loss/Gain", f"{position_change:,.0f}")
            with col3:
                position_perc = abs(cuts_df_with_total.iloc[-1]['Position loss/gain (% of FY25 positions)'])
                st.metric("% of Positions", f"{position_perc:,.0%}")
            with col4:
                sped_change = cuts_df_with_total.iloc[-1]['SPED position loss/gain (budgeted)']
                st.metric("SPED Position Loss/Gain", f"{sped_change:,.0f}")
            with col5:
                sped_perc = abs(cuts_df_with_total.iloc[-1]['SPED position loss/gain (% of FY25 SPED positions)'])
                st.metric("% of SPED Positions", f"{sped_perc:,.0%}")
        # Create and display the cuts table
        if len(filtered_df) > 0:
            # Create a custom HTML table for cuts data similar to operations. Make positions number int and % as 0.00%
            def create_html_table_cuts(df):
                cut2_columns = ['% of FY25 SPED Positions', '% of CTU Positions', '% of FY25 Positions']
                
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
                .cut2-column {
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
                        css_class = "cut2-column" if col in cut2_columns else ""
                        html += f'<td class="{css_class}">{value}</td>'
                    html += "</tr>"
                
                html += "</tbody></table></div>"
                return html
            
            # Display custom HTML table
            st.markdown(create_html_table_cuts(formatted_cuts_df), unsafe_allow_html=True) 
        else:
            st.warning("No schools found for the selected criteria.")
if __name__ == "__main__":
    main()