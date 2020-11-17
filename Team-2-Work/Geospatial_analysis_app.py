#Import necesssay libraries
import pandas as pd
import numpy as np
import streamlit as st
from bokeh.plotting import figure
from bokeh.models import HoverTool, ColumnDataSource, CategoricalColorMapper
from bokeh.tile_providers import get_provider, Vendors

import warnings
warnings.filterwarnings('ignore')

# Define plot navigation tools
TOOLS = 'pan,wheel_zoom,zoom_in,zoom_out,box_zoom,reset,save'
# Instantiate CategoricalColorMapper that Categorically maps Casualty Severity into colors.
color_mapper = CategoricalColorMapper(factors=['Slight', 'Serious', 'Fatal'], palette=['red', 'blue', 'green'])

st.sidebar.markdown('''# Road Safety Analysis''')

@st.cache(allow_output_mutation=True)
def load_data():
    '''
    Function to read-in the dataset
    '''
    req_cols1 = ['Accident_Index','Longitude','Latitude', 'Date', 'Time', 'Number_of_Casualties', 'Weather_Conditions']
    req_cols2 = ['Accident_Index', 'Casualty_Severity']
    df1 = pd.read_csv('https://raw.githubusercontent.com/HamoyeHQ/stage-f-01-road-safety/master/data/dftRoadSafety_Accidents_2016.csv', usecols=req_cols1)
    df2 = pd.read_csv('https://raw.githubusercontent.com/HamoyeHQ/stage-f-01-road-safety/master/data/Cas.csv', usecols=req_cols2)

    #----------------------Merging the Datasets--------
    df = pd.merge(df1, df2, on=['Accident_Index'])
    #----------------------FEATURE ENGINEERING AND TRANSFORMATION-------------------------------------
    df['Datetime'] = df['Date'] + ' ' + df['Time']  + ':00'
    df['Datetime'] = pd.to_datetime(df['Datetime'])

    hotspots = df.groupby(by=['Longitude','Latitude','Datetime', 'Casualty_Severity']).mean()[['Number_of_Casualties','Weather_Conditions']]
    hotspots.Weather_Conditions = hotspots.Weather_Conditions.astype(int)
    hotspots['circle_sizes'] = hotspots['Number_of_Casualties'] * 20 / hotspots['Number_of_Casualties'].max()
    hotspots.reset_index(inplace=True)
    hotspots['time'] = hotspots.Datetime.dt.hour

    Severity = {1 : 'Fatal', 2 : 'Serious', 3 : 'Slight'}
    hotspots['Casualty_Severity'].replace(Severity, inplace=True)
    hotspots.drop(columns='Datetime', inplace=True)

    return hotspots

def create_figure(TOOLS, height, source):
    '''
    Function to Create a new figure for plotting.
    '''
    fig = figure(x_axis_type="mercator", y_axis_type="mercator",
                height=height,
                tools = TOOLS)
    # instatiate the tile source provider to use for the map
    tile_provider = get_provider(Vendors.OSM)
    # add the back ground basemap
    fig.add_tile(tile_provider)
    # Add accident points using coordinates ('Longitude' & 'Latitude')
    fig.circle(x='LON',
                y='LAT',
                size='circle_sizes',
                fill_alpha=0.1,
                source=source,
                color={'field': 'Casualty_Severity', 'transform': color_mapper},
                legend_field='Casualty_Severity'
                )
    return fig

def hover(tips):
    '''
    Function to create a hoover inspector tool
    '''
    tool = HoverTool()
    tool.tooltips=tips
    return tool

def wgs84_to_web_mercator(df, lon="Longitude", lat="Latitude"):

    k = 6378137
    df["LON"] = df[lon] * (k * np.pi/180.0)
    df["LAT"] = np.log(np.tan((90 + df[lat]) * np.pi/360.0)) * k

    return df

data = load_data()

status = st.sidebar.radio('',('Select time of the day',
                              'Select weather Condition'))

#-------Select time of the day--------------------
if status == 'Select time of the day':
    timer = st.sidebar.slider("Time of the day:", 0, 23, 12)
    size = st.sidebar.slider("Zoom accident points:", 10, 40, 20)

    f'#### Spatial distribution of accident hotspots at {timer} hours'

    defaultdata = data[data.time == timer]
    defaultdata['circle_sizes'] = defaultdata['Number_of_Casualties'] * size / defaultdata['Number_of_Casualties'].max()

    # Tell Bokeh to use 'hotspots' as the source of the data
    data_source = ColumnDataSource(data=wgs84_to_web_mercator(defaultdata))

    p = create_figure(TOOLS=TOOLS, height=500, source=data_source)
    h = hover([("No. of Casualties", "@Number_of_Casualties"),
                ("(Long, Lat)", "(@Longitude, @Latitude)"),
                ("Severity", "@Casualty_Severity"),])
    p.add_tools(h)
    st.bokeh_chart(p, use_container_width=True)

else:
    Weather_Conditions = {'Fine no high winds' : 1, 'Raining no high winds' : 2, 'Snowing no high winds' : 3,
                          'Fine + high winds' : 4, 'Raining + high winds' : 5, 'Snowing + high winds' : 6,
                          'Fog or mist' : 7, 'Other' : 8, 'Unknown' : 9}
    w = [i for i in Weather_Conditions.keys()]

    weather = st.sidebar.selectbox( 'Select weather Condition:', tuple(w))
    size = st.sidebar.slider("Zoom accident points:", 10, 40, 20)

    wi = Weather_Conditions[weather]
    f'#### Spatial distribution of accident hotspots when the weather condition is {weather}'

    defaultdata = data[data.Weather_Conditions == wi]
    defaultdata['circle_sizes'] = defaultdata['Number_of_Casualties'] * size / defaultdata['Number_of_Casualties'].max()

    # Tell Bokeh to use 'hotspots' as the source of the data
    data_source = ColumnDataSource(data=wgs84_to_web_mercator(defaultdata))

    p = create_figure(TOOLS=TOOLS, height=500, source=data_source)
    h = hover([("No. of Casualties", "@Number_of_Casualties"),
                ("(Long, Lat)", "(@Longitude, @Latitude)"),
                ("Severity", "@Casualty_Severity"),])
    p.add_tools(h)
    st.bokeh_chart(p, use_container_width=True)

st.sidebar.markdown('''
### Developed by
[Team Road Safety - HDSC](https://github.com/HamoyeHQ/stage-f-01-road-safety)

Source code available [here](https://github.com/HamoyeHQ/stage-f-01-road-safety/tree/master/Team-2-Work)''')

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
