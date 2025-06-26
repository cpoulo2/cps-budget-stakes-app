import streamlit as st
import pandas as pd
import numpy as np

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
    # Force light mode
    st.markdown("""
    <style>
    .stApp {
        background-color: white !important;
        color: black !important;
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
    
        # Create tabs after filtering data
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
        
        # Display capital table
        def highlight_totals_capital(row):
            if row.name == len(capital_final_df) - 1:  # Last row (totals)
                return ['background-color: #f0f0f0; font-weight: bold'] * len(row)
            else:
                return [''] * len(row)
        
        if len(filtered_df) > 0:
            # Create custom HTML table for capital data
            def create_html_table_capital(df):
                # No cut columns for capital table since it's just showing capital needs
                
                html = """
                <style>
                .custom-table-capital {
                    border-collapse: collapse;
                    width: 100%;
                    font-family: 'Source Sans Pro', sans-serif;
                    font-size: 14px;
                }
                .custom-table-capital th {
                    background-color: white !important;
                    font-weight: bold !important;
                    text-align: center !important;
                    padding: 10px;
                    border: 1px solid #ddd;
                    color: black !important;
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
                        html += f'<td>{value}</td>'  # No special styling for capital table
                    html += "</tr>"
                
                html += "</tbody></table>"
                return html
            
            # Display custom HTML table for CAPITAL data
            st.markdown(create_html_table_capital(capital_final_df), unsafe_allow_html=True)
            
            # Download capital data
            capital_csv = capital_final_df.to_csv(index=False)
            filename_capital = f"capital_needs_{selected_chamber.replace(' ', '_')}_{selected_district}.csv" if filter_type == "Chamber & District" else f"capital_needs_{selected_legislator.replace(' ', '_').replace('.', '')}.csv"
            st.download_button(
                label="📥 Download Capital Data as CSV",
                data=capital_csv,
                file_name=filename_capital,
                mime="text/csv"
            )
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
        
        # Enhanced styling function with red cuts
        def style_operations_dataframe(df):
            # Define cut columns that should be red
            cut_columns = ['Budget Cut (7%)', 'Budget Cut (15%)', 'Position Loss (7%)', 'Position Loss (15%)', 'SPED Loss (7%)', 'SPED Loss (15%)']
            
            # Create styler object
            styler = df.style
            
            # Highlight totals row
            styler = styler.apply(
                lambda row: ['background-color: #f0f0f0; font-weight: bold'] * len(row) 
                if row.name == len(df) - 1 else [''] * len(row),
                axis=1
            )
            
            # Make cut columns red
            for col in cut_columns:
                if col in df.columns:
                    styler = styler.applymap(
                        lambda x: 'color: red',
                        subset=[col]
                    )
            
            # Center all numeric columns (all except School Name)
            numeric_cols = [col for col in df.columns if col != 'School Name']
            styler = styler.set_properties(subset=numeric_cols, **{'text-align': 'center'})
            
            return styler
        
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
                }
                .custom-table th {
                    background-color: white !important;
                    font-weight: bold !important;
                    text-align: center !important;
                    padding: 10px;
                    border: 1px solid #ddd;
                    color: black !important;
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
                
                html += "</tbody></table>"
                return html
            
            # Display custom HTML table
            st.markdown(create_html_table(formatted_operations_df), unsafe_allow_html=True)
             
            # Download operations data
            operations_csv = operations_final_df.to_csv(index=False)
            filename_operations = f"operations_data_{selected_chamber.replace(' ', '_')}_{selected_district}.csv" if filter_type == "Chamber & District" else f"operations_data_{selected_legislator.replace(' ', '_').replace('.', '')}.csv"
            st.download_button(
                label="📥 Download Operations Data as CSV",
                data=operations_csv,
                file_name=filename_operations,
                mime="text/csv"
            )
        else:
            st.warning("No schools found for the selected criteria.")


if __name__ == "__main__":
    main()