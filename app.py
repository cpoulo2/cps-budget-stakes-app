import streamlit as st
import pandas as pd
import numpy as np

# Add new imports for formatted tables
import polars as pl
from great_tables import GT, loc, style

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
    
    # Force light mode
    st.markdown("""
    <style>
    .stApp {
        background-color: white !important;
        color: black !important;
    }
    
    /* AGGRESSIVE WHITE SPACE FIXES */
    .main .block-container {
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: none !important;
        width: 100% !important;
    }
    
    /* Target the main content area specifically */
    .stApp > div:first-child > div:first-child > div:first-child {
        padding-left: 0rem !important;
    }
    
    /* Remove all default margins and padding */
    section.main > div {
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: none !important;
    }
    
    /* Force main content to use full width */
    .element-container {
        width: 100% !important;
        max-width: none !important;
    }
    
    /* Fix the content wrapper */
    .css-1d391kg, .css-1v0mbdj, .e1tzin5v2 {
        width: 100% !important;
        max-width: none !important;
        padding-left: 0rem !important;
    }
    
    /* Remove margin from app container */
    .stApp > div:first-child {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Ensure tables use full width */
    .stTabs [data-baseweb="tab-panel"] {
        padding-left: 0 !important;
        padding-right: 0 !important;
        width: 100% !important;
    }
    
    /* Fix any remaining margin issues */
    .stMarkdown {
        width: 100% !important;
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
    
    /* Ensure sidebar is also light */
    .css-1d391kg {
        background-color: #f0f2f6 !important;
    }
    
    /* Fix download buttons and other buttons */
    .stDownloadButton > button {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
    }
    
    .stDownloadButton > button:hover {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    /* Fix all button types */
    .stButton > button {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ddd !important;
    }
    
    .stButton > button:hover {
        background-color: #f0f2f6 !important;
        color: black !important;
    }
    
    /* Fix selectbox and other form elements */
    .stSelectbox > div > div {
        background-color: white !important;
        color: black !important;
    }
    
    /* Fix radio buttons */
    .stRadio > div {
        background-color: white !important;
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
        
        # HTML download of operations table
        if st.sidebar.button("📋 Generate Operations Report", help="Create formatted HTML report of operations data"):
            with st.spinner("Generating Operations Report..."):
                try:
                    operations_table, _ = create_formatted_tables(filtered_df, district_name)
                    
                    html_data = create_html_download(operations_table, f"{district_name} - Operations Report")
                    
                    st.sidebar.download_button(
                        label="⬇️ Download Operations Report (HTML)",
                        data=html_data,
                        file_name=f"{filename_prefix}_operations.html",
                        mime="text/html"
                    )
                    st.sidebar.success("✅ Operations report ready!")
                except Exception as e:
                    st.sidebar.error(f"Error: {str(e)}")
        
        # HTML download of capital table
        if st.sidebar.button("🏗️ Generate Capital Report", help="Create formatted HTML report of capital needs data"):
            with st.spinner("Generating Capital Report..."):
                try:
                    _, capital_table = create_formatted_tables(filtered_df, district_name)
                    
                    html_data = create_html_download(capital_table, f"{district_name} - Capital Needs Report")
                    
                    st.sidebar.download_button(
                        label="⬇️ Download Capital Report (HTML)",
                        data=html_data,
                        file_name=f"{filename_prefix}_capital.html",
                        mime="text/html"
                    )
                    st.sidebar.success("✅ Capital report ready!")
                except Exception as e:
                    st.sidebar.error(f"Error: {str(e)}")
    else:
        st.sidebar.info("Select a district or legislator to enable downloads.")
    
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
    tab1, tab2 = st.tabs(["💰 Capital Needs", "🏢 Operations & Positions"])
    
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
                    margin: 0 auto; !important;  /* Changed from "margin: 0 auto;" */
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
        
        # Display operations metrics with better spacing
        if len(filtered_df) > 0:
            # Use single column layout to prevent cut-off
            st.metric("Schools in District", len(filtered_df))
            st.metric("Total Possible Budget Cuts (15%)", format_currency(operations_totals['Budget Cut (15%)']))
            st.metric("Total Position Losses (15%)", format_positions(operations_totals['Position Loss (15%)']))
            st.metric("SPED Position Losses (15%)", format_positions(operations_totals['SPED Loss (15%)']))
        
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
                    margin: 0 !important;  /* Changed from "margin: 0 auto;" */
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