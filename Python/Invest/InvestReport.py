import streamlit as st
import pyodbc as pyod
import pandas as pd
import plotly.express as px
import numpy as np

# Define the connection string
connection_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=AGILEDB\\DEV2019;"
    "Database=UON;"
    "Uid=erp;"
    "Pwd=Pass@7046.;"
)

# Connect to the database
connection = pyod.connect(connection_str)
cursor = connection.cursor()

# Read data from the database
G_LEntry = pd.read_sql(
    """
    SELECT *, b.[G_L Account No_] 
    FROM [UON PEN RBS$G_L Entry$7d966dd5-a317-4db2-b529-926bbce15abf] a
    JOIN [UON PEN RBS$G_L Entry$437dbf0e-84ff-417a-965d-ed2bb9650972] b
    ON a.[Entry No_] = b.[Entry No_]
    """, 
    connection
)

# Function to rename duplicate columns
def rename_duplicate_columns(df):
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
        cols[cols[cols == dup].index.values.tolist()] = [dup + '_' + str(i) if i != 0 else dup for i in range(sum(cols == dup))]
    df.columns = cols
    return df

# Rename duplicate columns in G_LEntry DataFrame
G_LEntry = rename_duplicate_columns(G_LEntry)

# Define the investment type mapping
investment_type_mapping = {
    "120-0009": "Coperate Bonds",
    "120-0004": "OffShore",
    "120-0006": "Quoted Equities",
    "120-0010": "ShortTerm Deposit",
    "120-0008": "Treasury Bills",
    "120-0007": "Treasury Bonds",
    "120-0005": "Unquoted Equities"
}

# Create Investment Type column
G_LEntry['Investment Type'] = G_LEntry['G_L Account No_'].map(investment_type_mapping).fillna('Other')

# Filter out "Other" investment type
G_LEntry_filtered = G_LEntry[G_LEntry['Investment Type'] != 'Other']

# Convert PDateExt to datetime
G_LEntry_filtered['PDateExt'] = pd.to_datetime(G_LEntry_filtered['PDateExt'], errors='coerce')

# Extract year, month, and quarter from PDateExt
G_LEntry_filtered['Year'] = G_LEntry_filtered['PDateExt'].dt.year
G_LEntry_filtered['Month'] = G_LEntry_filtered['PDateExt'].dt.month
G_LEntry_filtered['Quarter'] = G_LEntry_filtered['PDateExt'].dt.to_period('Q')

# Create a summary table grouping by Investment Type and summing AmtExt
summary = G_LEntry_filtered.groupby('Investment Type')['AmtExt'].sum().reset_index()

# Format AmtExt values for better readability
def format_large_numbers(num):
    if num >= 1_000_000_000:
        return f'{num/1_000_000_000:.2f}B'
    elif num >= 1_000_000:
        return f'{num/1_000_000:.2f}M'
    elif num >= 1_000:
        return f'{num/1_000:.2f}K'
    else:
        return str(num)

summary['Formatted AmtExt'] = summary['AmtExt'].apply(format_large_numbers)

# Display the summary table
st.write("Investment Summary Table:")
st.dataframe(summary)

# Create a bar chart with formatted values
bar_chart = px.bar(
    summary, 
    x='Investment Type', 
    y='AmtExt', 
    text='Formatted AmtExt',
    title='Investment Type Summary'
)
bar_chart.update_traces(textposition='outside')

# Display the bar chart
st.plotly_chart(bar_chart)

# Create a pie chart
pie_chart = px.pie(
    summary, 
    values='AmtExt', 
    names='Investment Type', 
    title='Investment Type Distribution'
)

# Display the pie chart
st.plotly_chart(pie_chart)

# Displaying the filtered DataFrame with year, month, and quarter
st.write("Filtered DataFrame with Year, Month, and Quarter:")
st.dataframe(G_LEntry_filtered.head(10))

# Summary tables by year, month, and quarter
year_summary = G_LEntry_filtered.groupby(['Year', 'Investment Type'])['AmtExt'].sum().reset_index()
month_summary = G_LEntry_filtered.groupby(['Year', 'Month', 'Investment Type'])['AmtExt'].sum().reset_index()
quarter_summary = G_LEntry_filtered.groupby(['Year', 'Quarter', 'Investment Type'])['AmtExt'].sum().reset_index()

st.write("Summary by Year:")
st.dataframe(year_summary)

st.write("Summary by Month:")
st.dataframe(month_summary)

st.write("Summary by Quarter:")
st.dataframe(quarter_summary)