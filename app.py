import streamlit as st
import pandas as pd
import numpy as np

# Configure page
st.set_page_config(
    page_title="CPS Budget Stakes Dashboard",
    page_icon="🏫",
    layout="wide"
)

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
    st.markdown("**Filter schools by legislative district to view capital needs and budget impact**")
    
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
    
    # Calculate totals
    numeric_columns = [col for col in display_columns if col != 'School Name']
    totals = {}
    totals['School Name'] = 'TOTAL'
    
    for col in numeric_columns:
        totals[col] = display_df[col].sum()
    
    # Add totals row
    totals_df = pd.DataFrame([totals])
    final_df = pd.concat([display_df, totals_df], ignore_index=True)
    
    # Format currency and numbers
    def format_currency(val):
        if pd.isna(val):
            return ""
        return f"${val:,.0f}"
    
    def format_positions(val):
        if pd.isna(val):
            return ""
        return f"{val:.1f}"
    
    # Apply formatting
    currency_cols = ['Immediate Capital Needs', 'Total Capital Needs', 'Operational Budget FY25', 'Operations 7% Cut', 'Operations 15% Cut']
    position_cols = ['Positions', 'Positions 7% Cut', 'Positions 15% Cut', 'SPED Positions', 'SPED Positions 7% Cut', 'SPED Positions 15% Cut']
    
    formatted_df = final_df.copy()
    for col in currency_cols:
        formatted_df[col] = formatted_df[col].apply(format_currency)
    for col in position_cols:
        formatted_df[col] = formatted_df[col].apply(format_positions)
    
    # Display metrics
    if len(filtered_df) > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Schools", len(filtered_df))
        with col2:
            st.metric("Total Capital Needs", format_currency(totals['Total Capital Needs']))
        with col3:
            st.metric("Total Budget FY25", format_currency(totals['Operational Budget FY25']))
        with col4:
            st.metric("Total Positions", format_positions(totals['Positions']))
    
    # Display table
    st.subheader("📋 School Data")
    
    if len(filtered_df) > 0:
        # Highlight totals row
        def highlight_totals(row):
            if row.name == len(formatted_df) - 1:  # Last row (totals)
                return ['background-color: #f0f0f0; font-weight: bold'] * len(row)
            else:
                return [''] * len(row)
        
        styled_df = formatted_df.style.apply(highlight_totals, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Download button
        st.subheader("💾 Download Data")
        
        # Prepare download data (unformatted for CSV)
        download_df = final_df.copy()
        
        csv = download_df.to_csv(index=False)
        
        filename = f"cps_budget_data_{selected_chamber.replace(' ', '_')}_{selected_district}.csv" if filter_type == "Chamber & District" else f"cps_budget_data_{selected_legislator.replace(' ', '_').replace('.', '')}.csv"
        
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=filename,
            mime="text/csv"
        )
        
    else:
        st.warning("No schools found for the selected criteria.")
    
    # Additional info
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Data Info:**")
    st.sidebar.markdown(f"• Total Schools: {len(df)}")
    st.sidebar.markdown(f"• Chambers: {len(df['Chamber'].unique())}")
    st.sidebar.markdown(f"• Districts: {len(df['District'].unique())}")

if __name__ == "__main__":
    main()