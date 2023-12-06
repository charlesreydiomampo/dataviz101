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


# Load the GeoJSON data
with open('line1.geojson') as f:
    line1_geojson = json.load(f)
with open('line2.geojson') as f:
    line2_geojson = json.load(f)
with open('line3.geojson') as f:
    line3_geojson = json.load(f)

with open('line1.geojson') as f:
    line1_linestring_geojson = convert_points_to_linestring(json.load(f))
with open('line2.geojson') as f:
    line2_linestring_geojson = convert_points_to_linestring(json.load(f))
with open('line3.geojson') as f:
    line3_linestring_geojson = convert_points_to_linestring(json.load(f))

line1_points = [(feature['geometry']['coordinates'][::-1], feature['properties']['station_name']) for feature in line1_geojson['features']]
line2_points = [(feature['geometry']['coordinates'][::-1], feature['properties']['station_name']) for feature in line2_geojson['features']]
line3_points = [(feature['geometry']['coordinates'][::-1], feature['properties']['station_name']) for feature in line3_geojson['features']]

# Load and process the data for the chart
# Replace 'data.csv' with the path to your CSV file
data = pd.read_excel('data.xlsx')
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

# heatmap
raw_data_ = pd.read_csv("Raw-Data-2016-2022.csv")

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
initial_lat = 14.5547  # Latitude for Makati
initial_lon = 121.0244 # Longitude for Makati

# Define the layout of the app
app.layout = html.Div([
    # Container for the map and chart
    html.Div([
        # Map container
        html.Div([
        dl.Map(center=[initial_lat, initial_lon], zoom=10, children=[
            dl.TileLayer(),
            # LineString layers for connecting lines
            dl.GeoJSON(data=line1_linestring_geojson, options={'style': {'color': 'green', 'weight': 5}}),
            dl.GeoJSON(data=line2_linestring_geojson, options={'style': {'color': 'purple', 'weight': 5}}),
            dl.GeoJSON(data=line3_linestring_geojson, options={'style': {'color': 'blue', 'weight': 5}}),
            *[dl.CircleMarker(center=coords, radius=5, color='green', fill=True, fillOpacity=1.0, children=[
            dl.Tooltip(name)
                ]) for coords, name in line1_points],
            *[dl.CircleMarker(center=coords, radius=5, color='purple', fill=True, fillOpacity=1.0, children=[
            dl.Tooltip(name)
                ]) for coords, name in line2_points],
            *[dl.CircleMarker(center=coords, radius=5, color='blue', fill=True, fillOpacity=1.0, children=[
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
                    {'label': 'LRT1', 'value': 'LRT1'},
                    {'label': 'LRT2', 'value': 'LRT2'},
                    {'label': 'MRT3', 'value': 'MRT3'}
                ],
                value='LRT2',
                labelStyle={'display': 'inline-block'}
            ),
            dcc.Dropdown(
                id='station-selector',
                value='Recto Station'
            ),
            dcc.RadioItems(
                id='time-category-selector',
                options=[
                    {'label': 'Year', 'value': 'Year'},
                    {'label': 'Month', 'value': 'Month'},
                    {'label': 'Weekday', 'value': 'Weekday'}
                ],
                value='Year',
                labelStyle={'display': 'inline-block'}
            ),
            dcc.Graph(id='bar-chart', style={'height': '40vh'}),
            html.Br(),
            dcc.Graph(id='heat-map', style={'height': '40vh'})
        ], style={'width': '50%', 'float': 'right'})
    ], style={'display': 'flex', 'width': '100%'})
])

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
            color = 'purple'
        elif line == 'LRT1':
            color = 'green'
        elif line == 'MRT3':
            color = 'blue'
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
        fig = px.imshow(heatmap_data.pivot_table(index = "Time", columns = "weekday", values = "Value",
                                         aggfunc = "sum"))
        fig.update_xaxes(side="bottom", title = "Day of the Week")
        fig.update_layout(title={'text':f'Hourly Heatmap for {selected_station}'}, title_x=0.5)
    else:
        df = data[data['Line'] == selected_line]
        
        if time_category == "Year":
            time_cat = "Year"
        elif time_category == "Month":
            time_cat = "Month"
        else:
            time_cat = "Year"        
        
        heatmap_data = df[df["Station"] == selected_station]
        fig = px.imshow(heatmap_data.pivot_table(index = time_cat, columns = "Weekday", values = "Value",
                                         aggfunc = "sum"))
        fig.update_xaxes(side="bottom", title = "Day of the Week")
        fig.update_layout(title={'text':f'Heatmap for {selected_station}'}, title_x=0.5)
    return fig
    
    
# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)