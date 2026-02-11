import streamlit as st
import pandas as pd
import altair as alt

# --- Page Configuration ---
st.set_page_config(page_title="Investment Growth Calculator", layout="wide")

st.title("📈 Investment Growth Calculator")
st.write("Visualizing compound growth and capital contribution breakdowns.")

# --- Sidebar Inputs ---
st.sidebar.header("Investment Parameters")

initial_investment = st.sidebar.number_input("Initial Investment (R)", min_value=0.0, value=0.0, step=1000.0)
monthly_step = st.sidebar.number_input("Starting Monthly Installment (R)", min_value=0.0, value=0.0, step=100.0)

# Dynamic Escalation Rate
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

# --- The Calculate Button ---
if st.sidebar.button("Calculate"):
    
    if initial_investment == 0 and monthly_step == 0:
        st.warning("Please enter a value greater than 0 for either the Initial Investment or the Monthly Installment.")
    else:
        # --- Calculation Logic ---
        months = 30 * 12
        data = []
        
        current_balance = initial_investment
        current_monthly_installment = monthly_step
        total_capital = initial_investment

        for m in range(1, months + 1):
            # Apply escalation every 12 months
            if m > 1 and (m - 1) % 12 == 0:
                current_monthly_installment *= (1 + escalation_rate)
            
            # Add installment to our capital tracker
            total_capital += current_monthly_installment
            
            # Calculate monthly interest
            monthly_return = (1 + annual_return) ** (1/12) - 1
            
            # Add installment and apply interest to the balance
            current_balance = (current_balance + current_monthly_installment) * (1 + monthly_return)
            
            # Store yearly snapshots
            if m % 12 == 0:
                data.append({
                    "Year": m // 12,
                    "Total Amount": current_balance,
                    "Monthly Installment": current_monthly_installment,
                    "Total Capital Contributed": total_capital,
                    "Investment Return": current_balance - total_capital
                })

        df = pd.DataFrame(data)

        # --- Display Results: Milestone Table & Chart ---
        st.markdown("---")
        milestones = [1, 3, 5, 10, 20, 30]
        milestone_df = df[df['Year'].isin(milestones)].copy()

        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader(f"Summary: {selected_option}")
            display_df = milestone_df.set_index("Year")[['Total Amount']].copy()
            display_df['Total Amount'] = display_df['Total Amount'].apply(lambda x: f"R {x:,.2f}")
            st.table(display_df)

        with col2:
            st.subheader("Milestone Growth Projection")
            chart1 = alt.Chart(milestone_df).mark_bar(color='#2ca02c').encode(
                x=alt.X('Year:O', sort=milestones, title='Year', axis=alt.Axis(labelAngle=0)),
                y=alt.Y('Total Amount:Q', title='Total Amount (R)'),
                tooltip=[alt.Tooltip('Year:O'), alt.Tooltip('Total Amount:Q', format=',.2f')]
            ).properties(height=300)
            st.altair_chart(chart1, use_container_width=True)

        # --- Display Results: 5-Year Stacked Breakdown ---
        st.markdown("---")
        st.subheader("5-Year Interval Breakdown: Capital vs. Investment Return")
        
        # Filter for every 5 years
        five_year_intervals = [5, 10, 15, 20, 25, 30]
        stacked_df = df[df['Year'].isin(five_year_intervals)].copy()

        # Reshape data for the stacked bar chart 
        df_melted = stacked_df.melt(
            id_vars=['Year'], 
            value_vars=['Total Capital Contributed', 'Investment Return'],
            var_name='Component', 
            value_name='Amount'
        )

        # Create a specific sorting column to control the stack order
        df_melted['SortOrder'] = df_melted['Component'].apply(
            lambda x: 0 if x == 'Total Capital Contributed' else 1
        )

        # Build the stacked chart with explicit ordering
        stacked_chart = alt.Chart(df_melted).mark_bar().encode(
            x=alt.X('Year:O', sort=five_year_intervals, title='Year', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('Amount:Q', title='Amount (R)'),
            color=alt.Color(
                'Component:N', 
                scale=alt.Scale(
                    domain=['Total Capital Contributed', 'Investment Return'], 
                    range=['#1f77b4', '#d62728'] # Blue and Red
                ),
                legend=alt.Legend(title="Value Component", orient='top-left')
            ),
            order=alt.Order('SortOrder:Q', sort='ascending'),
            tooltip=[
                alt.Tooltip('Year:O'), 
                alt.Tooltip('Component:N'), 
                alt.Tooltip('Amount:Q', format=',.2f')
            ]
        ).properties(height=500)

        st.altair_chart(stacked_chart, use_container_width=True)