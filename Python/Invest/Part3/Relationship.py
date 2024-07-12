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

# Sample additional tables for demonstration (replace with your actual table data)
# For simplicity, here we're using a subset of the G_LEntry table as additional tables
# Replace these with actual tables from your database or other sources as needed
Other_Table_1 = G_LEntry.sample(10)
Other_Table_2 = G_LEntry.sample(10)

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
    "120-0009": "Corporate Bonds",
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

# Sidebar filters
st.sidebar.header('Filters')
investment_type = st.sidebar.selectbox(
    'Select Investment Type', 
    options=['All'] + list(G_LEntry_filtered['Investment Type'].unique())
)
year = st.sidebar.selectbox(
    'Select Year', 
    options=['All'] + list(G_LEntry_filtered['Year'].unique())
)
month = st.sidebar.selectbox(
    'Select Month', 
    options=['All'] + list(range(1, 13))
)
quarter = st.sidebar.selectbox(
    'Select Quarter', 
    options=['All'] + list(G_LEntry_filtered['Quarter'].unique().astype(str))
)

# Filter the data based on selections
filtered_data = G_LEntry_filtered.copy()
if investment_type != 'All':
    filtered_data = filtered_data[filtered_data['Investment Type'] == investment_type]

if year != 'All':
    filtered_data = filtered_data[filtered_data['Year'] == int(year)]

if month != 'All':
    filtered_data = filtered_data[filtered_data['Month'] == int(month)]

if quarter != 'All':
    filtered_data = filtered_data[filtered_data['Quarter'].astype(str) == quarter]

# Display the summary table
st.title("Investment Dashboard")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Summary", "Data Modeling", "Detailed Data", "Visualizations", "Build Report"])

with tab1:
    st.header("Investment Summary Table")
    st.dataframe(summary)

# For storing relationships
if 'relationships' not in st.session_state:
    st.session_state['relationships'] = []

with tab2:
    st.header("Data Modeling")

    if st.button("Add New Relationship"):
        with st.form(key='relationship_form'):
            # Select left table
            left_table_name = st.selectbox(
                "Select Left Table",
                options=["G_LEntry", "Other_Table_1", "Other_Table_2"]
            )

            # Select right table
            right_table_name = st.selectbox(
                "Select Right Table",
                options=["G_LEntry", "Other_Table_1", "Other_Table_2"]
            )

            # Load selected tables
            left_table = globals()[left_table_name]
            right_table = globals()[right_table_name]

            # Select common columns for joining
            left_column = st.selectbox(
                "Select Column from Left Table",
                options=left_table.columns
            )
            right_column = st.selectbox(
                "Select Column from Right Table",
                options=right_table.columns
            )

            # Select join type
            join_type = st.selectbox(
                "Select Join Type",
                options=["inner", "left", "right", "outer"]
            )

            # Submit button for the form
            submit_button = st.form_submit_button(label='Create Relationship')

            if submit_button:
                joined_table = pd.merge(
                    left_table, 
                    right_table, 
                    left_on=left_column, 
                    right_on=right_column, 
                    how=join_type
                )
                relationship = {
                    "left_table": left_table_name,
                    "right_table": right_table_name,
                    "left_column": left_column,
                    "right_column": right_column,
                    "join_type": join_type,
                    "joined_table": joined_table
                }
                st.session_state['relationships'].append(relationship)
                st.success("Relationship created successfully!")
                st.experimental_rerun()

    st.write("Existing Relationships:")
    for i, relationship in enumerate(st.session_state['relationships']):
        st.write(f"Relationship {i+1}: {relationship['left_table']} [{relationship['left_column']}] {relationship['join_type']} JOIN {relationship['right_table']} [{relationship['right_column']}]")
        st.dataframe(relationship['joined_table'].head(10))

with tab3:
    st.header("Filtered DataFrame with Year, Month, and Quarter")
    st.dataframe(filtered_data.head(10))

    # Summary tables by year, month, and quarter
    year_summary = filtered_data.groupby(['Year', 'Investment Type'], as_index=False)['AmtExt'].sum()
    month_summary = filtered_data.groupby(['Year', 'Month', 'Investment Type'], as_index=False)['AmtExt'].sum()
    quarter_summary = filtered_data.groupby(['Year', 'Quarter', 'Investment Type'], as_index=False)['AmtExt'].sum()

    st.write("Summary by Year:")
    st.dataframe(year_summary)

    st.write("Summary by Month:")
    st.dataframe(month_summary)

    st.write("Summary by Quarter:")
    st.dataframe(quarter_summary)

with tab4:
    st.header("Visualizations")

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

# For storing reports
if 'reports' not in st.session_state:
    st.session_state['reports'] = []

with tab5:
    st.header("Build Report")

    # Create a new report section
    if st.button("Create New Report"):
        st.session_state['reports'].append({"charts": []})
        st.experimental_rerun()

    # Display existing reports
    for i, report in enumerate(st.session_state['reports']):
        st.subheader(f"Report {i + 1}")

        # Allow user to select chart type
        chart_type = st.selectbox(
            f"Select Chart Type for Report {i + 1}",
            options=["Bar Chart", "Line Chart", "Scatter Plot", "Pie Chart"],
            key=f"chart_type_{i}"
        )

        # Allow users to select x and y axis
        x_axis = st.selectbox(f"Select X-Axis for Report {i + 1}", options=filtered_data.columns, key=f"x_axis_{i}")
        y_axis = st.selectbox(f"Select Y-Axis for Report {i + 1}", options=filtered_data.columns, key=f"y_axis_{i}")

        # Allow users to select aggregation operator
        operator = st.selectbox(
            f"Select Aggregation Operator for Report {i + 1}",
            options=["SUM", "COUNT", "AVERAGE", "MIN", "MAX"],
            key=f"operator_{i}"
        )

        # Data labels option
        show_data_labels = st.checkbox(f"Show Data Labels for Report {i + 1}", value=True, key=f"show_data_labels_{i}")
        label_format = st.selectbox(
            f"Select Data Label Format for Report {i + 1}", 
            options=["Actual Values", "Formatted Values"],
            key=f"label_format_{i}"
        )

        # Perform aggregation based on operator
        if operator == "SUM":
            y_data = filtered_data.groupby(x_axis, as_index=False)[y_axis].sum()
        elif operator == "COUNT":
            y_data = filtered_data.groupby(x_axis, as_index=False)[y_axis].count()
        elif operator == "AVERAGE":
            y_data = filtered_data.groupby(x_axis, as_index=False)[y_axis].mean()
        elif operator == "MIN":
            y_data = filtered_data.groupby(x_axis, as_index=False)[y_axis].min()
        elif operator == "MAX":
            y_data = filtered_data.groupby(x_axis, as_index=False)[y_axis].max()

        # Create data labels
        if show_data_labels:
            if label_format == "Actual Values":
                y_data['Data Labels'] = y_data[y_axis].apply(lambda x: f'{x:,.0f}' if isinstance(x, (int, float)) else x)
            else:
                y_data['Data Labels'] = y_data[y_axis].apply(lambda x: format_large_numbers(x) if isinstance(x, (int, float)) else x)

        # Create the selected chart
        if chart_type == "Bar Chart":
            chart = px.bar(y_data, x=x_axis, y=y_axis, title=f'{chart_type} of {y_axis} ({operator}) vs {x_axis}')
            if show_data_labels:
                chart.update_traces(text=y_data['Data Labels'], textposition='outside')
        elif chart_type == "Line Chart":
            chart = px.line(y_data, x=x_axis, y=y_axis, title=f'{chart_type} of {y_axis} ({operator}) vs {x_axis}')
            if show_data_labels:
                chart.update_traces(text=y_data['Data Labels'], textposition='top center')
        elif chart_type == "Scatter Plot":
            chart = px.scatter(y_data, x=x_axis, y=y_axis, title=f'{chart_type} of {y_axis} ({operator}) vs {x_axis}')
            if show_data_labels:
                chart.update_traces(text=y_data['Data Labels'], textposition='top center')
        elif chart_type == "Pie Chart":
            chart = px.pie(y_data, values=y_axis, names=x_axis, title=f'{chart_type} of {x_axis} ({operator})')
            if show_data_labels:
                chart.update_traces(text=y_data['Data Labels'], textposition='inside')

        # Store the chart in the report
        st.session_state['reports'][i]['charts'].append(chart)

        # Display the chart
        st.plotly_chart(chart)

    if st.button("Add New Report"):
        st.session_state['reports'].append({"charts": []})
        st.experimental_rerun()

# Close the database connection
cursor.close()
connection.close()