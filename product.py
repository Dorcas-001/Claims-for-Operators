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

def display_product():

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

    st.markdown('<h1 class="main-title">PRODUCT VIEW</h1>', unsafe_allow_html=True)


    # File paths and sheet names
    filepath_visits = "Claims.xlsx"
    sheet_name1 = "2023 claims"
    sheet_name2 = "2024 claims"

    # Read the Claims data
    dfc_2023 = pd.read_excel(filepath_visits, sheet_name=sheet_name1)
    dfc_2024 = pd.read_excel(filepath_visits, sheet_name=sheet_name2)

    # Concatenate the dataframes
    df = pd.concat([dfc_2023, dfc_2024])

    # Data preprocessing
    df['Claim Created Date'] = pd.to_datetime(df['Claim Created Date'], errors='coerce')
    df["Employer Name"] = df["Employer Name"].str.upper()
    df["Provider Name"] = df["Provider Name"].str.upper()

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
    df['Source'] = df['Source'].astype(str)
    df['Quarter'] = "Q" + df['Claim Created Date'].dt.quarter.astype(str)

    # Sidebar for filters
    st.sidebar.header("Filters")

    type = st.sidebar.multiselect(
        "Select Claim Type",
        options=sorted(df['Claim Type'].unique()),
        key="sidebar_claim_type_multiselect"
    )

    status = st.sidebar.multiselect(
        "Select Claim Status",
        options=df['Claim Status'].unique(),
        key="sidebar_claim_status_multiselect"
    )

    source = st.sidebar.multiselect(
        "Select Claim Provider Type",
        options=sorted(df['Source'].unique()),
        key="sidebar_source_multiselect"
    )

    code = st.sidebar.multiselect(
        "Select Diagnosis",
        options=df['Diagnosis'].unique(),
        key="sidebar_diagnosis_code_multiselect"
    )

    client_name = st.sidebar.multiselect(
        "Select Employer Name",
        options=sorted(df['Employer Name'].dropna().unique()),
        key="sidebar_employer_name_multiselect"
    )

    prov_name = st.sidebar.multiselect(
        "Select Provider Name",
        options=sorted(df['Provider Name'].dropna().unique()),
        key="sidebar_provider_name_multiselect"
    )

    # Apply filters to the DataFrame
    if 'Claim Type' in df.columns and type:
        df = df[df['Claim Type'].isin(type)]
    if 'Claim Status' in df.columns and status:
        df = df[df['Claim Status'].isin(status)]
    if 'Source' in df.columns and source:
        df = df[df['Source'].isin(source)]
    if 'Diagnosis' in df.columns and code:
        df = df[df['Diagnosis'].isin(code)]
    if 'Employer Name' in df.columns and client_name:
        df = df[df['Employer Name'].isin(client_name)]
    if 'Provider Name' in df.columns and prov_name:
        df = df[df['Provider Name'].isin(prov_name)]

    # Create a three-column layout
    col1, col2, col3, col4 = st.columns(4)

    # Year selector (allow multiple selections)
    with col1:
        years = sorted(df['Year'].dropna().unique())
        selected_years = st.multiselect(
            "Select Years",
            options=years,
            default=[years[-1]],  # Default to the most recent year
            key="year_select_multiselect"
        )
        if selected_years:
            df = df[df['Year'].isin(selected_years)]

    # Month selector (allow multiple selections)
    with col2:
        selected_months = st.multiselect(
            "Select Months",
            options=sorted_months,
            key="month_select_multiselect"
        )
        if selected_months:
            df = df[df['Month'].isin(selected_months)]

        # Dynamically calculate the quarters based on selected months
        if selected_months:
            suggested_quarters = list(set(month_to_quarter[month] for month in selected_months))
        else:
            suggested_quarters = sorted(df['Quarter'].dropna().unique())

    # Quarter selector (allow manual selection, with dynamic suggestions)
    with col3:
        quarters = sorted(df['Quarter'].dropna().unique())
        selected_quarters = st.multiselect(
            "Select Quarters",
            options=quarters,
            key="filter_quarter_multiselector"
        )
        if selected_quarters:
            df = df[df['Quarter'].isin(selected_quarters)]

    # Business Line selector (pre-select all options by default)
    with col4:
        business_lines = sorted(df['Product'].dropna().unique()) if 'Product' in df.columns else []
        selected_business_lines = st.multiselect(
            "Select Business Lines",
            options=business_lines,
            key="filter_business_line_multiselector"
        )
        if selected_business_lines:
            df = df[df['Product'].isin(selected_business_lines)]


    # Create a three-column layout
    col1, col2, col3, col4 = st.columns(4)


    # Year selector (allow multiple selections)
    with col3:
        years = sorted(df['Provider Name'].dropna().unique())
        selected_years = st.multiselect(
            "Select Service Provider",
            options=years,
            key="Provider_selector_multiselector"
        )
        if selected_years:
            df = df[df['Provider Name'].isin(selected_years)]


        # Claim Status selector (pre-select one status by default)
    with col2:
            business_lines = sorted(df['Claim Status'].dropna().unique()) if 'Claim Status' in df.columns else []
            
            # Pre-select only one status by default (e.g., "Approved")
            selected_business_lines = st.multiselect(
                "Select Claim Status",
                options=business_lines,
                key="status_multiselector"
            )
            
            # Apply filter for Claim Status
            if selected_business_lines:
                df = df[df['Claim Status'].isin(selected_business_lines)]

        # Claim Status selector (pre-select one status by default)
    with col1:
            business_lines = sorted(df['Claim Type'].dropna().unique()) if 'Claim Type' in df.columns else []
            
            # Pre-select only one status by default (e.g., "Approved")
            selected_business_lines = st.multiselect(
                "Select Claim Type",
                options=business_lines,
                key="type_select_multiselect"
            )
            
            # Apply filter for Claim Status
            if selected_business_lines:
                df = df[df['Claim Type'].isin(selected_business_lines)]

    # Year selector (allow multiple selections)
    with col4:
        years = sorted(df['Employer Name'].dropna().unique())
        selected_years = st.multiselect(
            "Select Employer Group",
            options=years,
            key="employer_selecto_multiselector"
        )
        if selected_years:
            df = df[df['Employer Name'].isin(selected_years)]

    # Dynamically calculate the date range based on selected filters
    if selected_months:
        # Filter DataFrame by selected months
        df_filtered = df[df['Month'].isin(selected_months)]
    else:
        df_filtered = df

    # Get the minimum and maximum dates from the filtered DataFrame
    startDate = df_filtered["Claim Created Date"].min()
    endDate = df_filtered["Claim Created Date"].max()


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
        date1 = pd.to_datetime(display_date_input(col1, "Start Date", startDate, startDate, endDate, key="date_start_multiselecto"))

    with col2:
        date2 = pd.to_datetime(display_date_input(col2, "End Date", endDate, startDate, endDate, key="date_end_multiselecto"))

    # Filter the DataFrame based on the selected date range
    if date1 and date2:
        df = df[(df["Claim Created Date"] >= date1) & (df["Claim Created Date"] <= date2)]



    df.rename(columns={'Employer Name': 'Client Name'}, inplace=True)

 


    df_app = df[df['Claim Status'] == 'Approved']
    df_dec = df[df['Claim Status'] == 'Declined']

    if not df.empty:
        scale = 1_000_000  # For millions
        scaling = 1000  # For thousands

        # Calculate key metrics
        total_claim_amount = (df["Claim Amount"].sum()) / scale
        average_amount = (df["Claim Amount"].mean()) / scaling
        average_app_amount = (df["Approved Claim Amount"].mean()) / scaling

        total_app_claim_amount = (df_app["Approved Claim Amount"].sum()) / scale
        total_dec_claim_amount = (df_dec["Claim Amount"].sum()) / scaling

        total_app = df_app["Claim ID"].nunique()
        total_dec = df_dec["Claim ID"].nunique()



        total_clients = df["Client Name"].nunique()
        total_claims = df["Claim ID"].nunique()


        # Approval Rate (Claims Approved / Total Claims)
        approval_rate = (total_app / total_claims) * 100 if total_claims > 0 else 0

        # Denial Rate (Claims Declined / Total Claims)
        denial_rate = (total_dec / total_claims) * 100 if total_claims > 0 else 0


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


        # Display client and claim metrics
        st.markdown('<h2 class="custom-subheader">For Health Insurance or ProActiv Claims in Numbers</h2>', unsafe_allow_html=True)
        cols1, cols2, cols3 = st.columns(3)
        display_metric(cols1, "Number of Clients", total_clients)
        display_metric(cols2, "Number of Claims", f"{total_claims:,}")
        display_metric(cols3, "Number of Approved Claims", f"{total_app:,}")
        display_metric(cols1, "Number of Declined Claims", total_dec)
        display_metric(cols2, "Approval Rate", f"{approval_rate:.2f} %")
        display_metric(cols3, "Denial Rate", f"{denial_rate:.2f} %")

        # Display claim amount metrics
        st.markdown('<h2 class="custom-subheader">For Health Insurance or ProActiv Claim Amounts </h2>', unsafe_allow_html=True)
        cols1, cols2, cols3 = st.columns(3)
        display_metric(cols1, "Total Claims", total_claims)
        display_metric(cols2, "Total Claim Amount", f"{total_claim_amount:,.0f} M")
        display_metric(cols3, "Total Approved Claim Amount", f"{total_app_claim_amount:,.0f} M")
        display_metric(cols1, "Total Declined Claim Amount", f"{total_dec_claim_amount:,.0f} K")
        display_metric(cols2, "Average Claim Amount", f"{average_amount:,.1f} K")
        display_metric(cols3, "Average Approved Claim Amount", f"{average_app_amount:,.1f} K")


        st.dataframe(df)



        # Define custom colors
        custom_colors = ["#006E7F", "#e66c37", "#461b09", "#f8a785", "#CC3636"]

        col1, col2 = st.columns(2)

        with col1:
            # Total Claims and Approved Claim Amount Over Time
            area_chart_count = df.groupby(df["Claim Created Date"].dt.strftime("%Y-%m-%d")).size().reset_index(name='Count')

            area_chart_amount = df.groupby(df["Claim Created Date"].dt.strftime("%Y-%m-%d"))['Claim Amount'].sum().reset_index(name='Claim Amount')

            area_chart = pd.merge(area_chart_count, area_chart_amount, on='Claim Created Date').sort_values("Claim Created Date")

            fig1 = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig1.add_trace(
                go.Scatter(
                    x=area_chart['Claim Created Date'], 
                    y=area_chart['Count'], 
                    name="Number of Claims", 
                    fill='tozeroy', 
                    line=dict(color=custom_colors[1])), 
                    secondary_y=False)
            
            fig1.add_trace(
                go.Scatter(
                    x=area_chart['Claim Created Date'], 
                    y=area_chart['Claim Amount'], 
                    name="Claim Amount", fill='tozeroy', 
                    line=dict(color=custom_colors[0])), 
                    secondary_y=True)
            
            fig1.update_xaxes(
                title_text="Claim Created Date", 
                tickangle=45)
            
            fig1.update_yaxes(
                title_text="<b>Number of Claims</b>", 
                secondary_y=False)
            
            fig1.update_yaxes(
                title_text="<b>Approved Claim Amount</b>", 
                secondary_y=True)
            
            st.markdown('<h3 class="custom-subheader">Total Claims and Approved Claim Amount Over Time</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig1, use_container_width=True)

        # Group data by "Year" and "Product" and calculate the average Claim Amount
        yearly_avg_claim = df.groupby(['Year', 'Product'])['Claim Amount'].sum().unstack().fillna(0)

        # Define custom colors
        with col2:
            # Create the grouped bar chart
            fig_yearly_avg_claim = go.Figure()

            # Add traces for each product
            for idx, product in enumerate(yearly_avg_claim.columns):
                fig_yearly_avg_claim.add_trace(go.Bar(
                    x=yearly_avg_claim.index,  # Years on the x-axis
                    y=yearly_avg_claim[product],  # Average claim amount for each product
                    name=product,  # Product name as legend
                    text=yearly_avg_claim[product].apply(lambda x: f"{x / 1_000_000:.1f}M"),  # Format values in millions
                    textposition='inside',
                    textfont=dict(color='white'),
                    hoverinfo='x+y+name',
                    marker_color=custom_colors[idx % len(custom_colors)]  # Cycle through custom colors
                ))

            # Update layout
            fig_yearly_avg_claim.update_layout(
                barmode='group',  # Grouped bar chart
                xaxis_title="Year",
                yaxis_title="Total Claim Amount (M)",
                font=dict(color='Black'),
                xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                margin=dict(l=0, r=0, t=30, b=50),
                height=450
            )

            # Display the chart in Streamlit
            st.markdown('<h3 class="custom-subheader">Total Yearly Claims by Product</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig_yearly_avg_claim, use_container_width=True)

        col1, col2 = st.columns(2)

        # Group data by "Month" and "Product" and calculate the average Claim Amount
        monthly_avg_claim = df.groupby(['Month', 'Product'])['Claim Amount'].mean().unstack().fillna(0)

        # Define custom colors
        with col1:
            # Create the grouped bar chart
            fig_monthly_avg_claim = go.Figure()

            # Add traces for each product
            for idx, product in enumerate(monthly_avg_claim.columns):
                fig_monthly_avg_claim.add_trace(go.Bar(
                    x=monthly_avg_claim.index,  # Months on the x-axis
                    y=monthly_avg_claim[product],  # Average claim amount for each product
                    name=product,  # Product name as legend
                    text=monthly_avg_claim[product].apply(lambda x: f"{x / 1_000:.1f}K"),  # Format values in millions
                    textposition='inside',
                    textfont=dict(color='white'),
                    hoverinfo='x+y+name',
                    marker_color=custom_colors[idx % len(custom_colors)]  # Cycle through custom colors
                ))

            # Update layout
            fig_monthly_avg_claim.update_layout(
                barmode='group',  # Grouped bar chart
                xaxis_title="Month",
                yaxis_title="Average Claim Amount (M)",
                font=dict(color='Black'),
                xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12), tickangle=45),  # Rotate month labels for readability
                yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                margin=dict(l=0, r=0, t=30, b=50),
                height=450
            )

            # Display the chart in Streamlit
            st.markdown('<h3 class="custom-subheader">Average Monthly Claim Amount by Product</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig_monthly_avg_claim, use_container_width=True)

    # Group by product and count total claims
    product_claim_count = df.groupby(['Product'])['Claim Amount'].mean().reset_index()

    with col2:
        # Create a bar chart showing total claims by product
        fig_claim_status_by_product = go.Figure()

        # Add traces for each product with different colors
        for idx, product in enumerate(product_claim_count['Product']):
            fig_claim_status_by_product.add_trace(go.Bar(
                x=[product],  # The product name on the x-axis
                y=[product_claim_count.loc[product_claim_count['Product'] == product, 'Claim Amount'].values[0]],  # The claim amount for the product
                name=product,  # Product name as legend
                text=product_claim_count.loc[product_claim_count['Product'] == product, 'Claim Amount'].apply(lambda x: f"{x / 1_000:.1f}K"),  # Format values in millions
                textposition='inside',
                textfont=dict(color='white'),
                hoverinfo='x+y+name',
                marker_color=custom_colors[idx % len(custom_colors)]  # Cycle through custom colors
            ))

        # Update layout
        fig_claim_status_by_product.update_layout(
            barmode='group',
            xaxis_title="Product",
            yaxis_title="Average Claim Amount",
            font=dict(color='Black'),
            margin=dict(l=0, r=0, t=50, b=50),
            height=500
        )

        st.markdown('<h3 class="custom-subheader">Average Claim Amount by Product</h3>', unsafe_allow_html=True)

        st.plotly_chart(fig_claim_status_by_product, use_container_width=True)


    col1, col2 = st.columns(2)

    # Group by product and count total claims
    product_claim_count = df.groupby(['Product'])['Claim ID'].nunique().reset_index()

    with col1:
        # Create a bar chart showing total claims by product
        fig_claim_status_by_product = go.Figure()

        # Add traces for each product with different colors
        for idx, product in enumerate(product_claim_count['Product']):
            fig_claim_status_by_product.add_trace(go.Bar(
                x=[product],  # The product name on the x-axis
                y=[product_claim_count.loc[product_claim_count['Product'] == product, 'Claim ID'].values[0]],  # The claim amount for the product
                name=product,  # Product name as legend
                textposition='inside',
                textfont=dict(color='white'),
                hoverinfo='x+y+name',
                marker_color=custom_colors[idx % len(custom_colors)]  
            ))

        # Update layout
        fig_claim_status_by_product.update_layout(
            barmode='group',
            xaxis_title="Product",
            yaxis_title="Number of Claims",
            font=dict(color='Black'),
            margin=dict(l=0, r=0, t=50, b=50),
            height=500
        )

        st.markdown('<h3 class="custom-subheader">Number of Claims by Product</h3>', unsafe_allow_html=True)

        st.plotly_chart(fig_claim_status_by_product, use_container_width=True)



        with col2:

            # Filter top providers by claim volume
            top_providers = df.groupby(['Product', 'Source'])['Claim Amount'].mean().reset_index(name='Claim Amount')


            # Create a grouped bar chart
            fig_top_providers = go.Figure()

            for product in top_providers['Product'].unique():
                product_data = top_providers[top_providers['Product'] == product]
                fig_top_providers.add_trace(go.Bar(
                    x=product_data['Source'],
                    y=product_data['Claim Amount'],
                    name=product,
                    marker_color=custom_colors[list(top_providers['Product'].unique()).index(product) % len(custom_colors)]  # Assign unique color per product
                ))

            # Update layout
            fig_top_providers.update_layout(
                barmode='group',
                xaxis_title="Provider Type",
                yaxis_title="Average Claim Amount",
                font=dict(color='Black'),
                xaxis=dict(tickangle=45),
                margin=dict(l=0, r=0, t=50, b=50),
                height=500
            )
            st.markdown('<h3 class="custom-subheader">Provider Type Trend by Product and Average Cllaim Amount</h3>', unsafe_allow_html=True)

            st.plotly_chart(fig_top_providers, use_container_width=True)


        with col1:

            # Filter top providers by claim volume
            top_providers = df.groupby(['Product', 'Claim Type'])['Claim Amount'].mean().reset_index(name='Claim Amount')


            # Create a grouped bar chart
            fig_top_providers = go.Figure()

            for product in top_providers['Product'].unique():
                product_data = top_providers[top_providers['Product'] == product]
                fig_top_providers.add_trace(go.Bar(
                    x=product_data['Claim Type'],
                    y=product_data['Claim Amount'],
                    name=product,
                    marker_color=custom_colors[list(top_providers['Product'].unique()).index(product) % len(custom_colors)]  # Assign unique color per product
                ))

            # Update layout
            fig_top_providers.update_layout(
                barmode='group',
                xaxis_title="Claim Type",
                yaxis_title="Average Claim Amount",
                font=dict(color='Black'),
                xaxis=dict(tickangle=45),
                margin=dict(l=0, r=0, t=50, b=50),
                height=500
            )
            st.markdown('<h3 class="custom-subheader">Average Claim Amount and Claim Type Trend by Product</h3>', unsafe_allow_html=True)

            st.plotly_chart(fig_top_providers, use_container_width=True)

        with col2:

            # Filter top providers by claim volume
            top_providers = df.groupby(['Product', 'Diagnosis'])['Claim Amount'].sum().reset_index(name='Claim Amount')

            top_providers = top_providers.sort_values(by=['Product', 'Claim Amount'], ascending=[True, False]).groupby('Product').head(10)

            # Create a grouped bar chart
            fig_top_providers = go.Figure()

            for product in top_providers['Product'].unique():
                product_data = top_providers[top_providers['Product'] == product]
                fig_top_providers.add_trace(go.Bar(
                    x=product_data['Diagnosis'],
                    y=product_data['Claim Amount'],
                    name=product,
                    marker_color=custom_colors[list(top_providers['Product'].unique()).index(product) % len(custom_colors)]  # Assign unique color per product
                ))

            # Update layout
            fig_top_providers.update_layout(
                barmode='group',
                xaxis_title="Diagnosis",
                yaxis_title="Claim Amount",
                font=dict(color='Black'),
                xaxis=dict(tickangle=45),
                margin=dict(l=0, r=0, t=50, b=50),
                height=500,
            )
            st.markdown('<h3 class="custom-subheader">Top 10 Diagnosis by Product</h3>', unsafe_allow_html=True)

            st.plotly_chart(fig_top_providers, use_container_width=True)

        with col1:

            # Filter top providers by claim volume
            top_providers = df.groupby(['Product', 'Provider Name'])['Claim Amount'].sum().reset_index(name='Total Claim Amount')

            # Sort by claim amount and limit to top 5 providers per product
            top_providers = top_providers.sort_values(by=['Product', 'Total Claim Amount'], ascending=[True, False]).groupby('Product').head(10)

            # Create a grouped bar chart for top providers
            fig_top_providers = go.Figure()

            for idx, product in enumerate(top_providers['Product'].unique()):
                product_data = top_providers[top_providers['Product'] == product]
                fig_top_providers.add_trace(go.Bar(
                    x=product_data['Provider Name'],
                    y=product_data['Total Claim Amount'],
                    name=product,
                    text=product_data['Total Claim Amount'].apply(lambda x: f"Client Name{x / 1_000_000:.1f}M"),  # Format as millions
                    textposition='outside',
                    marker_color=custom_colors[idx % len(custom_colors)]  # Assign unique color per product
                ))

            # Update layout
            fig_top_providers.update_layout(
                barmode='group',
                xaxis_title="Provider Name",
                yaxis_title="Total Claim Amount (M)",
                font=dict(color='Black', size=12),
                xaxis=dict(tickangle=45, title_font=dict(size=14), tickfont=dict(size=12)),
                yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12), ticksuffix="M"),
                margin=dict(l=0, r=0, t=50, b=50),
                height=500
            )

            # Display the chart in Streamlit
            st.markdown('<h3 class="custom-subheader">Top 10 Service Providers by Claim Amount</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig_top_providers, use_container_width=True)

        with col2:

            # Filter top clients by claim volume
            top_clients = df.groupby(['Product', 'Client Name'])['Claim Amount'].sum().reset_index(name='Total Claim Amount')

            # Sort by claim amount and limit to top 5 clients per product
            top_clients = top_clients.sort_values(by=['Product', 'Total Claim Amount'], ascending=[True, False]).groupby('Product').head(10)

            # Create a grouped bar chart for top clients
            fig_top_clients = go.Figure()

            for idx, product in enumerate(top_clients['Product'].unique()):
                product_data = top_clients[top_clients['Product'] == product]
                fig_top_clients.add_trace(go.Bar(
                    x=product_data['Client Name'],
                    y=product_data['Total Claim Amount'],
                    name=product,
                    text=product_data['Total Claim Amount'].apply(lambda x: f"{x / 1_000_000:.1f}M"),  # Format as millions
                    textposition='outside',
                    marker_color=custom_colors[idx % len(custom_colors)]  # Assign unique color per product
                ))

            # Update layout
            fig_top_clients.update_layout(
                barmode='group',
                xaxis_title="Client Name",
                yaxis_title="Total Claim Amount (M)",
                font=dict(color='Black', size=12),
                xaxis=dict(tickangle=45, title_font=dict(size=14), tickfont=dict(size=12)),
                yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12), ticksuffix="M"),
                margin=dict(l=0, r=0, t=50, b=50),
                height=500
            )

            # Display the chart in Streamlit
            st.markdown('<h3 class="custom-subheader">Top 10 Employer Group by Claim Amount</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig_top_clients, use_container_width=True)