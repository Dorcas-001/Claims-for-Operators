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

def display_claim_type():

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

    st.markdown('<h1 class="main-title">CLAIM TYPE ANALYSIS</h1>', unsafe_allow_html=True)


    # File paths and sheet names
    filepath_visits = "Claims.xlsx"
    sheet_name1 = "2023 claims"
    sheet_name2 = "2024 claims"

    # Read the Claims data
    dfc_2023 = pd.read_excel(filepath_visits, sheet_name=sheet_name1)
    dfc_2024 = pd.read_excel(filepath_visits, sheet_name=sheet_name2)

    # Concatenate the dataframes
    df = pd.concat([dfc_2023, dfc_2024])

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

    source = st.sidebar.multiselect(
        "Select Claim Provider Type", 
        options=sorted(df['Source'].unique()), 
        key="filter_source_2025"
    )

    code = st.sidebar.multiselect(
        "Select Diagnosis Code", 
        options=df['ICD-10 Code'].unique(), 
        key="filter_diag_code_2025"
    )

    client_name = st.sidebar.multiselect(
        "Select Employer Name", 
        options=sorted(df['Employer Name'].dropna().unique()), 
        key="filter_employer_2025"
    )

    prov_name = st.sidebar.multiselect(
        "Select Provider Name", 
        options=sorted(df['Provider Name'].dropna().unique()), 
        key="filter_provider_2025"
    )

    # Apply filters to the DataFrame
    if 'Source' in df.columns and source:
        df = df[df['Source'].isin(source)]
    if 'ICD-10 Code' in df.columns and code:
        df = df[df['ICD-10 Code'].isin(code)]
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
            key="year_selector_multiselector"
        )
        if selected_years:
            df = df[df['Year'].isin(selected_years)]

    # Month selector (allow multiple selections)
    with col2:
        selected_months = st.multiselect(
            "Select Months",
            options=sorted_months,
            key="month_selector_multiselector"
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
            key="filter_quarter_multi"
        )
        if selected_quarters:
            df = df[df['Quarter'].isin(selected_quarters)]

    # Business Line selector (pre-select all options by default)
    with col4:
        business_lines = sorted(df['Product'].dropna().unique()) if 'Product' in df.columns else []
        selected_business_lines = st.multiselect(
            "Select Business Lines",
            options=business_lines,
            key="filter_business_line_multi"
        )
        if selected_business_lines:
            df = df[df['Product'].isin(selected_business_lines)]


    # Create a three-column layout
    col1, col2, col3, col4 = st.columns(4)

    # Year selector (allow multiple selections)
    with col3:
        years = sorted(df['Employer Name'].dropna().unique())
        selected_years = st.multiselect(
            "Select Employer Group",
            options=years,
            key="employer_selector_multi"
        )
        if selected_years:
            df = df[df['Employer Name'].isin(selected_years)]

    # Year selector (allow multiple selections)
    with col4:
        years = sorted(df['Provider Name'].dropna().unique())
        selected_years = st.multiselect(
            "Select Service Provider",
            options=years,
            key="Provider_selector_multi"
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
                key="status_select_multiselect"
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
                key="type_sele_multiselect"
            )
            
            # Apply filter for Claim Status
            if selected_business_lines:
                df = df[df['Claim Type'].isin(selected_business_lines)]

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
        date1 = pd.to_datetime(display_date_input(col1, "Start Date", startDate, startDate, endDate, key="date_start_multiselec"))

    with col2:
        date2 = pd.to_datetime(display_date_input(col2, "End Date", endDate, startDate, endDate, key="date_end_multiselec"))

    # Filter the DataFrame based on the selected date range
    if date1 and date2:
        df = df[(df["Claim Created Date"] >= date1) & (df["Claim Created Date"] <= date2)]






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



        total_clients = df["Employer Name"].nunique()
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


        custom_colors = ["#009DAE", "#e66c37", "#461b09", "#f8a785", "#9ACBD0","#CC3636"]

        cols1, cols2 = st.columns(2)

        # Group by Claim Created Date and Claim Type, and count the occurrences
        claim_type_count = (
            df.groupby([df["Claim Created Date"].dt.strftime("%Y-%m-%d"), "Claim Type"])
            .size()
            .reset_index(name="Count")
        )

        # Pivot the data for plotting (Claim Type as columns)
        pivot_claim_type = claim_type_count.pivot(
            index="Claim Created Date", columns="Claim Type", values="Count"
        ).fillna(0)

        # Sort the data by date
        pivot_claim_type = pivot_claim_type.sort_index()

        # Create the stacked area chart
        with cols1:
            fig2 = go.Figure()

            # Add traces for each Claim Type
            for i, claim_type in enumerate(pivot_claim_type.columns):
                fig2.add_trace(
                    go.Scatter(
                        x=pivot_claim_type.index,
                        y=pivot_claim_type[claim_type],
                        mode="lines",
                        stackgroup="one",  # This creates a stacked area chart
                        name=claim_type,
                        line=dict(width=0.5, color=custom_colors[i % len(custom_colors)]),
                        hoverinfo="x+y+name",
                        fillcolor=custom_colors[i % len(custom_colors)],
                    )
                )

            # Update layout
            fig2.update_layout(
                xaxis_title="Claim Created Date",
                yaxis_title="Number of Claims",
                font=dict(color="Black"),
                xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12), tickangle=45),
                yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                margin=dict(l=0, r=0, t=30, b=50),
                legend=dict(x=0, y=1.1, orientation="h"),  # Place legend above the chart
                height=450,
            )

            # Display the chart in Streamlit
            st.markdown('<h3 class="custom-subheader">Number of Claims by Claim Type Over Time</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig2, use_container_width=True)


        # Group data by "Claim Type" and "Month" to calculate the average claim amount per month
        monthly_claim_type_avg = df.groupby(['Claim Type', 'Year'])['Claim Amount'].mean().reset_index()


        with cols2:
            # Create the bar chart for average monthly claim amount by claim type
            fig_monthly_claim_type_avg = go.Figure()

            # Add trace for Average Monthly Claim Amount
            for idx, claim_type in enumerate(monthly_claim_type_avg['Claim Type'].unique()):
                filtered_data = monthly_claim_type_avg[monthly_claim_type_avg['Claim Type'] == claim_type]
                fig_monthly_claim_type_avg.add_trace(go.Bar(
                    x=filtered_data['Year'],
                    y=filtered_data['Claim Amount'],
                    name=claim_type,
                    text=[f'{value/1e3:.0f}K' for value in filtered_data['Claim Amount']],
                    textposition='inside',
                    textfont=dict(color='white'),
                    hoverinfo='x+y+name',
                    marker_color=custom_colors[idx % len(custom_colors)]  # Cycle through custom colors
                ))

            # Set layout for the chart
            fig_monthly_claim_type_avg.update_layout(
                barmode='group',  # Grouped bar chart
                xaxis_title="Year",
                yaxis_title="Average Claim Amount",
                font=dict(color='Black'),
                xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                margin=dict(l=0, r=0, t=50, b=50),
                height=500,
                legend=dict(title="Claim Type")
            )

            # Display the chart in Streamlit
            st.markdown('<h3 class="custom-subheader">Average Yearly Claim Amount by Claim Type</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig_monthly_claim_type_avg, use_container_width=True)


        # Group data by "Claim Type" and "Month" to calculate the average claim amount per month
        monthly_claim_type_avg = df.groupby(['Claim Type', 'Month'])['Claim Amount'].mean().reset_index()

        monthly_claim_type_avg['Month_Order'] = monthly_claim_type_avg['Month'].apply(lambda x: sorted_months.index(x) if x in sorted_months else len(sorted_months))

        monthly_claim_type_avg = monthly_claim_type_avg.sort_values(by=['Month_Order', 'Claim Type'])


        with cols1:
            # Create the bar chart for average monthly claim amount by claim type
            fig_monthly_claim_type_avg = go.Figure()

            # Add trace for Average Monthly Claim Amount
            for idx, claim_type in enumerate(monthly_claim_type_avg['Claim Type'].unique()):
                filtered_data = monthly_claim_type_avg[monthly_claim_type_avg['Claim Type'] == claim_type]
                fig_monthly_claim_type_avg.add_trace(go.Bar(
                    x=filtered_data['Month'],
                    y=filtered_data['Claim Amount'],
                    name=claim_type,
                    text=[f'{value/1e3:.0f}K' for value in filtered_data['Claim Amount']],
                    textposition='inside',
                    textfont=dict(color='white'),
                    hoverinfo='x+y+name',
                    marker_color=custom_colors[idx % len(custom_colors)]  # Cycle through custom colors
                ))

            # Set layout for the chart
            fig_monthly_claim_type_avg.update_layout(
                barmode='group',  # Grouped bar chart
                xaxis_title="Month",
                yaxis_title="Average Claim Amount",
                font=dict(color='Black'),
                xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                margin=dict(l=0, r=0, t=50, b=50),
                height=500,
                legend=dict(title="Claim Type")
            )

            # Display the chart in Streamlit
            st.markdown('<h3 class="custom-subheader">Average Monthly Claim Amount by Claim Type</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig_monthly_claim_type_avg, use_container_width=True)


        # Calculate the Approved Claim Amount by Client Segment
        int_owner = df.groupby("Claim Type")["Claim Amount"].sum().reset_index()
        int_owner.columns = ["Claim Type", "Claim Amount"]    

        with cols2:
            # Display the header
            st.markdown('<h3 class="custom-subheader">Total Claim Amount by Claim Type</h3>', unsafe_allow_html=True)


            # Create a donut chart
            fig = px.pie(int_owner, names="Claim Type", values="Claim Amount", hole=0.5, template="plotly_dark", color_discrete_sequence=custom_colors)
            fig.update_traces(textposition='inside', textinfo='value+percent')
            fig.update_layout(height=450, margin=dict(l=0, r=10, t=30, b=50))

            # Display the chart in Streamlit
            st.plotly_chart(fig, use_container_width=True)


        # Group data by "Claim Type" and "Month" to calculate the average claim amount per month
        monthly_claim_type_avg = df.groupby(['Claim Status', 'Claim Type'])['Claim Amount'].mean().reset_index()
        monthly_claim_type_avg = monthly_claim_type_avg.sort_values(by=['Claim Type', 'Claim Status'])


        with cols1:
            # Create the bar chart for average monthly claim amount by claim type
            fig_monthly_claim_type_avg = go.Figure()

            # Add trace for Average Monthly Claim Amount
            for idx, claim_type in enumerate(monthly_claim_type_avg['Claim Status'].unique()):
                filtered_data = monthly_claim_type_avg[monthly_claim_type_avg['Claim Status'] == claim_type]
                fig_monthly_claim_type_avg.add_trace(go.Bar(
                    x=filtered_data['Claim Type'],
                    y=filtered_data['Claim Amount'],
                    name=claim_type,
                    text=[f'{value/1e3:.0f}K' for value in filtered_data['Claim Amount']],
                    textposition='inside',
                    textfont=dict(color='white'),
                    hoverinfo='x+y+name',
                    marker_color=custom_colors[idx % len(custom_colors)]  # Cycle through custom colors
                ))

            # Set layout for the chart
            fig_monthly_claim_type_avg.update_layout(
                barmode='group',  # Grouped bar chart
                xaxis_title="Claim Type",
                yaxis_title="Average Claim Amount",
                font=dict(color='Black'),
                xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                margin=dict(l=0, r=0, t=50, b=50),
                height=500,
                legend=dict(title="Claim Status")
            )

            # Display the chart in Streamlit
            st.markdown('<h3 class="custom-subheader">Average Claim Amount by Claim Type and Status</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig_monthly_claim_type_avg, use_container_width=True)


        # Group data by "Claim Type" and "Month" to calculate the average claim amount per month
        monthly_claim_type_avg = df.groupby(['Claim Status', 'Claim Type'])['Claim ID'].nunique().reset_index()
        monthly_claim_type_avg = monthly_claim_type_avg.sort_values(by=['Claim Type', 'Claim Status'])


        with cols2:
            # Create the bar chart for average monthly claim amount by claim type
            fig_monthly_claim_type_avg = go.Figure()

            # Add trace for Average Monthly Claim Amount
            for idx, claim_type in enumerate(monthly_claim_type_avg['Claim Status'].unique()):
                filtered_data = monthly_claim_type_avg[monthly_claim_type_avg['Claim Status'] == claim_type]
                fig_monthly_claim_type_avg.add_trace(go.Bar(
                    x=filtered_data['Claim Type'],
                    y=filtered_data['Claim ID'],
                    name=claim_type,
                    text=[f'{value/1e3:.0f}K' for value in filtered_data['Claim ID']],
                    textposition='inside',
                    textfont=dict(color='white'),
                    hoverinfo='x+y+name',
                    marker_color=custom_colors[idx % len(custom_colors)]  # Cycle through custom colors
                ))

            # Set layout for the chart
            fig_monthly_claim_type_avg.update_layout(
                barmode='group',  # Grouped bar chart
                xaxis_title="Claim Type",
                yaxis_title="Number of Claims",
                font=dict(color='Black'),
                xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                margin=dict(l=0, r=0, t=50, b=50),
                height=500,
                legend=dict(title="Claim Status")
            )

            # Display the chart in Streamlit
            st.markdown('<h3 class="custom-subheader">Number of Claims by Claim Type and Status</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig_monthly_claim_type_avg, use_container_width=True)


        # Create the layout columns
        cls1, cls2 = st.columns(2)
        # Group by Employer Name and Client Segment, then sum the Approved Claim Amount
        df_grouped = df.groupby(['Employer Name', 'Claim Type'])['Approved Claim Amount'].sum().nlargest(10).reset_index()

        # Get the top 10 clients by Approved Claim Amount
        top_10_clients = df_grouped.groupby('Employer Name')['Approved Claim Amount'].sum().reset_index()

        # Filter the original DataFrame to include only the top 10 clients
        client_df = df_grouped[df_grouped['Employer Name'].isin(top_10_clients['Employer Name'])]

        # Sort the client_df by Approved Claim Amount in descending order
        client_df = client_df.sort_values(by='Approved Claim Amount', ascending=False)

        with cls1:
            # Create the bar chart
            fig = go.Figure()


                    # Add bars for each Client Segment
            for idx, Client_Segment in enumerate(client_df['Claim Type'].unique()):
                        Client_Segment_data = client_df[client_df['Claim Type'] == Client_Segment]
                        fig.add_trace(go.Bar(
                            x=Client_Segment_data['Employer Name'],
                            y=Client_Segment_data['Approved Claim Amount'],
                            name=Client_Segment,
                            text=[f'{value/1e6:.0f}M' for value in Client_Segment_data['Approved Claim Amount']],
                            textposition='auto',
                            marker_color=custom_colors[idx % len(custom_colors)]  # Cycle through custom colors
                        ))

            fig.update_layout(
                        barmode='stack',
                        yaxis_title="Approved Claim Amount",
                        xaxis_title="Employer Name",
                        font=dict(color='Black'),
                        xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                        yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                        margin=dict(l=0, r=0, t=30, b=50)
                    )

                    # Display the chart in Streamlit
            st.markdown('<h3 class="custom-subheader">Top 10 Employer groups by Approved Claim Amount and Claim Type</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)


        # Group by Employer Name and Client Segment, then sum the Approved Claim Amount
        df_grouped = df.groupby(['Provider Name', 'Claim Type'])['Approved Claim Amount'].sum().nlargest(10).reset_index()

        # Get the top 10 clients by Approved Claim Amount
        top_10_clients = df_grouped.groupby('Provider Name')['Approved Claim Amount'].sum().reset_index()

        # Filter the original DataFrame to include only the top 10 clients
        client_df = df_grouped[df_grouped['Provider Name'].isin(top_10_clients['Provider Name'])]

        # Sort the client_df by Approved Claim Amount in descending order
        client_df = client_df.sort_values(by='Approved Claim Amount', ascending=False)

        with cls2:
            # Create the bar chart
            fig = go.Figure()


                    # Add bars for each Client Segment
            for idx, Client_Segment in enumerate(client_df['Claim Type'].unique()):
                        Client_Segment_data = client_df[client_df['Claim Type'] == Client_Segment]
                        fig.add_trace(go.Bar(
                            x=Client_Segment_data['Provider Name'],
                            y=Client_Segment_data['Approved Claim Amount'],
                            name=Client_Segment,
                            text=[f'{value/1e6:.0f}M' for value in Client_Segment_data['Approved Claim Amount']],
                            textposition='auto',
                            marker_color=custom_colors[idx % len(custom_colors)]  # Cycle through custom colors
                        ))

            fig.update_layout(
                        barmode='stack',
                        yaxis_title="Approved Claim Amount",
                        xaxis_title="Provider Name",
                        font=dict(color='Black'),
                        xaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                        yaxis=dict(title_font=dict(size=14), tickfont=dict(size=12)),
                        margin=dict(l=0, r=0, t=30, b=50)
                    )

                    # Display the chart in Streamlit
            st.markdown('<h3 class="custom-subheader">Top 10 Service Providers by Approved Claim Amount and Claim Type</h3>', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)

