import numpy as np
import pandas as pd
import plotly.express as px
import unidecode
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from support.formula_one import FormulaOne


#####
# Loading data
#####
f1 = FormulaOne()
# f1.update()

fantasy_rosters = pd.read_csv('./draft/fantasy_rosters.csv', index_col=0)
TEAM_NAMES_LST = [
    '3 Orange Whips',
    'Deep Fried',
    'Scuderia Spaghetti',
    'Carlaniel & the Romeos'
]

leaderboard = (
    f1.results[f1.results['RaceID'] > 202100]
    .merge(fantasy_rosters, on='DriverID')
    .groupby('Team').sum()[['Points']]
    .sort_values('Points', ascending=False)
    .reset_index()
)
pts_per_round = (
    f1.results.loc[f1.results['RaceID'] > 202100]
    .merge(fantasy_rosters[['Team', 'DriverID']], 
           on='DriverID')
    .merge(f1.races[['RaceID', 'Round']])
    .sort_values(['RaceID', 'Position'])
    .loc[:, ['Points', 'Team', 'Round']]
    .groupby(['Round', 'Team']).sum()
    .reset_index()
)
cumulative_points = (
    pts_per_round
    .groupby(['Team', 'Round']).sum()
    .groupby('Team').cumsum()
    .reset_index()
)

### Adjustable.
# TEAM_NAME = 'Deep Fried'
# team_results = (f1.results.loc[f1.results['RaceID'] > 202100]
#  .merge(fantasy_rosters
#         .loc[fantasy_rosters['Team'] == TEAM_NAME][['Team', 'DriverID']], 
#         on='DriverID')
#  .merge(f1.races[['RaceID', 'Round']],
#         on='RaceID')
#  .merge(f1.drivers[['DriverID', 'Code']], on='DriverID')
# )

#####
# App Components
#####
TABLEAU_DASHBOARD = 'https://public.tableau.com/app/profile/stephen.helms/viz/Progresstowardthe2021Formula1DriversChampionship/2021Results'
GOOGLE_DRIVE = 'https://docs.google.com/spreadsheets/d/15-2tdikz61PpbfsLgq9f9d4sTZW6DN1odPC8if-ksOk/edit#gid=415894594'

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "14rem",
    "padding": "2rem 1rem",
}
CONTENT_STYLE = {
    "margin-left": "14rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}
SIDEBAR = html.Div([
        dbc.Row(html.H2("Navigation"), justify='center'),
        html.Hr(),
        dbc.Row(
            dbc.Nav([
                dbc.NavLink("F1antasy League", href="/", active="exact"),
                dbc.DropdownMenu(
                    [dbc.NavLink(team, href=f'/{"-".join(team.split())}', active="exact")
                    for team in TEAM_NAMES_LST],
                    label='Teams'
                    ),
                dbc.NavLink('EXPERIMENTAL', href='experimental', active='exact')
                ],
            vertical=True,
            # pills=True,
            ),
            justify='center'),
        html.Hr(),
        dbc.Row(
            html.A(
                'Driver Dashboard - Tableau', 
                href=TABLEAU_DASHBOARD,
                target='_blank'),
            justify='center'
            ),
        dbc.Row(
            html.A(
                'League - Google Sheets',
                href=GOOGLE_DRIVE,
                target='_blank'
                ),
            justify='center'
            ),
    ],
    style=SIDEBAR_STYLE,
)

###
# League
###
HEADING_DIV = html.Div(id='heading', children=[
	dbc.Row(
		dbc.Col(
			html.H1('F1antasy League'), 
			width='auto'), 
		justify='center'
		),
	dbc.Row(
		dbc.Col(
			html.H3('Formula One for Formula-Friends Family'),
			width='auto'),
		justify='center'),
    ]
    )

LEADERBOARD = html.Div(id='leaderboard', children=[
    dbc.Row(
        dbc.Col([
            dbc.Row(html.H3('Leaderboard'), justify='center'),
            dbc.Table.from_dataframe(
                leaderboard, 
                striped=True, 
                bordered=True, 
                hover=True,
                size='sm'),
            ],
            width=4
            ),
        justify='center',
    ),
])

CHART_WIDTH = 8
LEAGUE_LINE = (
    px.line(
        x='Round', y='Points', color='Team',
        data_frame=cumulative_points, 
        title='Cumulative Points - 2021 Season',
        )
    .update_traces(mode='lines+markers')
    .update_layout(paper_bgcolor='rgba(0,0,0,0)', autosize=True)
)
LEAGUE_BAR = (
    px.bar(
        x='Round', y='Points', color='Team', 
        data_frame=pts_per_round,
        title='Points by Round',
        )
    .update_layout(paper_bgcolor='rgba(0,0,0,0)', autosize=True)
)
LEAGUE = html.Div(id='league', children=[
    dbc.Row(
        dbc.Col(
            dcc.Graph(id='league_line', figure=LEAGUE_LINE),
            width=CHART_WIDTH
            ),
        justify='center'
    ),
    dbc.Row(
        dbc.Col(
            dcc.Graph(id='league_bar', figure=LEAGUE_BAR),
            width=CHART_WIDTH
        ),
        justify='center'
    ),
    ]
)
###
# Experimental
###
EXP_leaderboard = (
    f1.results[f1.results['RaceID'] > 202100]
    .merge(fantasy_rosters, on='DriverID')
    .drop_duplicates()
    .groupby('Team').sum()[['Position']]
    .sort_values('Position', ascending=True)
    .reset_index()
)
EXP_pts_per_round = (
    f1.results.loc[f1.results['RaceID'] > 202100]
    .merge(fantasy_rosters[['Team', 'DriverID']], 
           on='DriverID')
    .merge(f1.races[['RaceID', 'Round']])
    .sort_values(['RaceID', 'Position'])
    .loc[:, ['Position', 'Team', 'Round']]
    .groupby(['Round', 'Team']).sum()
    .reset_index()
)
EXP_cumulative_points = (
    EXP_pts_per_round
    .groupby(['Team', 'Round']).sum()
    .groupby('Team').cumsum()
    .reset_index()
)
EXP_cumulative_points['Position'] = -EXP_cumulative_points['Position']
for round_num in EXP_cumulative_points['Round'].unique():
    rnd_df = EXP_cumulative_points[EXP_cumulative_points['Round'] == round_num]['Position'].values
    n = rnd_df.max()
    EXP_cumulative_points.loc[EXP_cumulative_points['Round'] == round_num, 'PositionDifference'] = (rnd_df - n)

EXP_LEADERBOARD = html.Div(id='exp-leaderboard', children=[
    dbc.Row(
        dbc.Col([
            dbc.Row(html.H3('Experimental Leaderboard'), justify='center'),
            dbc.Row(
                html.P('The points system in this experimental section is golf-like where the lowest score is best. Points are awarded by finishing position (1-20) for each driver (1 being best, 20 being worst).'), 
                justify='center'),
            dbc.Table.from_dataframe(
                EXP_leaderboard, 
                striped=True, 
                bordered=True, 
                hover=True,
                size='sm'),
            ],
            width=4
            ),
        justify='center',
    ),
])

EXP_LEAGUE_LINE = (
    px.line(
        x='Round', y='PositionDifference', color='Team',
        data_frame=EXP_cumulative_points, 
        title='Experimental - Total Position Difference - 2021 Season',
        )
    .update_traces(mode='lines+markers')
    .update_layout(paper_bgcolor='rgba(0,0,0,0)', autosize=True)
)
EXP_LEAGUE_BAR = (
    px.bar(
        x='Round', y='Position', color='Team', 
        data_frame=EXP_pts_per_round,
        title='Experimental - Total Position by Round',
        )
    .update_layout(paper_bgcolor='rgba(0,0,0,0)', autosize=True)
)
EXP_DRIVER_POSITION = px.bar(
    data_frame=(
        f1.results[f1.results['RaceID'] > 202100]
        .merge(fantasy_rosters[['DriverID', 'LastName', 'Team']], on='DriverID')
        [['Position', 'LastName', 'Team']]
        .groupby(['LastName', 'Team']).sum()
        .reset_index()
        .sort_values('Position', ascending=False)
    ),
    x='Position',
    y='LastName',
    title='Driver Performance',
    height=500
).update_layout(paper_bgcolor='rgba(0,0,0,0)', autosize=True)

EXP_DRIVER_POSITION_BYTEAM = px.bar(
    data_frame=(
        f1.results[f1.results['RaceID'] > 202100]
        .merge(fantasy_rosters[['DriverID', 'LastName', 'Team']], on='DriverID')
        [['Position', 'LastName', 'Team']]
        .groupby(['LastName', 'Team']).sum()
        .reset_index()
        .sort_values('Position', ascending=False)
    ),
    x='Position',
    y='LastName',
    color='Team',
    title='Driver Performance by Team',
    height=500
).update_layout(paper_bgcolor='rgba(0,0,0,0)', autosize=True)

EXP_LEAGUE = html.Div(id='exp-league', children=[
    dbc.Row(
        dbc.Col(
            dcc.Graph(id='exp_driver_standings', figure=EXP_DRIVER_POSITION),
            width=CHART_WIDTH
        ),
        justify='center'
    ),
    dbc.Row(
        dbc.Col(
            dcc.Graph(id='exp_driver_standings_byteam', figure=EXP_DRIVER_POSITION_BYTEAM),
            width=CHART_WIDTH
        ),
        justify='center'
    ),
    dbc.Row(
        dbc.Col(
            dcc.Graph(id='exp_league_line', figure=EXP_LEAGUE_LINE),
            width=CHART_WIDTH
            ),
        justify='center'
    ),
    dbc.Row(
        dbc.Col(
            dcc.Graph(id='exp_league_bar', figure=EXP_LEAGUE_BAR),
            width=CHART_WIDTH
        ),
        justify='center'
    ),
    ]
)

###
# Team
###
# TEAM_DROPDOWN = dbc.Row(
#     dbc.Col(
#         dcc.Dropdown(
#             id='dropdown',
#             options=[dict(label=team, value=team) for team in TEAM_NAMES_LST],
#             value=None,
#             placeholder='Select a Team'
#         ),
#         width=3
#     )
# )

#####
# App
#####
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.PULSE])
app.title = 'Formula One - Fantasy League'
server = app.server

app.layout = html.Div(
	id='overall_container', 
	children=[
        SIDEBAR,

        html.Div(
            id='main_div',
            children=[
                dcc.Location(id='url'),
                HEADING_DIV,
                html.Hr(),
                html.Div(id='content-div')
                ],
            style=CONTENT_STYLE)
        ],
	style={'width': '90%', 'margin': 'auto', 'padding': '30px'}
)

#####
# Callbacks
#####
def make_team_div(team_name):
    """Return a list of children elements for the content-div."""

    team_results = (
        f1.results.loc[f1.results['RaceID'] > 202100]
        .merge(fantasy_rosters
            .loc[fantasy_rosters['Team'] == team_name][['Team', 'DriverID']], 
            on='DriverID')
        .merge(f1.races[['RaceID', 'Round']],
            on='RaceID')
        .merge(f1.drivers[['DriverID', 'Code']], 
            on='DriverID')
    )

    POINTS_PER_DRIVER = (
        px.bar(
            x='Round', y='Points', color='Code', 
            data_frame=team_results, 
            title=f'{team_name} - Points by Driver'
            )
        .update_layout(paper_bgcolor='rgba(0,0,0,0)', autosize=True)
    )

    TEAM_DRIVERS_TOTALS = (
        px.line(x='Round', y='Points', color='Code', 
        data_frame=(team_results
                    .groupby(['Code', 'Round']).sum()
                    .groupby('Code').cumsum()
                    .reset_index()
                    ), 
        title=f'{team_name} - Cumulative Driver Points')
        .update_layout(paper_bgcolor='rgba(0,0,0,0)', autosize=True)
    )

    TEAM_ROSTER = (
        fantasy_rosters.loc[fantasy_rosters['Team'] == team_name]
        .drop(columns=['LastName', 'FirstName', 'Nationality', 'Team'])
        .merge(f1.drivers, on='DriverID')
        .drop('DriverID', axis=1)
        .loc[:, ['LastName', 'FirstName', 'Code', 
                'TeamPick', 'OverallPick', 'Car',
                'Nationality', 'DOB', 'URL']]
    )

    div_lst = [
        dbc.Row(dbc.Col(html.H3(team_name), width='auto'), justify='center'),
        dbc.Row(html.H5('Roster'), justify='center'),
        dbc.Row(
            dbc.Table.from_dataframe(
                TEAM_ROSTER, 
                striped=True, 
                bordered=True, 
                hover=True,
                size='sm'),
            justify='center'
        ),
        html.Br(),
        dbc.Row(
            dcc.Graph(
                id='points_per_driver', 
                figure=POINTS_PER_DRIVER
                ),
            justify='center'
            ),
        html.Br(),
        dbc.Row(
            dcc.Graph(
                id='team_driver_standings',
                figure=TEAM_DRIVERS_TOTALS
                ),
            justify='center'
        )
    ]
    return div_lst


@app.callback(Output('content-div', 'children'), Input('url', 'pathname'))
def render_page_content(pathname):
    """Return the page Div for each team and the league."""

    team_name = pathname[1:].replace('-', ' ')
    if not team_name:
        return [
            LEADERBOARD,
            html.Br(),
            LEAGUE,
            ]
    elif team_name == 'experimental':
        return [
            EXP_LEADERBOARD,
            html.Br(),
            EXP_LEAGUE
        ]
    return make_team_div(team_name)

#####
# Run
#####
if __name__ == '__main__':
	# app.run_server(debug=True)
    app.run_server()
