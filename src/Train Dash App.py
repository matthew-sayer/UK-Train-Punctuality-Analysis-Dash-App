import pandas as pd
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.io as pio
import plotly.graph_objects as go

def readCsv(inputfile):
    df = pd.read_csv(inputfile)
    print(df.columns)
    print(df.dtypes)
    return df

df = readCsv('C:\\Users\\matth\\Downloads\\train-punctuality.csv')

def cleanData(df):
    df['Year'] = df['Time period'].str.extract(r'(\d{4})') #extract the year (any number with 4 digits basically here)
    df = df.dropna(subset=['Year']) #drop any NaN values from Year
    df['Year'] = df['Year'].astype(int) #convert year to integer
    # Set our percentages to a number
    df['Trains arriving within 3 minutes (percentage)'] = pd.to_numeric(df['Trains arriving within 3 minutes (percentage)'], errors='coerce') #convert the percentage to a number
    df['Trains arriving within 15 minutes (percentage)'] = pd.to_numeric(df['Trains arriving within 15 minutes (percentage)'], errors='coerce') #convert the percentage to a number
    df['Trains arriving within 59 seconds (percentage)'] = pd.to_numeric(df['Trains arriving within 59 seconds (percentage)'], errors='coerce') #convert the percentage to a number

    return df

def groupData(df):
    # Here i'm grouping the operator by the year, so I can get the average % of trains arriving within 3 minutes
    print(type(df))
    df = df[~df['National or Operator'].str.contains('Great Britain|England and Wales|Scotland|Hull Trains [note 2]|Hull Trains|Elizabeth line [note 4]|Lumo|Grand Central|Elizabeth line', na=False)]
    within3Minutes = df.groupby(['National or Operator', 'Year'])['Trains arriving within 3 minutes (percentage)'].mean().reset_index()
    within15Minutes = df.groupby(['National or Operator', 'Year'])['Trains arriving within 15 minutes (percentage)'].mean().reset_index()
    within59seconds = df.groupby(['National or Operator', 'Year'])['Trains arriving within 59 seconds (percentage)'].mean().reset_index()
    return within3Minutes, within15Minutes, within59seconds

#def main(inputfile):
   # df = readCsv(inputfile)
    #df = cleanData(df)
    #df = groupData(df)

df = cleanData(df)
within3Minutes, within15Minutes, within59seconds = groupData(df)

app = dash.Dash(__name__) #create the dash app

#now we will define the layout of the app for our screen
app.layout = html.Div(style={'backgroundColor': '#111111', 'color': 'white','font-family': 'Courier New, monospace','height':'100vh'}, children=[ # this is our main header
    html.Div([ #this is our first div, which will contain the dropdown
        dcc.Dropdown(
            id='dropdown',
            options=[ # now define our options for our dropdown
                {'label': 'Trains arriving within 59 seconds', 'value': '59'},
                {'label': 'Trains arriving within 3 minutes', 'value': '3'},
                {'label': 'Trains arriving within 15 minutes', 'value': '15'},
            ],
            value='3',
            style={'backgroundColor': 'white', 'color': 'black', 'family': 'Courier New, monospace'}
        )   
    ]), #closes the first div
    html.Div(
        id='graph-container', children=[ # this is the id of the div that will contain our graph
        dcc.Graph(id='graph') # this holds our graph
        ], style={'width': '80%', 'display':'inline-block', 'backgroundColor': '#111111'} # this is the style of our graph
    ),
    html.Div(id='summariser',
    style={'backgroundColor': '#111111', 'color': 'white','font-family': 'Courier New, monospace','height':'100vh'},
     children=[ # this is the id of the div that will contain our graph
        html.H3('Best and Worst Performers'),
        html.P(id='best-performer'),
        html.P(id='worst-performer'),
        html.P(id='average-performance'),
        html.P(id='median-performance')
        ])
]) #closes the main div
 # this is our dropdown to choose our graph to show

#Now we need a function to update our dcc graph based on what i choose on the dropdown

@app.callback( # this is the start of our callback function
Output('graph', 'figure'), # this is what we wnat to output, basically the graph and the figure because we want to show a graph
Output('best-performer', 'children'),
Output('worst-performer', 'children'),
Output('average-performance', 'children'),
Output('median-performance', 'children'),
#the figure is there because that is the container for the graph
[Input('dropdown', 'value')] # this is the input, which is the dropdown
)

#now we need to define our function that will update the graph based on the dropdown
def update_graph(input_value):
    if input_value == '59':
        data = within59seconds
        name = 'Trains arriving within 59 seconds'
        x = within59seconds['Year']
        y = 'Trains arriving within 59 seconds (percentage)'
    elif input_value == '15':
        data = within15Minutes
        name = 'Trains arriving within 15 minutes'
        x = within15Minutes['Year']
        y = 'Trains arriving within 15 minutes (percentage)'
    elif input_value == '3':
        data = within3Minutes
        name = 'Trains arriving within 3 minutes'
        x = within3Minutes['Year']
        y = 'Trains arriving within 3 minutes (percentage)'

    average_performance = data.groupby('National or Operator')[y].mean()
    best_performer_average = average_performance.idxmax()
    worst_performer_average = average_performance.idxmin()

    mean_performance = average_performance.mean()
    median_performance = average_performance.median()
    best_performer = average_performance.max()
    worst_performer = average_performance.min()

    sorted_operators = average_performance.sort_values(ascending=False).index

    traces = [] #this is a list of all the traces we want to show on our graph
    for operator in sorted_operators: #this is looping through all the operators in the data
        df_by_operator = data[data['National or Operator'] == operator] #this is creating a new dataframe for each operator
        traces.append(go.Scatter( #this is creating a scatter plot for each operator
            x=df_by_operator['Year'],
            y=df_by_operator[y],
            text=operator,
            mode='lines',
            name=operator

        ))
    
    figure = go.Figure( #our graph
        data= traces, # this is building out all the graph options we want to show
        layout= go.Layout(
            title= 'How many trains are on time in the UK?',
            plot_bgcolor= 'rgba(0,0,0,0)',
            paper_bgcolor= 'rgba(0,0,0,0)',
            height= 800,
            showlegend=True,            
            #style the font
            font=dict(color='white', family='Courier New, monospace'),
            legend=dict(traceorder="normal")
        )
    )
    return figure, f'Best Performer: {best_performer_average} at {best_performer:.1f}%', f'Worst Performer: {worst_performer_average} at {worst_performer:.1f}%', f'Average Performance: {mean_performance:.1f}%', f'Median Performance: {median_performance:.1f}%' #this is returning our graph 

#now we create a function to run the server itself
if __name__ == '__main__':
    app.run_server(debug=True)

