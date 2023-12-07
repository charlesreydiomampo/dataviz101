import dash
import dash_leaflet as dl
from dash import html, dcc
import json
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import calendar
import dash_bootstrap_components as dbc
from shapely.geometry import LineString
import plotly.graph_objs as go

# Function to convert points to LineString
def convert_points_to_linestring(geojson):
    points = [feature["geometry"]["coordinates"] for feature in geojson["features"]]
    linestring = LineString(points)
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": linestring.__geo_interface__,
            "properties": {}
        }]
    }

# Load the GeoJSON data for points
with open('line1.geojson') as f:
    line1_geojson = json.load(f)
with open('line2.geojson') as f:
    line2_geojson = json.load(f)
with open('line3.geojson') as f:
    line3_geojson = json.load(f)

# Load the GeoJSON data for LineStrings
with open('route_line1.geojson') as f:
    route_line1_geojson = json.load(f)
with open('route_line2.geojson') as f:
    route_line2_geojson = json.load(f)
with open('route_line3.geojson') as f:
    route_line3_geojson = json.load(f)

line1_points = [(feature['geometry']['coordinates'][::-1], feature['properties']['station_name']) for feature in line1_geojson['features']]
line2_points = [(feature['geometry']['coordinates'][::-1], feature['properties']['station_name']) for feature in line2_geojson['features']]
line3_points = [(feature['geometry']['coordinates'][::-1], feature['properties']['station_name']) for feature in line3_geojson['features']]

# Load and process the data for the chart
# Replace 'data.csv' with the path to your CSV file
#data = pd.read_excel('data.xlsx')
data = pd.read_csv('data.csv')
data['Date'] = pd.to_datetime(data['Date'])
data['Year'] = data['Date'].dt.year
data['Month'] = data['Date'].dt.month
data['Weekday'] = data['Date'].dt.dayofweek

# Mapping for month and weekday
month_mapping = {i: month for i, month in enumerate(calendar.month_name) if month}
weekday_mapping = {i: day for i, day in enumerate(calendar.day_name)}

data['Month'] = data['Month'].map(month_mapping)
data['Weekday'] = data['Weekday'].map(weekday_mapping)

# Separate stations based on the line
lrt1_stations = data[data['Line'] == 'LRT1']['Station'].unique()
lrt2_stations = data[data['Line'] == 'LRT2']['Station'].unique()
mrt3_stations = data[data['Line'] == 'MRT3']['Station'].unique()

data['Quarter'] = data['Date'].dt.to_period('Q')
grouped_data = data.groupby(['Quarter', 'Line'])['Value'].mean().reset_index()
mrt3_data = grouped_data[grouped_data['Line'] == 'MRT3']
lrt2_data = grouped_data[grouped_data['Line'] == 'LRT2']
lrt1_data = grouped_data[grouped_data['Line'] == 'LRT1']

# heatmap
raw_data_ = pd.read_csv("Raw-Data-2016-2022.csv")
raw_data_['Date'] = pd.to_datetime(raw_data_['Date'], dayfirst = True)
raw_data_['weekday'] = raw_data_['Date'].dt.dayofweek
#raw_data_['weekday'] = raw_data_['weekday'].map(weekday_mapping)

# Initialize the Dash app
#app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
initial_lat = 14.5547 #14.58901 # Latitude for Makati
initial_lon = 121.03723 #120.95788  # Longitude for Makati

# Define the layout of the app
app.layout = html.Div([
    # Container for the map and chart
    html.Div([
        # Map container
        html.Div([
            dl.Map(center=[initial_lat, initial_lon], zoom=13, children=[
                dl.TileLayer(),
                # LineString layers for connecting lines
                dl.GeoJSON(data=route_line1_geojson, options={'style': {'color': '#4dc262', 'weight': 5}}),
                dl.GeoJSON(data=route_line2_geojson, options={'style': {'color': '#972db8', 'weight': 5}}),
                dl.GeoJSON(data=route_line3_geojson, options={'style': {'color': '#2596be', 'weight': 5}}),
                *[dl.CircleMarker(center=coords, radius=5, color='#4dc262', fill=True, fillOpacity=1.0, children=[
                    dl.Tooltip(name)
                ]) for coords, name in line1_points],
                *[dl.CircleMarker(center=coords, radius=5, color='#972db8', fill=True, fillOpacity=1.0, children=[
                    dl.Tooltip(name)
                ]) for coords, name in line2_points],
                *[dl.CircleMarker(center=coords, radius=5, color='#2596be', fill=True, fillOpacity=1.0, children=[
                    dl.Tooltip(name)
                ]) for coords, name in line3_points],
            ], style={'width': '100%', 'height': '100vh'})
        ], style={'width': '50%', 'float': 'left'}),

        # Chart container
        html.Div([
            html.Div([html.H2("Average Number of Passengers of Each Station")],
                     style={'text-align': 'center'}),
            dcc.RadioItems(
                id='line-selector',
                options=[
                    {'label': 'LRT-1', 'value': 'LRT1'},
                    {'label': 'LRT-2', 'value': 'LRT2'},
                    {'label': 'MRT-3', 'value': 'MRT3'}
                ],
                value='LRT1',
                labelStyle={'display': 'inline-block', 'margin-right': '15px'},  # Keep display as 'inline-block'
            ),
            dcc.Dropdown(
                id='station-selector',
                value='Baclaran'
            ),
            dcc.RadioItems(
                id='time-category-selector',
                options=[
                    {'label': 'Year', 'value': 'Year'},
                    {'label': 'Month', 'value': 'Month'},
                    {'label': 'Weekday', 'value': 'Weekday'}
                ],
                value='Year',
                labelStyle={'display': 'inline-block', 'margin-right': '15px'}
            ),
            dcc.Graph(id='bar-chart', style={'height': '40vh'}),
            html.Br(),
            dcc.Graph(id='heat-map', style={'height': '40vh'})
        ], style={'width': '50%', 'float': 'right'})
    ], style={'display': 'flex', 'width': '100%'})
])

line_colors = {'MRT3': '#2596be', 'LRT2': '#972db8', 'LRT1': '#4dc262'}
# Define callback to update graph based on selected line option
@app.callback(
    Output('line-graph', 'figure'),
    [Input('line-option', 'value')]
)
def update_graph(line_option):
    traces = []
    if line_option == 'MRT3' or line_option == 'All':
        traces.append(go.Scatter(
            x=mrt3_data['Quarter'].dt.to_timestamp(),
            y=mrt3_data['Value'],
            mode='lines',
            name='MRT-3',
            line=dict(color=line_colors['MRT3'])
        ))
    if line_option == 'LRT2' or line_option == 'All':
        traces.append(go.Scatter(
            x=lrt2_data['Quarter'].dt.to_timestamp(),
            y=lrt2_data['Value'],
            mode='lines',
            name='LRT-2',
            line=dict(color=line_colors['LRT2'])
        ))
    if line_option == 'LRT1' or line_option == 'All':
        traces.append(go.Scatter(
            x=lrt1_data['Quarter'].dt.to_timestamp(),
            y=lrt1_data['Value'],
            mode='lines',
            name='LRT-1',
            line=dict(color=line_colors['LRT1'])
        ))

    layout = go.Layout(
        title='Average Number of Passengers Everyday over Year',
        xaxis={'title': 'Timeline'},
        height=300, 
        yaxis={'title': 'Number of Passengers'},
        margin={'l': 40, 'b': 40, 't': 50, 'r': 10},
        hovermode='closest'
    )
    return {'data': traces, 'layout': layout}

# Callbacks for updating the chart
@app.callback(
    Output('station-selector', 'options'),
    Input('line-selector', 'value')
)
def set_station_options(selected_line):
    if selected_line == 'LRT2':
        return [{'label': station, 'value': station} for station in lrt2_stations]
    elif selected_line == 'LRT1':
        return [{'label': station, 'value': station} for station in lrt1_stations]
    else:
        return [{'label': station, 'value': station} for station in mrt3_stations]

@app.callback(
    Output('bar-chart', 'figure'),
    [Input('station-selector', 'value'),
     Input('time-category-selector', 'value')]
)
def update_graph(selected_station, selected_time_category):
    if selected_station is None:
        return px.bar()

    filtered_data = data[data['Station'] == selected_station]

    if not filtered_data.empty:
        avg_values = filtered_data.groupby([selected_time_category])['Value'].mean()

        if selected_time_category == 'Month':
            avg_values = avg_values.reindex(list(calendar.month_name[1:]))
        elif selected_time_category == 'Weekday':
            avg_values = avg_values.reindex(list(calendar.day_name))

        line = filtered_data['Line'].iloc[0]
        if line == 'LRT2':
            color = '#972db8'
        elif line == 'LRT1':
            color = '#4dc262'
        elif line == 'MRT3':
            color = '#2596be'
        else:
            color = 'default_color'

        return px.bar(avg_values, x=avg_values.values, y=avg_values.index, labels={'y': selected_time_category, 'x': 'Average Value'}, orientation='h', title=f'Average Value for {selected_station} per {selected_time_category}', color_discrete_sequence=[color])
    else:
        return px.bar()

@app.callback(
    Output('heat-map', 'figure'),
    [Input('station-selector', 'value'),
     Input('line-selector', 'value'),
     Input('time-category-selector', 'value')]
)
def update_output(selected_station, selected_line, time_category):
    if selected_line == "MRT3":
        df = raw_data_
    
        heatmap_data = df[df["Station"] == selected_station]
        fig = px.imshow(heatmap_data.pivot_table(index="Time", columns="weekday", values="Value", aggfunc="sum"))
        fig.update_xaxes(side="bottom", title="Day of the Week")
        fig.update_layout(title={'text': f'Hourly Heatmap for {selected_station}'}, title_x=0.5,
                 xaxis = dict(
                     tickmode = 'array',
                     tickvals = [0, 1, 2, 3, 4, 5, 6],
                     ticktext = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    ))
    else:
        df = data[data['Line'] == selected_line]
        
        if time_category == "Year":
            time_cat = "Year"
        elif time_category == "Month":
            time_cat = "Month"
        else:
            time_cat = "Year"        
        
        heatmap_data = df[df["Station"] == selected_station]
        fig = px.imshow(heatmap_data.pivot_table(index=time_cat, columns="Weekday", values="Value", aggfunc="sum"))
        fig.update_xaxes(side="bottom", title="Day of the Week")
        fig.update_layout(title={'text': f'Heatmap for {selected_station}'}, title_x=0.5)
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
