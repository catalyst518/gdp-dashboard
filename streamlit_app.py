import streamlit as st
import pandas as pd
import math
from pathlib import Path

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Global Electricity Dashboard',
    page_icon=':electric_plug:',
)

@st.cache_data
def get_electricity_data():
    """Grab electricity data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
    DATA_FILENAME = Path(__file__).parent/'data/electricity_data.csv'
    raw_df = pd.read_csv(DATA_FILENAME)

    # remove invalid measurements, "--", "ie", or blanks
    raw_df.replace("--",pd.NA,inplace=True)
    raw_df.replace("ie",pd.NA,inplace=True)
    raw_df.replace("",pd.NA,inplace=True)

    # cleanup strings
    raw_df['Country']=raw_df['Country'].str.strip()
    raw_df['Features']=raw_df['Features'].str.strip()

    # transform table into country, year, measurement format rather than a column for each year
    raw_df=raw_df.melt(id_vars=['Country','Features','Region'], var_name='Year', value_name='Value')
    raw_df['Year']=raw_df['Year'].astype('int')
    raw_df.dropna(inplace=True)#drop NaN measurements
    raw_df['Value']=raw_df['Value'].astype('float')

    # pivot and create columns for each measurement type by year
    raw_df=raw_df.pivot_table(values='Value', index=['Country', 'Region', 'Year'], columns='Features')
    raw_df.reset_index(inplace=True)

    return raw_df

elec_df = get_electricity_data()

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# :electric_plug: Global Electricity Dashboard

Browse global electricity statistics from [Kaggle](https://www.kaggle.com/datasets/akhiljethwa/global-electricity-statistics/data).

The data includes yearly data from 1980 to 2021 and contains measurements such as net generation (billion kWh), net consumption (billion kWh), and installed capacity (million kW).
'''

st.header('Raw Data', divider='gray')
'''Here's a view of the raw data in table format.'''
st.dataframe(elec_df)

st.header('Settings', divider='gray')

min_value = elec_df['Year'].min()
max_value = elec_df['Year'].max()

from_year, to_year = st.slider(
    'Which years are you interested in?',
    min_value=min_value,
    max_value=max_value,
    value=[min_value, max_value])

countries = elec_df['Country'].unique()

if not len(countries):
    st.warning("Select at least one country")

selected_countries = st.multiselect(
    'Which countries would you like to view?',
    countries,
    ['United States', 'France', 'China', 'India', 'Japan'])


# Filter the data
filtered_elec_df = elec_df[
    (elec_df['Country'].isin(selected_countries))
    & (elec_df['Year'] <= to_year)
    & (from_year <= elec_df['Year'])
]

st.header('Plots', divider='gray')
st.subheader('Net Consumption (billions of kWh)', divider='gray')


st.line_chart(
    filtered_elec_df,
    x='Year',
    y='net consumption',
    color='Country',
)

first_year = elec_df[elec_df['Year'] == from_year]
last_year = elec_df[elec_df['Year'] == to_year]

st.subheader(f'Net Consumption (kWh) in {to_year}\nPercent difference compared to {from_year}', divider='gray')

cols = st.columns(4)

for i, country in enumerate(selected_countries):
    col = cols[i % len(cols)]

    with col:
        first_data = first_year[first_year['Country'] == country]['net consumption'].iat[0]
        last_data = last_year[last_year['Country'] == country]['net consumption'].iat[0]

        if math.isnan(first_data):
            growth = 'n/a'
            delta_color = 'off'
        else:
            growth = f'{100*(last_data-first_data) / first_data:,.1f}%'
            delta_color = 'normal'

        st.metric(
            label=f'{country}',
            value=f'{last_data:,.0f}B',
            delta=growth,
            delta_color=delta_color
        )
