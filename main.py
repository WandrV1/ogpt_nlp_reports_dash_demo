import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output, State, dash_table
from scipy import stats

from src.data_location import DataLocator

data_path = 'data/records.xlsx'
warnings_path = 'data/warnings.xlsx'
data_locator = DataLocator(data_path, warnings_path)

available_params = [
    'Забойное давление',
    'Пластовое давление',
    'Скин-фактор',
    'Проницаемость',
    'Фазовая проницаемость',
    'Коэффициент продуктивности/приемистости',
]

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([], md=3),
        dbc.Col(html.H1('Поиск данных'), md=6),
        dbc.Col([], md=3),
    ]),
    dbc.Row([
        dbc.Col([], md=3),
        dbc.Col([
            dbc.FormGroup([
                dbc.Label('Скважина'),
                dbc.Input(id='input-well', placeholder='Название скважины', type='text')
            ])
        ], md=3),
        dbc.Col([
            dbc.FormGroup([
                dbc.Label('Месторождение'),
                dbc.Input(id='input-field', placeholder='Название месторождения', type='text')
            ])
        ], md=3),
        dbc.Col([], md=3)
    ]),
    dbc.Row([
        dbc.Col([], md=3),
        dbc.Col([
            dbc.FormGroup([
                dbc.Label('Параметр'),
                dcc.Dropdown(
                    id='input-param',
                    options=[{'label': param, 'value': param} for param in available_params],
                    placeholder='Параметр'
                )
            ])
        ], md=3),
        dbc.Col([
            dbc.FormGroup([
                dbc.Label('Тип параметра'),
                dcc.Dropdown(
                    id='input-param-type',
                    placeholder='Тип параметра'
                )
            ])
        ], md=3),
        dbc.Col([], md=3)
    ]),
    dbc.Row([
        dbc.Col([], md=5),
        dbc.Col([
            dbc.FormGroup([
                dbc.Label('Период'),
                dcc.DatePickerRange(
                    id='input-date-range',
                    start_date_placeholder_text='Начало исследования',
                    end_date_placeholder_text='Окончание исследования',
                    display_format='DD.MM.YYYY'
                )
            ])
        ], md=4),
        dbc.Col([], md=3)
    ]),
    dbc.Row([
        dbc.Col([], md=3),
        dbc.Col([
            dbc.Button('Поиск', id='search-button', color='primary', n_clicks=0)
        ], width='auto'),
    ], justify='start'),
    dbc.Row([
        dbc.Col([], md=3),
        dbc.Col(
            html.Div(id='output-graph'),
            md=6
        ),
        dbc.Col([], md=3),
    ]),
    dbc.Row([
        dbc.Col([], md=3),
        dbc.Col(
            html.Div(id='output-warning'),
            width=6
        ),
        dbc.Col([], md=3),
    ]),
    dbc.Row([
        dbc.Col([], md=3),
        dbc.Col(
            dash_table.DataTable(
                id='output-table',
                columns=[
                    {'name': 'Файл', 'id': 'Файл'},
                    {'name': 'Начало исследования', 'id': 'Начало_исследования'},
                    {'name': 'Окончание исследования', 'id': 'Окончание_исследования'},
                    {'name': 'Значение', 'id': 'Значение'},
                ],
                style_table={'overflowX': 'auto'},
                page_size=20,
            ),
            md=6
        ),
        dbc.Col([], md=3),
    ]),
], fluid=True)

@app.callback(
Output('input-param-type', 'options'),
    Output('input-param-type', 'value'),
    Output('input-param-type', 'disabled'),
    Input('input-param', 'value')
)
def update_param_type_options(selected_param):
    if selected_param == 'Забойное давление':
        return ['ВДП', 'На глубине замера', 'ВНК', 'На кровлю', 'ГНК'], None, False
    elif selected_param == 'Пластовое давление':
        return ['ВДП', 'На глубине замера', 'ВНК', 'На кровлю', 'ГНК'], None, False
    elif selected_param == 'Скин-фактор':
        return ['Интегральный', 'Механический'], None, False
    elif selected_param == 'Проницаемость':
        return ['По жидкости', 'По нефти'], None, False
    elif selected_param == 'Фазовая проницаемость':
        return ['По жидкости', 'По нефти'], None, False
    elif selected_param == 'Коэффициент продуктивности/приемистости':
        return [], None, True
    else:
        return [], None, True

@app.callback(
    Output('output-graph', 'children'),
    Output('output-warning', 'children'),
    Output('output-table', 'data'),
    Input('search-button', 'n_clicks'),
    State('input-well', 'value'),
    State('input-field', 'value'),
    State('input-param', 'value'),
    State('input-param-type', 'value'),
    State('input-date-range', 'start_date'),
    State('input-date-range', 'end_date')
)
def search_records(n_clicks, well, field, param, param_type, start_date, end_date):
    if not n_clicks:
        return '', '', []

    if well is None or field is None or param is None:
        return dbc.Alert('Необходимо заполнить все обязательные поля: "Скважина", "Месторождение", "Параметр"'), '', []

    start_date = pd.to_datetime(start_date) if start_date is not None else None
    end_date = pd.to_datetime(end_date) if end_date is not None else None
    if param == 'Коэффициент продуктивности/приемистости':
        param = 'Коэффициент продуктивности'
    try:
        records, warnings = data_locator.locate_records(well, field, param, param_type, start_date, end_date)
    except NotImplementedError as e:
        return dbc.Alert(str(e), color='danger'), '', []

    if records.empty:
        return dbc.Alert('Не найдено записей по заданным критериям поиска', color='warning'), '', []

    try:
        records = records.sort_values('Дата').reset_index(drop=True)
        records['Начало_исследования'] = pd.to_datetime(records['Начало_исследования']).dt.strftime('%d.%m.%Y')
        records['Окончание_исследования'] = pd.to_datetime(records['Окончание_исследования']).dt.strftime('%d.%m.%Y')
        table_data = records[['Файл', 'Начало_исследования', 'Окончание_исследования', 'Значение']].to_dict('records')

        param_name = records['Параметр'].unique()[0]
        param_type_val = records['Тип'].unique()[0]
        if pd.isna(param_type_val) or param_type_val is None:
            param_type_val = ''
        records['Дата_ordinal'] = records['Дата'].map(pd.Timestamp.toordinal)

        fig = px.line(
            records, x='Дата', y='Значение',
            title=f'Динамика параметра "{param_name} {param_type_val}"',
            labels={'Значение': 'Значение', 'Дата': 'Дата'}
        )

        slope, intercept, r_value, p_value, std_err = stats.linregress(records['Дата_ordinal'], records['Значение'])
        records['Trend'] = intercept + slope * records['Дата_ordinal']
        annotation_text = (f"Тренд: y = {slope:.4f}x + {intercept:.2f}<br>"
                           f"R² = {r_value ** 2:.4f}<br>"
                           f"p-value = {p_value:.4f}")
        fig.add_traces([go.Scatter(
            x=records['Дата'],
            y=records['Trend'],
            mode='lines',
            name='Линейный тренд',
            line=dict(color='red')
        )])

        fig.add_annotation(
            x=0.05,
            y=0.95,
            xref='paper',
            yref='paper',
            text=annotation_text,
            showarrow=False,
            align='left',
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='black',
            borderwidth=1
        )

        if warnings is not None and not warnings.empty:
            warning_filenames = warnings['Файл'].unique()
            warning_records = records[records['Файл'].isin(warning_filenames)]

            if not warning_records.empty:
                fig.add_traces([go.Scatter(
                    x=warning_records['Дата'],
                    y=warning_records['Значение'],
                    mode='markers',
                    name='Предупреждение',
                    marker=dict(color='orange', size=10, symbol='cross')
                )])

        fig.update_layout(
            xaxis_title='Дата',
            yaxis_title='Значение',
            # legend_title='Легенда',
            hovermode='x unified'
        )

        graph = dcc.Graph(figure=fig)

    except Exception as e:
        return dbc.Alert(f'Ошибка при построении графика: {str(e)}', color='danger'), '', []

    warnings_item = ''
    if warnings is not None and not warnings.empty:
        warnings_items = [f'Найдено предупреждений: {len(warnings)}']
        for _, warning in warnings.iterrows():
            warnings_items.append(f'\n{warning["Файл"]} - {warning["Сообщение"]}')
        warnings_item = dbc.Container([
            dbc.Alert(warning, color='warning') for warning in warnings_items
        ])

    return graph, warnings_item, table_data

if __name__ == "__main__":
    app.run(debug=True)
