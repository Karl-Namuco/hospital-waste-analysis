import streamlit as st
import pandas as pd
import plotly.express as px


st.set_page_config(page_title="Hospital Waste Management", layout="wide")


@st.cache_data
def load_data():
    df = pd.read_csv("enriched_hospital_waste_data.csv")
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.strftime('%B')
    
    def get_bin_color(infectious, waste_type):
        if infectious == "Yes":
            if "Sharps" in str(waste_type):
                return "Red" 
            return "Yellow" 
        else:
            if "Recyclable" in str(waste_type):
                return "Blue"
            return "Black" 

    if 'Bin_Color' not in df.columns:
        df['Bin_Color'] = df.apply(lambda x: get_bin_color(x['Infectious'], x.get('Waste_Type', '')), axis=1)
        
    return df

df = load_data()

st.sidebar.header("Dashboard Controls")


month_order = [
    "January", "February", "March", "April", "May", "June", 
    "July", "August", "September", "October", "November", "December"
]
available_months = [m for m in month_order if m in df['Month'].unique()]

selected_months = st.sidebar.multiselect(
    "Select Month(s):",
    options=available_months,
    default=available_months, 
    placeholder="Choose months to analyze..."
)

selected_dept = st.sidebar.multiselect(
    "Filter by Department:",
    options=df["Department"].unique(),
    default=df["Department"].unique()
)

mask = (
    (df["Month"].isin(selected_months)) & 
    (df["Department"].isin(selected_dept))
)
filtered_df = df.loc[mask]

st.header("Hospital Waste Management Audit (2024 Data)")
st.subheader("Operational Overview: Infectious vs. Non-Infectious Generation")


if len(selected_months) == 12:
    period_text = "Full Year 2024"
else:
    period_text = f"{', '.join(selected_months)} 2024"
st.caption(f"**Reporting Period:** {period_text}")

with st.container(border=True):
    st.subheader("Key Metrics")
    total_waste = filtered_df["Weight_kg"].sum()
    infectious_waste = filtered_df[filtered_df["Infectious"] == "Yes"]["Weight_kg"].sum()
    avg_daily = filtered_df["Weight_kg"].mean()
    max_waste = filtered_df["Weight_kg"].max()

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Waste Volume", f"{total_waste:,.1f} kg", delta="Accumulated")
    kpi2.metric("Infectious Waste", f"{infectious_waste:,.1f} kg", delta="Biohazard Risk", delta_color="inverse")
    kpi3.metric("Avg. Daily Output", f"{avg_daily:,.2f} kg")
    kpi4.metric("Max Recorded Spike", f"{max_waste:,.2f} kg")

with st.container(border=True):
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Risk Analysis: Infectious Ratio")
        fig_pie = px.pie(filtered_df, names="Infectious", values="Weight_kg", 
                         color="Infectious", hole=0.4,
                         color_discrete_map={"Yes":"#AE5061", "No":"#6FD2EB"})
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("Total Volume by Department")
        dept_group = filtered_df.groupby("Department")["Weight_kg"].sum().reset_index().sort_values("Weight_kg")
        fig_bar = px.bar(dept_group, x="Weight_kg", y="Department", orientation='h',
                         color="Department", text_auto=True)
        st.plotly_chart(fig_bar, use_container_width=True)

with st.container(border=True):
    st.subheader("Waste Composition & Segregation Audit")
    col3, col4 = st.columns([1, 1])
    
    with col3:
        st.caption("Volume by Specific Waste Category")
        if "Waste_Type" in filtered_df.columns:
            type_group = filtered_df.groupby("Waste_Type")["Weight_kg"].sum().reset_index().sort_values("Weight_kg", ascending=False)
            fig_type = px.bar(type_group, x="Waste_Type", y="Weight_kg",
                              color="Waste_Type", text_auto=True)
            fig_type.update_layout(showlegend=False)
            st.plotly_chart(fig_type, use_container_width=True)
        else:
            st.warning("Waste_Type column missing.")

    with col4:
        st.caption("Bin Color Distribution (Compliance Check)")
        if "Bin_Color" in filtered_df.columns:
            bin_group = filtered_df.groupby("Bin_Color")["Weight_kg"].sum().reset_index()
            color_map = {
                "Yellow": "#FFD700", 
                "Red": "#DC143C",    
                "Black": "#2F4F4F",  
                "Blue": "#1E90FF"    
            }
            fig_bin = px.pie(bin_group, names="Bin_Color", values="Weight_kg",
                             color="Bin_Color", hole=0.4,
                             color_discrete_map=color_map)
            st.plotly_chart(fig_bin, use_container_width=True)

with st.container(border=True):
    st.subheader("Comparative Analysis: Infectious vs. Non-Infectious by Department")
    grouped_df = filtered_df.groupby(["Department", "Infectious"])["Weight_kg"].sum().reset_index()
    fig_grouped = px.bar(grouped_df, x="Department", y="Weight_kg", 
                         color="Infectious", 
                         barmode="group", 
                         text_auto=True,
                         color_discrete_map={"Yes":"#AE5061", "No":"#6FD2EB"})
    st.plotly_chart(fig_grouped, use_container_width=True)

with st.container(border=True):
    st.subheader("Timeline Analysis: Waste Generation Spikes")
    trend_data = filtered_df.sort_values("Date").groupby("Date")["Weight_kg"].sum().reset_index()
    fig_line = px.area(trend_data, x="Date", y="Weight_kg", 
                       title="Daily Waste Volume (kg) - Interactive Zoom",
                       color_discrete_sequence=["#00AEDF"])
    st.plotly_chart(fig_line, use_container_width=True)

st.markdown("---")
with st.expander("View Raw Data (Audit Trail)"):
    st.dataframe(filtered_df)
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Filtered Data as CSV", 
        data=csv, 
        file_name='hospital_waste_audit_data.csv', 
        mime='text/csv'
    )

st.sidebar.caption("Project: ITE3 Health Informatics")
st.sidebar.caption("Passed By: Namuco, Karl Cedrick R.")
st.sidebar.caption("Data Source: Medical Waste Classification (2024) - https://www.kaggle.com/datasets/rohitshetty04/medical-waste-classification")