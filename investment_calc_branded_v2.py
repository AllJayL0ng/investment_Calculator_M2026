import streamlit as st
import pandas as pd
import altair as alt
import os

# --- PATH CONFIGURATION ---
# This forces Python to look in the exact folder where this script is saved
current_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(current_dir, "logo.png")
icon_path = os.path.join(current_dir, "icon.png")

# --- PAGE CONFIGURATION ---
try:
    st.set_page_config(
        
        page_title="Mazi Asset Management | Investment Calculator",
        page_icon=icon_path if os.path.exists(icon_path) else None,
        layout="wide"
    )
    
except Exception:
    st.set_page_config(page_title="Mazi Asset Management | Investment Calculator", layout="wide")

# --- BRANDING & STYLE BLOCK ---
st.markdown("""
    <style>
    /* 1. IMPORT FONT */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

    /* 2. GENERAL SETTINGS */
    html, body, [class*="css"] {
        font-family: 'Poppins black', 'poppins';
        color: #262730; /* Default Text Color (Dark Grey) */
    }

    /* 3. MAIN TITLE COLOR */
    h1 {
        color: #C5A059 !important; /* Mazi Gold */
        font-weight: 600 !important;
    }

    /* 4. SIDEBAR HEADINGS */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #C5A059 !important; /* Mazi Gold */
    }

    /* 5. INPUT LABELS (Text above the boxes) */
    .stNumberInput label, .stSelectbox label, .stTextInput label {
        color: #FFFFFF !important; /* Pure Black for readability */
        font-size: 1rem !important;
        font-weight: 500 !important;
    }

    /* 6. INPUT VALUES (The numbers inside the boxes) */
    input {
        color: #FFFFFF !important; /* Dark Grey */
    }

    /* 7. THE 'CALCULATE' BUTTON */
    div.stButton > button:first-child {
        background-color: #77121b !important; /* Button Background (Gold) */
        color: white !important;               /* Button Text (White) */
        border-radius: 5px;
        border: none;
        font-weight: 600;
    }
    
    /* Hover effect for the button */
    div.stButton > button:first-child:hover {
        background-color: #B08D45 !important; /* Slightly darker Gold when hovering */
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: BRANDING & INPUTS ---
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_container_width=True)
else:
    st.sidebar.warning("⚠️ Logo not found. Check 'logo.png' is in the folder.")

st.sidebar.header("Investment Parameters")

# Inputs default to 0.0 so the app starts blank
initial_investment = st.sidebar.number_input("Initial Investment (R)", min_value=0.0, value=0.0, step=1000.0)
monthly_step = st.sidebar.number_input("Starting Monthly Installment (R)", min_value=0.0, value=0.0, step=100.0)
escalation_input = st.sidebar.number_input("Annual Installment Escalation (%)", min_value=0.0, value=6.0, step=0.5)
escalation_rate = escalation_input / 100.0

# Return Options
return_options = {
    "Cash (6%)": 0.06,
    "Balanced (10%)": 0.10,
    "Equity (13%)": 0.13
}
selected_option = st.sidebar.selectbox("Select Return Profile", list(return_options.keys()))
annual_return = return_options[selected_option]

# --- MAIN PAGE ---
st.title("📈 Investment Growth Calculator")
st.write("Visualizing long-term compound growth for Mazi Asset Management clients.")

# --- CALCULATE LOGIC ---
if st.sidebar.button("Calculate"):
    
    if initial_investment == 0 and monthly_step == 0:
        st.warning("Please enter a value greater than 0 for either the Initial Investment or the Monthly Installment.")
    else:
        # 1. GENERATE THE DATA
        months = 30 * 12
        data = []
        
        current_balance = initial_investment
        current_monthly_installment = monthly_step
        total_capital = initial_investment

        for m in range(1, months + 1):
            # Apply escalation every 12 months (Month 13, 25, 37...)
            if m > 1 and (m - 1) % 12 == 0:
                current_monthly_installment *= (1 + escalation_rate)
            
            # Track total capital invested (Money out of pocket)
            total_capital += current_monthly_installment
            
            # Calculate monthly interest (Geometric mean)
            monthly_return = (1 + annual_return) ** (1/12) - 1
            
            # Add installment and apply interest
            current_balance = (current_balance + current_monthly_installment) * (1 + monthly_return)
            
            # Store Year-End snapshots
            if m % 12 == 0:
                data.append({
                    "Year": m // 12,
                    "Total Amount": current_balance,
                    "Monthly Installment": current_monthly_installment,
                    "Total Capital Contributed": total_capital,
                    "Investment Return": current_balance - total_capital
                })

        df = pd.DataFrame(data)

        # 2. SECTION 1: MILESTONE SUMMARY (Years 1, 3, 5, 10, 20, 30)
        st.markdown("---")
        milestones = [1, 3, 5, 10, 20, 30]
        milestone_df = df[df['Year'].isin(milestones)].copy()

        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader(f"Summary: {selected_option}")
            # Format table as Currency
            display_df = milestone_df.set_index("Year")[['Total Amount']].copy()
            display_df['Total Amount'] = display_df['Total Amount'].apply(lambda x: f"R {x:,.2f}")
            st.table(display_df)

        with col2:
            st.subheader("Milestone Growth Projection")
            # Green Bar Chart
            chart1 = alt.Chart(milestone_df).mark_bar(color='#535a62').encode(
                x=alt.X('Year:O', sort=milestones, title='Year', axis=alt.Axis(labelAngle=0)),
                y=alt.Y('Total Amount:Q', title='Total Amount (R)'),
                tooltip=[alt.Tooltip('Year:O'), alt.Tooltip('Total Amount:Q', format=',.2f')]
            ).properties(height=350)
            st.altair_chart(chart1, use_container_width=True)

        # 3. SECTION 2: CAPITAL VS RETURN (Every 5 Years)
        st.markdown("---")
        st.subheader("Capital vs. Return Breakdown (5-Year Intervals)")
        
        # Filter for years 5, 10, 15, 20, 25, 30
        five_year_intervals = [5, 10, 15, 20, 25, 30]
        stacked_df = df[df['Year'].isin(five_year_intervals)].copy()

        # Reshape data for stacking
        df_melted = stacked_df.melt(
            id_vars=['Year'], 
            value_vars=['Total Capital Contributed', 'Investment Return'],
            var_name='Component', 
            value_name='Amount'
        )

        # SortOrder: 0 = Bottom (Capital), 1 = Top (Return)
        df_melted['SortOrder'] = df_melted['Component'].apply(
            lambda x: 0 if x == 'Total Capital Contributed' else 1
        )

        # Stacked Chart (Blue Bottom / Red Top)
        stacked_chart = alt.Chart(df_melted).mark_bar().encode(
            x=alt.X('Year:O', sort=five_year_intervals, title='Year', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('Amount:Q', title='Amount (R)'),
            color=alt.Color(
                'Component:N', 
                scale=alt.Scale(
                    domain=['Total Capital Contributed', 'Investment Return'], 
                    range=['#535a62', '#77121b'] # Mazi Grey = Capital, Red = Return
                ),
                legend=alt.Legend(title="Value Component", orient='top-left')
            ),
            order=alt.Order('SortOrder:Q', sort='ascending'), # Force stacking order
            tooltip=[
                alt.Tooltip('Year:O'), 
                alt.Tooltip('Component:N'), 
                alt.Tooltip('Amount:Q', format=',.2f')
            ]
        ).properties(height=500)

        st.altair_chart(stacked_chart, use_container_width=True)