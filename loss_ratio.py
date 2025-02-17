import streamlit as st
import matplotlib.colors as mcolors
import plotly.express as px
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from itertools import chain
from matplotlib.ticker import FuncFormatter
from datetime import datetime
import matplotlib.dates as mdates

def display_loss_ratio():

    # Centered and styled main title using inline styles
    st.markdown('''
        <style>
            .main-title {
                color: #e66c37; /* Title color */
                text-align: center; /* Center align the title */
                font-size: 3rem; /* Title font size */
                font-weight: bold; /* Title font weight */
                margin-bottom: .5rem; /* Space below the title */
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1); /* Subtle text shadow */
            }
            div.block-container {
                padding-top: 2rem; /* Padding for main content */
            }
        </style>
    ''', unsafe_allow_html=True)

    st.markdown('<h1 class="main-title">CLAIMS ANAYSIS - LOSS RATIO VIEW</h1>', unsafe_allow_html=True)

    # Filepaths and sheet names
    filepath_premiums = "JAN-NOV 2024 GWP.xlsx"
    sheet_name_new_business = "2023"
    sheet_name_endorsements = "2024"

    filepath_claims = "Claims.xlsx"
    sheet_name1 = "2023 claims"
    sheet_name2 = "2024 claims"

    # Read premium data
    df_2023 = pd.read_excel(filepath_premiums, sheet_name=sheet_name_new_business)
    df_2024 = pd.read_excel(filepath_premiums, sheet_name=sheet_name_endorsements)

    # Read claims data
    dfc_2023 = pd.read_excel(filepath_claims, sheet_name=sheet_name1)
    dfc_2024 = pd.read_excel(filepath_claims, sheet_name=sheet_name2)

    # Concatenate premiums and claims
    df_premiums = pd.concat([df_2023, df_2024])
    df_claims = pd.concat([dfc_2023, dfc_2024])

    # Standardize date formats
    df_premiums['Start Date'] = pd.to_datetime(df_premiums['Start Date'])
    df_premiums['End Date'] = pd.to_datetime(df_premiums['End Date'])
    df_claims['Claim Created Date'] = pd.to_datetime(df_claims['Claim Created Date'], errors='coerce')

    # Add 'Month' and 'Year' columns
    df_premiums['Month'] = df_premiums['Start Date'].dt.strftime('%B')
    df_premiums['Year'] = df_premiums['Start Date'].dt.year
    df_claims['Month'] = df_claims['Claim Created Date'].dt.strftime('%B')
    df_claims['Year'] = df_claims['Claim Created Date'].dt.year

    # Rename 'Employer Name' in claims data for consistency
    df_claims.rename(columns={'Employer Name': 'Client Name'}, inplace=True)


    # Function to prioritize cover types and mark prioritized rows
    def prioritize_and_mark(group):
        if 'Renewal' in group['Cover Type'].values:
            return group[group['Cover Type'] == 'Renewal'].assign(Is_Prioritized=True)
        elif 'New' in group['Cover Type'].values:
            return group[group['Cover Type'] == 'New'].assign(Is_Prioritized=True)
        else:
            return group.assign(Is_Prioritized=False)

    # Apply prioritization and marking
    premiums_grouped = df_premiums.groupby(['Client Name', 'Product', 'Year']).apply(prioritize_and_mark).reset_index(drop=True)

    # Filter endorsements
    endorsements = premiums_grouped[premiums_grouped['Cover Type'] == 'Endorsement']

    # Merge endorsements with prioritized premiums (Renewal or New)
    merged_endorsements = pd.merge(
        endorsements,
        premiums_grouped[premiums_grouped['Cover Type'].isin(['New', 'Renewal'])],
        on=['Client Name', 'Product', 'Year'],
        suffixes=('_endorsement', '_prioritized')
    )

    # Filter valid endorsements (within the premium period)
    valid_endorsements = merged_endorsements[
        (merged_endorsements['Start Date_endorsement'] >= merged_endorsements['Start Date_prioritized']) &
        (merged_endorsements['End Date_endorsement'] <= merged_endorsements['End Date_prioritized'])
    ]

    # Aggregate endorsement premiums
    endorsement_grouped = valid_endorsements.groupby(['Client Name', 'Product', 'Year']).agg({
        'Total_endorsement': 'sum'
    }).reset_index().rename(columns={'Total_endorsement': 'Endorsement Premium'})

    # Merge endorsement premiums back into prioritized premiums
    final_premiums = pd.merge(
        premiums_grouped,
        endorsement_grouped,
        on=['Client Name', 'Product', 'Year'],
        how='left'
    )

    # Calculate total premium (base + endorsements)
    final_premiums['Total Premium'] = (
        final_premiums['Total'] + 
        final_premiums['Endorsement Premium'].fillna(0)
    )

    # Add 'Month' column
    final_premiums['Month'] = final_premiums['Start Date'].dt.strftime('%B')

    # Compute time-based metrics
    current_date = pd.Timestamp.now()
    client_product_data = final_premiums.groupby(['Client Name', 'Product', 'Year']).agg({
        'Start Date': 'min',
        'End Date': 'max',
        'Total Premium': 'sum'
    }).reset_index()

    client_product_data['Days Since Start'] = (current_date - client_product_data['Start Date']).dt.days
    client_product_data['days_on_cover'] = (client_product_data['End Date'] - client_product_data['Start Date']).dt.days
    client_product_data['Earned Premium'] = (
        client_product_data['Total Premium'] * 
        client_product_data['Days Since Start'] / 
        client_product_data['days_on_cover']
    )

    # Merge earned premium calculations
    premiums_with_earned = pd.merge(
        final_premiums,
        client_product_data[['Client Name', 'Product', 'Year', 'Days Since Start', 'days_on_cover', 'Earned Premium']],
        on=['Client Name', 'Product', 'Year'],
        how='left'
    )

    # Final premium DataFrame
    premiums_final = premiums_with_earned[
        ['Client Name', 'Product', 'Year', 'Start Date', 'End Date', 'Month', 'Total Premium', 
        'Endorsement Premium', 'Cover Type', 'Is_Prioritized', 'Days Since Start', 'days_on_cover', 'Earned Premium']
    ]

    # Filter only prioritized rows for claims matching
    premiums_prioritized = premiums_final[premiums_final['Is_Prioritized']].reset_index(drop=True)

    # Match claims to prioritized premiums
    claims_within_range = pd.merge(
        df_claims,
        premiums_prioritized[['Client Name', 'Product', 'Year', 'Start Date', 'End Date']],
        on=['Client Name', 'Product', 'Year'],
        how='inner'
    )

    # Filter claims that fall within the premium period
    claims_within_range = claims_within_range[
        (claims_within_range['Claim Created Date'] >= claims_within_range['Start Date']) &
        (claims_within_range['Claim Created Date'] <= claims_within_range['End Date'])
    ]

    # Aggregate claims by client-product-year
    claims_aggregated = claims_within_range.groupby(['Client Name', 'Product', 'Year']).agg({
        'Claim ID': 'count',  # Number of claims
        'Claim Amount': 'sum',  # Total claim amount
        'Approved Claim Amount': 'sum'  # Approved claim amount (if available)
    }).reset_index()

    # Rename columns for clarity
    claims_aggregated.rename(columns={
        'Claim ID': 'Number of Claims',
        'Claim Amount': 'Total Claims',
        'Approved Claim Amount': 'Approved Claims'
    }, inplace=True)

    # Merge claims with premiums (outer join to include all premiums, even without claims)
    final_data = pd.merge(
        premiums_final,
        claims_aggregated,
        on=['Client Name', 'Product', 'Year'],
        how='outer'
    )

    # Fill missing values (e.g., no claims for some clients/products)
    final_data['Number of Claims'] = final_data['Number of Claims'].fillna(0).astype(int)
    final_data['Total Claims'] = final_data['Total Claims'].fillna(0)
    final_data['Approved Claims'] = final_data['Approved Claims'].fillna(0)


    df=final_data


    df['Client Name'] = df['Client Name'].astype(str)
    df["Client Name"] = df["Client Name"].str.upper()


    # Inspect the merged DataFrame

    # Sidebar styling and logo
    st.markdown("""
        <style>
        .sidebar .sidebar-content {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        .sidebar .sidebar-content h2 {
            color: #007BFF; /* Change this color to your preferred title color */
            font-size: 1.5em;
            margin-bottom: 20px;
            text-align: center;
        }
        .sidebar .sidebar-content .filter-title {
            color: #e66c37;
            font-size: 1.2em;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 10px;
            text-align: center;
        }
        .sidebar .sidebar-content .filter-header {
            color: #e66c37; /* Change this color to your preferred header color */
            font-size: 2.5em;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 20px;
            text-align: center;
        }
        .sidebar .sidebar-content .filter-multiselect {
            margin-bottom: 15px;
        }
        .sidebar .sidebar-content .logo {
            text-align: center;
            margin-bottom: 20px;
        }
        .sidebar .sidebar-content .logo img {
            max-width: 80%;
            height: auto;
            border-radius: 50%;
        }
                
        </style>
        """, unsafe_allow_html=True)

    # Dictionary to map month names to their order
    month_order = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12
    }
    # Define the mapping of months to quarters
    month_to_quarter = {
        "January": "Q1", "February": "Q1", "March": "Q1",
        "April": "Q2", "May": "Q2", "June": "Q2",
        "July": "Q3", "August": "Q3", "September": "Q3",
        "October": "Q4", "November": "Q4", "December": "Q4"
    }
    # Filter DataFrame by months in `month_order`
    df = df[df['Month'].isin(month_order)]

    # Sort months based on their order
    sorted_months = sorted(df['Month'].dropna().unique(), key=lambda x: pd.to_datetime(x, format='%B').month)

    df['Quarter'] = "Q" + df['Start Date'].dt.quarter.astype(str)


    # Create a three-column layout
    col1, col2, col3, col4 = st.columns(4)

    # Year selector (allow multiple selections)
    with col1:
        years = sorted(df['Year'].dropna().unique())
        selected_years = st.multiselect(
            "Select Years",
            options=years,
            default=[years[-1]],  # Default to the most recent year
            key="year_selector_multi"
        )
        if selected_years:
            df = df[df['Year'].isin(selected_years)]

    # Month selector (allow multiple selections)
    with col2:
        selected_months = st.multiselect(
            "Select Months",
            options=sorted_months,
            key="month_select_multi"
        )
        if selected_months:
            df = df[df['Month'].isin(selected_months)]

        # Dynamically calculate the quarters based on selected months
        if selected_months:
            suggested_quarters = list(set(month_to_quarter[month] for month in selected_months))
        else:
            suggested_quarters = sorted(df['Quarter'].dropna().unique())  # Default to all quarters

    # Quarter selector (allow manual selection, with dynamic suggestions)
    with col3:
        quarters = sorted(df['Quarter'].dropna().unique())
        selected_quarters = st.multiselect(
            "Select Quarters",
            options=quarters,
            key="filter_quarter_selector_multiselect"
        )
        if selected_quarters:
            df = df[df['Quarter'].isin(selected_quarters)]

    # Business Line selector (pre-select all options by default)
    with col4:
        business_lines = sorted(df['Product'].dropna().unique()) if 'Product' in df.columns else []
        selected_business_lines = st.multiselect(
            "Select Business Lines",
            options=business_lines,
            key="filter_business_line_selector_multiselect"
        )
        if selected_business_lines:
            df = df[df['Product'].isin(selected_business_lines)]


    # Create a three-column layout
    col1, col2 = st.columns(2)

    # Claim Status selector (pre-select one status by default)
    with col2:
        business_lines = sorted(df['Client Name'].dropna().unique()) if 'Client Name' in df.columns else []
        
        # Pre-select only one status by default (e.g., "Approved")
        selected_business_lines = st.multiselect(
            "Select Employer Group",
            options=business_lines,
            key="outlier_multiselect"
        )
        
        # Apply filter for Claim Status
        if selected_business_lines:
            df = df[df['Client Name'].isin(selected_business_lines)]


    # Claim Status selector (pre-select one status by default)
    with col1:
        business_lines = sorted(df['Cover Type'].dropna().unique()) if 'Cover Type' in df.columns else []
        
        # Pre-select only one status by default (e.g., "Approved")
        selected_business_lines = st.multiselect(
            "Select Cover Type",
            options=business_lines,
            key="cover_multiselect"
        )
        
        # Apply filter for Claim Status
        if selected_business_lines:
            df = df[df['Cover Type'].isin(selected_business_lines)]


    # Dynamically calculate the date range based on selected filters
    if selected_months:
        # Filter DataFrame by selected months
        df_filtered = df[df['Month'].isin(selected_months)]
    else:
        df_filtered = df

    # Get the minimum and maximum dates from the filtered DataFrame
    startDate = df_filtered["Start Date"].min()
    endDate = df_filtered["Start Date"].max()


    # Define CSS for the styled date input boxes
    st.markdown("""
        <style>
        .date-input-box {
            border-radius: 10px;
            text-align: left;
            margin: 5px;
            font-size: 1.2em;
            font-weight: bold;
        }
        .date-input-title {
            font-size: 1em;
            margin-bottom: 2px;
        }
        .date-range-title {
            font-size: 1.5em;
            font-weight: bold;
            color: #e66c37; /* Orange color for emphasis */
            margin-bottom: 10px;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)
    # Add a title for the date range selection
    st.markdown('<div class="date-range-title">Select Claim Date Range</div>', unsafe_allow_html=True)

    # Create 2-column layout for date inputs
    col1, col2 = st.columns(2)

    # Function to display date input in styled boxes
    def display_date_input(col, title, default_date, min_date, max_date, key):
        col.markdown(f"""
            <div class="date-input-box">
                <div class="date-input-title">{title}</div>
            </div>
            """, unsafe_allow_html=True)
        return col.date_input("", default_date, min_value=min_date, max_value=max_date, key=key)

    # Display date inputs with unique keys
    with col1:
        date1 = pd.to_datetime(display_date_input(col1, "Start Date", startDate, startDate, endDate, key="date_start_selector_multiselect"))

    with col2:
        date2 = pd.to_datetime(display_date_input(col2, "End Date", endDate, startDate, endDate, key="date_end_selector_multiselect"))

    # Filter the DataFrame based on the selected date range
    if date1 and date2:
        df = df[(df["Start Date"] >= date1) & (df["Start Date"] <= date2)]




    # Function to prioritize cover types and mark prioritized rows
    def prioritize_and_mark(group):
        if 'Renewal' in group['Cover Type'].values:
            return group[group['Cover Type'] == 'Renewal'].assign(Is_Prioritized=True)
        elif 'New' in group['Cover Type'].values:
            return group[group['Cover Type'] == 'New'].assign(Is_Prioritized=True)
        else:
            return group.assign(Is_Prioritized=False)

    # Apply prioritization and marking
    df = df.groupby(['Client Name', 'Product', 'Year']).apply(prioritize_and_mark).reset_index(drop=True)


    # Current date
    current_date = pd.Timestamp.now()

    # Compute time-based metrics for prioritized rows
    df['Days Since Start'] = (
        df.apply(lambda row: (current_date - row['Start Date']).days if row['Is_Prioritized'] else 0, axis=1)
    )
    df['days_on_cover'] = (
        df.apply(lambda row: (row['End Date'] - row['Start Date']).days if row['Is_Prioritized'] else 0, axis=1)
    )

    # Calculate Earned Premium for each row
    df['Earned Premium'] = (
        df.apply(
            lambda row: (row['Total Premium'] * row['Days Since Start']) / row['days_on_cover']
            if row['Is_Prioritized'] and row['days_on_cover'] != 0 else 0,
            axis=1
        )
    )
    df['Loss Ratio'] = (
        df.apply(
            lambda row: (row['Approved Claims'] / row['Earned Premium'])
            if row['Is_Prioritized'] and row['Earned Premium'] != 0 else 0,
            axis=1
        )
    )
    df['Loss Ratio Rate'] = (
        df.apply(
            lambda row: (row['Approved Claims'] / row['Earned Premium']) * 100 
            if row['Is_Prioritized'] and row['Earned Premium'] != 0 else 0,
            axis=1
        )
    )


    # Set claims metrics to 0 for non-prioritized rows
    df['Number of Claims'] = df.apply(lambda row: row['Number of Claims'] if row['Is_Prioritized'] else 0, axis=1)
    df['Total Claims'] = df.apply(lambda row: row['Total Claims'] if row['Is_Prioritized'] else 0, axis=1)
    df['Approved Claims'] = df.apply(lambda row: row['Approved Claims'] if row['Is_Prioritized'] else 0, axis=1)

    st.dataframe(df)

    if not df.empty:
        scale = 1_000_000  # For millions

        # Filter datasets based on cover types
        df_new = df[df['Cover Type'] == 'New']
        df_renew = df[df['Cover Type'] == 'Renewal']
        df_end = df[df['Cover Type'] == 'Endorsement']
        df_combined = df[df['Cover Type'].isin(['New', 'Renewal'])]


        # Total Claim Amount (Approved Claims)
        total_claim_amount = (df["Total Claims"].sum()) / scale
        average_claim_amount = (df["Total Claims"].mean()) / scale
        average_approved_claim_amount = (df["Approved Claims"].mean()) / scale

        # Client and Claim Metrics
        total_clients = df["Client Name"].nunique()
        total_claims = df["Number of Claims"].sum()  # Sum of unique claims
        num_new = df_new["Client Name"].nunique()
        num_renew = df_renew["Client Name"].nunique()
        num_end = df_end["Client Name"].nunique()


        # Premium Metrics (includes endorsements)
        total_new_premium = (df_new["Total Premium"].sum()) / scale
        total_renew_premium = (df_renew["Total Premium"].sum()) / scale
        total_premium = (df["Total Premium"].sum()) / scale  # Only New + Renewal
        total_endorsement_premium = (df_end["Total Premium"].sum()) / scale

        # Days Metrics (only from prioritized rows)
        prioritized_df = df[df['Is_Prioritized']]
        total_days_since_start = prioritized_df["Days Since Start"].sum()
        total_days_on_cover = prioritized_df["days_on_cover"].sum()

        # Approved Claims Metrics
        total_approved_claim_amount = (df["Approved Claims"].sum()) / scale
        percent_approved = (total_approved_claim_amount / total_claim_amount) * 100 if total_claim_amount != 0 else 0

        # Aggregate Earned Premium (only from prioritized rows)
        total_earned_premium = (prioritized_df["Earned Premium"].sum())/scale

        # Loss Ratio Calculation (aggregate level)
        loss_ratio_amount = (
            total_approved_claim_amount / total_earned_premium if total_earned_premium != 0 else 0
        )
        df['Loss Ratio'] = (total_approved_claim_amount / total_earned_premium)

        loss_ratio = loss_ratio_amount * 100



        # Create 4-column layout for metric cards# Define CSS for the styled boxes and tooltips
        st.markdown("""
            <style>
            .custom-subheader {
                color: #e66c37;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
                padding: 10px;
                border-radius: 5px;
                display: inline-block;
            }
            .metric-box {
                padding: 10px;
                border-radius: 10px;
                text-align: center;
                margin: 10px;
                font-size: 1.2em;
                font-weight: bold;
                box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
                border: 1px solid #ddd;
                position: relative;
            }
            .metric-title {
                color: #e66c37; /* Change this color to your preferred title color */
                font-size: 0.9em;
                margin-bottom: 10px;
            }
            .metric-value {
                color: #009DAE;
                font-size: 1em;
            }

            </style>
            """, unsafe_allow_html=True)


        # Function to display metrics in styled boxes with tooltips
        def display_metric(col, title, value):
            col.markdown(f"""
                <div class="metric-box">
                    <div class="metric-title">{title}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """, unsafe_allow_html=True)


        st.markdown('<h2 class="custom-subheader">For all Sales in Numbers</h2>', unsafe_allow_html=True)
        cols1, cols2, cols3 = st.columns(3)
        display_metric(cols1, "Number of Clients", f"{total_clients:,.0f}")
        display_metric(cols2, "Number of New Business", f"{num_new:,.0f}")
        display_metric(cols3, "Number of Renewals", f"{num_renew:,.0f}")
        display_metric(cols1, "Number of Endorsements", f"{num_end:,.0f} ")
        display_metric(cols2, "Number of Claims", f"{total_claims:,.0f}")

        st.markdown('<h2 class="custom-subheader">For all Sales Amount</h2>', unsafe_allow_html=True)
        cols1, cols2, cols3 = st.columns(3)
        display_metric(cols1, "Total Premium", f"{total_premium:,.0f} M")
        display_metric(cols2, "Total New Business Premium", f"{total_new_premium:,.0f} M")
        display_metric(cols3, "Total Renewal Premium", f"{total_renew_premium:,.0f} M")
        display_metric(cols1, "Total Endorsement Premium", f"{total_endorsement_premium:,.1f} M")
        display_metric(cols2, "Total Claim Amount", f"{total_claim_amount:,.0f} M")
        display_metric(cols3, "Average Claim Amount", f"{average_claim_amount:,.0f} M")


        st.markdown('<h2 class="custom-subheader">For Loss Ratio</h2>', unsafe_allow_html=True)
        cols1, cols2, cols3 = st.columns(3)
        display_metric(cols1, "Days Since Premium Start", f"{total_days_since_start:,.0f} days")
        display_metric(cols2, "Premium Duration (Days)", f"{total_days_on_cover:,.0f} days")
        display_metric(cols3, "Earned Premium", f"{total_earned_premium:,.0f} M")
        display_metric(cols1, "Approved Claim Amount", f"{total_approved_claim_amount:,.0f} M")
        display_metric(cols2, "Loss Ratio", f"{loss_ratio_amount:,.1f} M")
        display_metric(cols3, "Percentage Loss Ratio", f"{loss_ratio:,.0f} %")






    
        # Sidebar styling and logo
        st.markdown("""
            <style>
            .sidebar .sidebar-content {
                background-color: #f0f2f6;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
            .sidebar .sidebar-content h3 {
                color: #007BFF; /* Change this color to your preferred title color */
                font-size: 1.5em;
                margin-bottom: 20px;
                text-align: center;
            }
            .sidebar .sidebar-content .filter-title {
                color: #e66c37;
                font-size: 1.2em;
                font-weight: bold;
                margin-top: 20px;
                margin-bottom: 10px;
                text-align: center;
            }
            .sidebar .sidebar-content .filter-header {
                color: #e66c37; /* Change this color to your preferred header color */
                font-size: 2.5em;
                font-weight: bold;
                margin-top: 20px;
                margin-bottom: 20px;
                text-align: center;
            }
            .sidebar .sidebar-content .filter-multiselect {
                margin-bottom: 15px;
            }
            .sidebar .sidebar-content .logo {
                text-align: center;
                margin-bottom: 20px;
            }
            .sidebar .sidebar-content .logo img {
                max-width: 80%;
                height: auto;
                border-radius: 50%;
            }
                    
            </style>
            """, unsafe_allow_html=True)

        cols1, cols2 = st.columns(2)

        custom_colors = ["#009DAE", "#e66c37", "#461b09", "#f8a785", "#CC3636"]

        # Group data by 'Start Date' to calculate daily loss ratio
        daily_loss_ratio = (
            df.groupby(df['Start Date'].dt.strftime("%Y-%m-%d"))  # Group by date (day level)
            .agg(
                Total_Claims=("Approved Claims", "sum"),  # Sum of approved claims
                Earned_Premium=("Earned Premium", "sum")       # Sum of earned premium
            )
            .reset_index()
        )

        # Calculate loss ratio for each day
        daily_loss_ratio["Loss Ratio"] = (
            daily_loss_ratio["Total_Claims"] / daily_loss_ratio["Earned_Premium"]
        ) * 100
        daily_loss_ratio = daily_loss_ratio.fillna(0)  # Handle days with no claims or premiums

        with cols1:
            # Create the area chart
            fig_daily_loss_ratio_area = go.Figure()

            # Add area trace
            fig_daily_loss_ratio_area.add_trace(go.Scatter(
                x=daily_loss_ratio['Start Date'],  # X-axis: Start Date (day level)
                y=daily_loss_ratio['Loss Ratio'],  # Y-axis: Loss Ratio
                mode='lines',
                fill='tozeroy',  # Fill area under the line
                name='Loss Ratio',
                text=[f"{value:.1f}%" for value in daily_loss_ratio['Loss Ratio']],  # Tooltip format
                hoverinfo='x+y+text+name',
                line=dict(color=custom_colors[0])
            ))

            # Update layout
            fig_daily_loss_ratio_area.update_layout(
                xaxis_title="Date",
                yaxis_title="Loss Ratio (%)",
                font=dict(color="Black"),
                xaxis=dict(
                    title_font=dict(size=14),
                    tickfont=dict(size=12),
                    type='date',  # Ensure proper date formatting
                    tickformat="%Y-%m-%d"  # Display date in YYYY-MM-DD format
                ),
                yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                margin=dict(l=0, r=0, t=30, b=50),
                height=450
            )

            # Display the chart in Streamlit
            st.markdown('<h3 class="custom-subheader">Daily Loss Ratio Over Time</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig_daily_loss_ratio_area, use_container_width=True)

        # Group data by 'Year' and calculate the sum of Total Premium, Approved Claims, and Earned Premium
        yearly_data_combined = df.groupby('Year')['Total Premium'].sum().reset_index(name='Total Premium')
        yearly_data_earned = df.groupby('Year')['Approved Claims'].sum().reset_index(name='Approved Claim Amount')
        yearly_data_endorsements = df.groupby('Year')['Earned Premium'].sum().reset_index(name='Earned Premium')

        # Merge the data frames on 'Year'
        yearly_data = pd.merge(yearly_data_combined, yearly_data_earned, on='Year', how='outer')
        yearly_data = pd.merge(yearly_data, yearly_data_endorsements, on='Year', how='outer')


        with cols2:
            # Fill NaN values with 0
            yearly_data = yearly_data.fillna(0)

            # Create the grouped bar chart for Total Premium and Endorsements
            fig_yearly_avg_premium = go.Figure()

            # Add Total Premium bar trace
            fig_yearly_avg_premium.add_trace(go.Bar(
                x=yearly_data['Year'],
                y=yearly_data['Total Premium'],
                name='Total Premium',
                textposition='inside',
                textfont=dict(color='white'),
                hoverinfo='x+y+name',
                marker_color=custom_colors[0]
            ))
            # Add Total Premium bar trace
            fig_yearly_avg_premium.add_trace(go.Bar(
                x=yearly_data['Year'],
                y=yearly_data['Earned Premium'],
                name='Earned Premium',
                textposition='inside',
                textfont=dict(color='white'),
                hoverinfo='x+y+name',
                marker_color=custom_colors[1]
            ))
            # Add Total Endorsements bar trace
            fig_yearly_avg_premium.add_trace(go.Bar(
                x=yearly_data['Year'],
                y=yearly_data['Approved Claim Amount'],
                name='Approved Claim Amount',
                textposition='inside',
                textfont=dict(color='white'),
                hoverinfo='x+y+name',
                marker_color=custom_colors[2]
            ))

            fig_yearly_avg_premium.update_layout(
                barmode='group',  # Grouped bar chart
                xaxis_title="Year",
                yaxis_title="Total Amount",
                font=dict(color='Black'),
                xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12), type='category'),
                yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                margin=dict(l=0, r=0, t=30, b=50),
                height=450
            )

            # Display the chart in Streamlit
            st.markdown('<h3 class="custom-subheader">Yearly Distribution of Total Premium, Earned Premium and Approved Claim Amount</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig_yearly_avg_premium, use_container_width=True)

        # Group by product and calculate the mean loss ratio
        product_data = df.groupby('Product')['Loss Ratio Rate'].mean().reset_index(name='Loss_Ratio_Rate')

        with cols1:
            # Create a bar chart
            fig_loss_ratio_by_product = go.Figure()

            for idx, (product, loss_ratio) in enumerate(zip(product_data['Product'], product_data['Loss_Ratio_Rate'])):
                fig_loss_ratio_by_product.add_trace(go.Bar(
                    x=[product],  # Single product per trace to allow individual coloring
                    y=[loss_ratio],
                    name=product,  # Product name in legend
                    text=f"{loss_ratio:.1f}%",
                    textposition='outside',
                    marker_color=custom_colors[idx % len(custom_colors)]  # Cycle through custom colors
                ))

            # Update layout
            fig_loss_ratio_by_product.update_layout(
                xaxis_title="Product",
                yaxis_title="Loss Ratio Rate (%)",
                font=dict(color='Black'),
                xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                margin=dict(l=0, r=0, t=50, b=50),
                height=500
            )

            st.markdown('<h3 class="custom-subheader">Average Loss Ratio Rate by Product</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig_loss_ratio_by_product, use_container_width=True)


        # Group data by 'Product' to calculate Average Claim Size
        average_claim_size = (
            df.groupby('Product')
            .agg(Average_Claim_Size=("Approved Claims", "sum"), Number_of_Claims=("Number of Claims", "sum"))
            .reset_index()
        )
        average_claim_size["Average Claim Size"] = average_claim_size["Average_Claim_Size"] / average_claim_size["Number_of_Claims"]

        with cols2:
            # Create the bar chart
            fig_average_claim_size = go.Figure()
            
            # Add bar trace for each product
            for idx, (product, avg_claim) in enumerate(zip(average_claim_size['Product'], average_claim_size['Average Claim Size'])):
                fig_average_claim_size.add_trace(go.Bar(
                    x=[product],  # Single product per trace to allow individual coloring
                    y=[avg_claim],
                    name=product,  # Product name in legend
                    text=f"{avg_claim / 1e3:.0f}K",
                    textposition='outside',
                    marker_color=custom_colors[idx % len(custom_colors)]  # Cycle through custom colors
                ))

            # Update layout
            fig_average_claim_size.update_layout(
                xaxis_title="Product",
                yaxis_title="Average Claim Size ()",
                font=dict(color='Black'),
                xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                margin=dict(l=0, r=0, t=30, b=50),
                height=450
            )

            # Display the chart in Streamlit
            st.markdown('<h3 class="custom-subheader">Average Claim Size by Product</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig_average_claim_size, use_container_width=True)


        cols1, cols2 = st.columns(2)


        # Group data by 'Month' and calculate the sum/mean of relevant metrics
        monthly_data_earned = df.groupby('Month')['Earned Premium'].sum().reset_index(name='Earned_Premium')
        monthly_data_claims = df.groupby('Month')['Approved Claims'].sum().reset_index(name='Approved_Claim_Amount')
        monthly_data_loss_ratio = df.groupby('Month')['Loss Ratio Rate'].mean().reset_index(name='Loss_Ratio_Rate')

        # Merge the data frames on the 'Month'
        monthly_data = (
            monthly_data_earned
            .merge(monthly_data_claims, on='Month', how='outer')
            .merge(monthly_data_loss_ratio, on='Month', how='outer')
        )

        # Fill NaN values with 0 for numerical columns
        monthly_data[['Earned_Premium', 'Approved_Claim_Amount']] = monthly_data[['Earned_Premium', 'Approved_Claim_Amount']].fillna(0)
        monthly_data['Loss_Ratio_Rate'] = monthly_data['Loss_Ratio_Rate'].fillna(0)

        with cols1:
            # Create a subplot with dual y-axes
            fig_monthly_distribution = make_subplots(specs=[[{"secondary_y": True}]])  # Secondary y-axis for Loss Ratio Rate

            # Add Earned Premium bar trace (on primary y-axis)
            fig_monthly_distribution.add_trace(go.Bar(
                x=monthly_data['Month'],
                y=monthly_data['Earned_Premium'],
                name='Earned Premium',
                text=monthly_data['Earned_Premium'].apply(lambda x: f"{x / 1_000_000:.1f}M"),
                textposition='outside',  # Display values outside the bars
                textfont=dict(color='black', size=12),
                marker_color=custom_colors[0],
                offsetgroup=0
            ), secondary_y=False)

            # Add Approved Claim Amount bar trace (on primary y-axis)
            fig_monthly_distribution.add_trace(go.Bar(
                x=monthly_data['Month'],
                y=monthly_data['Approved_Claim_Amount'],
                name='Approved Claim Amount',
                text=monthly_data['Approved_Claim_Amount'].apply(lambda x: f"{x / 1_000_000:.1f}M"),
                textposition='outside',  # Display values outside the bars
                textfont=dict(color='black', size=12),
                marker_color=custom_colors[1],
                offsetgroup=1
            ), secondary_y=False)

            # Add Loss Ratio Rate line trace (on secondary y-axis)
            fig_monthly_distribution.add_trace(go.Scatter(
                x=monthly_data['Month'],
                y=monthly_data['Loss_Ratio_Rate'],  # Loss Ratio Rate on secondary y-axis
                name='Loss Ratio Rate (%)',
                mode='lines+markers+text',
                text=monthly_data['Loss_Ratio_Rate'].apply(lambda x: f"{x:.1f}%"),  # Format as percentage
                textposition='top center',  # Display values above the line
                textfont=dict(color='black', size=12),
                line=dict(color=custom_colors[2], width=2),
                marker=dict(size=8, color=custom_colors[2]),
                hoverinfo='x+y+name'
            ), secondary_y=True)

            # Update layout for grouped bars and dual axes
            fig_monthly_distribution.update_layout(
                barmode='group',  # Grouped bar chart
                xaxis_title="Month",
                yaxis_title="Amount (M)",
                font=dict(color='Black'),
                xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12), type='category'),
                yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                margin=dict(l=0, r=0, t=50, b=50),
                height=500,
                legend=dict(x=0.01, y=1.1, orientation="h")  # Place legend above the chart
            )

            # Set secondary y-axis for Loss Ratio Rate
            fig_monthly_distribution.update_yaxes(
                title_text="Loss Ratio Rate (%)",
                secondary_y=True,
                title_font=dict(size=14),
                tickfont=dict(size=12),
                range=[0, max(monthly_data['Loss_Ratio_Rate']) * 1.2]  # Adjust range dynamically
            )

            # Rotate x-axis labels for better readability
            fig_monthly_distribution.update_xaxes(tickangle=45)

            # Display the chart in Streamlit
            st.markdown('<h3 class="custom-subheader">Monthly Distribution of Earned Premium, Approved Claims, and Loss Ratio Rate</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig_monthly_distribution, use_container_width=True)


        # Group by client and calculate the mean loss ratio
        client_data = df.groupby('Client Name')['Loss Ratio Rate'].mean().reset_index(name='Loss_Ratio_Rate')

        # Sort by loss ratio rate for better visualization
        client_data = client_data.sort_values(by='Loss_Ratio_Rate', ascending=False).head(10)
        
        with cols2:

            # Create a bar chart
            fig_loss_ratio_by_client = go.Figure()

            fig_loss_ratio_by_client.add_trace(go.Bar(
                x=client_data['Client Name'],
                y=client_data['Loss_Ratio_Rate'],
                name='Loss Ratio Rate (%)',
                text=client_data['Loss_Ratio_Rate'].apply(lambda x: f"{x:.1f}%"),
                textposition='outside',
                marker_color='#009DAE'
            ))

            # Update layout
            fig_loss_ratio_by_client.update_layout(
                xaxis_title="Client Name",
                yaxis_title="Loss Ratio Rate (%)",
                font=dict(color='Black'),
                xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12), tickangle=45),
                yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                margin=dict(l=0, r=0, t=50, b=50),
                height=500,
            )
            st.markdown('<h3 class="custom-subheader">Top 10 Employer Groups by Loss Ratio</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig_loss_ratio_by_client, use_container_width=True)
        
        with cols1:

            # Create a scatter plot
            fig_loss_vs_premium = go.Figure()

            fig_loss_vs_premium.add_trace(go.Scatter(
                x=df['Loss Ratio Rate'],
                y=df['Earned Premium'],
                mode='markers',
                name='Loss Ratio vs Earned Premium',
                marker=dict(color='#009DAE', size=10),
                text=df.apply(lambda row: f"Year: {row['Year']}<br>Product: {row['Product']}", axis=1),
                hoverinfo='text+x+y'
            ))

            # Update layout
            fig_loss_vs_premium.update_layout(
                yaxis_title="Earned Premium (M)",
                xaxis_title="Loss Ratio Rate (%)",
                font=dict(color='Black'),
                xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                margin=dict(l=0, r=0, t=50, b=50),
                height=500,
            )
            st.markdown('<h3 class="custom-subheader">Earned Premium vs Loss Ratio Rate by Product</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig_loss_vs_premium, use_container_width=True)

        # Calculate Claims Frequency (Number of Claims per Client)
        df['Claims Frequency'] = df['Number of Claims'] / df.groupby('Client Name')['Client Name'].transform('count')

        # Group by 'Client Name' and calculate average Loss Ratio Rate and Claims Frequency
        client_data = (
            df.groupby('Client Name')
            .agg(
                Average_Loss_Ratio_Rate=('Loss Ratio Rate', 'mean'),  # Mean of Loss Ratio Rate
                Claims_Frequency=('Claims Frequency', 'mean')        # Mean of Claims Frequency
            )
            .reset_index()
        )

        # Calculate claims frequency per client
        df['Claims Frequency'] = df['Number of Claims'] / df.groupby('Client Name')['Client Name'].transform('count')

        with cols2:
            # Create a scatter plot
            fig_loss_vs_frequency = go.Figure()

            # Add scatter trace
            for idx, product in enumerate(df['Product'].unique()):
                filtered_data = df[df['Product'] == product]
                fig_loss_vs_frequency.add_trace(
                    go.Scatter(
                        x=filtered_data['Claims Frequency'],
                        y=filtered_data['Loss Ratio Rate'],
                        mode='markers',
                        name=product,
                        text=filtered_data['Client Name'],  # Hover text
                        marker=dict(
                            color=custom_colors[idx % len(custom_colors)],
                            size=8
                        )
                    )
                )

            # Update layout
            fig_loss_vs_frequency.update_layout(
                xaxis_title="Claims Frequency",
                yaxis_title="Loss Ratio Rate (%)",
                font=dict(color="Black"),
                xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                margin=dict(l=0, r=0, t=50, b=50),
                height=500,
                legend=dict(x=0, y=1.1, orientation='h')  # Place legend above the chart
            )

            st.markdown('<h3 class="custom-subheader">Loss Ratio Rate vs. Claims Frequency</h3>', unsafe_allow_html=True)
            # Display the chart in Streamlit
            st.plotly_chart(fig_loss_vs_frequency, use_container_width=True)