
import streamlit as st
import json
import bcrypt
import pandas as pd
import altair as alt
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


# Import functions from other files
from claim_analysis import display_analysis
from product import display_product
from claim_type import display_claim_type
from loss_ratio import display_loss_ratio
from fraud import display_fraud


st.set_page_config(
    page_title="Eden Care Claims Dashboard Executive View",
    page_icon=Image.open("logo.png"),
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to load users from the JSON file
def load_users():
    with open('users.json', 'r') as file:
        return json.load(file)['users']

# Function to authenticate a user
def authenticate(username, password):
    users = load_users()
    for user in users:
        if user['username'] == username and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return True
    return False



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
current_date = datetime.now()



# Function to display the dashboard
def display_dashboard(username):
    # SIDEBAR FILTER
    logo_url = 'EC_logo.png'  
    st.sidebar.image(logo_url, use_column_width=True)

    tab_titles = ["Home", "Claims Analysis", "Product View", "Claim Type View", "Fraud Detection", "Loss Ratio View"]
    tabs = st.tabs(tab_titles)

    # Custom CSS for vivid and bold tabs
    st.markdown(
        """
        <style>

        /* Style for the entire tab container */
        [data-baseweb="tab-list"] {
            font-size: 1.2rem;
            font-weight: bold;
            color: white;
            background-color: #009DAE; /* Dark green background */
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 20px;
            position: sticky; /* Make the tabs sticky */
            top: 0; /* Stick to the top of the viewport */
            z-index: 1000; /* Ensure it stays above other content */
        }

        /* Style for individual tabs */
        [data-baseweb="tab"] {
            background-color: #e66c37; /* Orange background for tabs */
            color: white;
            
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            margin-right: 10px;
            transition: all 0.3s ease;
        }



        /* Hover effect for tabs */
        [data-baseweb="tab"]:hover {
            background-color: #F49773; /* Darker orange on hover */
            cursor: pointer;
            color: white;
            font-weight: bold; /* Makes text inside the tab bold */


        }

        /* General styling for the dashboard */
        .reportview-container {
            background-color: #013220;
            color: white;
        }
        .main-title {
            color: #e66c37;
            text-align: center;
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: .5rem;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
        }
        div.block-container {
            padding-top: 2rem;
        }
        .subheader {
            color: #e66c37;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
            padding: 10px;
            border-radius: 5px;
            display: inline-block;
        }

        .subheader {
            color: #e66c37;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
            padding: 10px;
            border-radius: 5px;
            display: inline-block;
        }

        .text {
            font-size: 1.1rem;
            color: #333;
            padding: 10px;
            line-height: 1.6;
            margin-bottom: 1rem;
        }

        .separator {
            margin: 2rem 0;
            border-bottom: 2px solid #ddd;
        }
        </style>
        """,
        unsafe_allow_html=True
    )



    with tabs[0]:
            st.markdown('<h1 class="main-title">EDEN CARE CLAIMS MANAGEMENT DASHBOARD</h1>', unsafe_allow_html=True)
            st.image("Tiny doctor giving health insurance.jpg", caption='Eden Care Medical', use_column_width=True)
            st.markdown('<h2 class="subheader">Welcome to the Eden Care Claims Management Dashboard Executive View</h2>', unsafe_allow_html=True)

            # Introduction
            st.markdown(
                """
                <div class="text">
                    This comprehensive tool provides a clear and insightful 
                    overview of our claims management performance across several key areas: 
                    <strong>Claims Overview, Claims Analysis, Fraud Detection, Loss Ratio Analysis, and Claim Type Insights</strong>. 
                    <br><br>
                    - The <strong>Claims Overview</strong> offers a high-level summary of all claims processed.
                    - The <strong>Claims Analysis</strong> dives deeper into claim details, providing insights into trends and patterns.
                    - The <strong>Fraud Detection</strong> section helps identify potential fraudulent claims using advanced analytics.
                    - The <strong>Loss Ratio Analysis</strong> evaluates the financial performance of claims processing by analyzing the ratio of claims paid to premiums earned.
                    - The <strong>Claim Type View</strong> categorizes claims by type, offering insights into common claim categories and their impact.
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown('<div class="separator"></div>', unsafe_allow_html=True)

            # User Instructions
            st.markdown('<h2 class="subheader">User Instructions</h2>', unsafe_allow_html=True)
            st.markdown('<div class="text">1. <strong>Navigation:</strong> Use the menu on the left to navigate between visits, claims and Preauthorisation dashboards.</div>', unsafe_allow_html=True)
            st.markdown('<div class="text">2. <strong>Filters:</strong> Apply filters on the left side of each page to customize the data view.</div>', unsafe_allow_html=True)
            st.markdown('<div class="text">3. <strong>Manage visuals:</strong> Hover over the visuals and use the options on the top right corner of each visual to download zoom or view on fullscreen</div>', unsafe_allow_html=True)
            st.markdown('<div class="text">3. <strong>Manage Table:</strong> click on the dropdown icon (<img src="https://img.icons8.com/ios-glyphs/30/000000/expand-arrow.png"/>) on table below each visual to get a full view of the table data and use the options on the top right corner of each table to download or search and view on fullscreen.</div>', unsafe_allow_html=True)    
            st.markdown('<div class="text">4. <strong>Refresh Data:</strong> The data will be manually refreshed on the last week of every quarter. </div>', unsafe_allow_html=True)
            st.markdown('<div class="separator"></div>', unsafe_allow_html=True)

        

    # Claims Analysis Tab
    with tabs[1]:
        display_analysis()

    with tabs[2]:
        display_product()

    with tabs[3]:
        display_claim_type()

    with tabs[4]:
        display_fraud()

    with tabs[5]:
        display_loss_ratio()

# Streamlit app
def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""

    if st.session_state['logged_in']:
        display_dashboard(st.session_state['username'])
    else:
        st.title("Login Page")

        username = st.text_input("Enter username")
        password = st.text_input("Enter password", type="password")
        
        st.markdown('<div class="text">Please double-click on the login or logout button </div>', unsafe_allow_html=True)
        if st.button("Login"):
            if authenticate(username, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.success("Authentication successful")
                st.experimental_rerun()
            else:
                st.error("Authentication failed")

if __name__ == "__main__":
    main()
