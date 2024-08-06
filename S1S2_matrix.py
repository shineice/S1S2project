import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import base64
import io

# 初始化Dash應用
app = dash.Dash(__name__)

# 示例數據
data = {
    '風險': [f'Risk {i+1}' for i in range(18)],
    '對於企業ESG面的衝擊': ['中高', '低', '中高', '中', '低', '低', '低', '低', '低', '中', '低', '中', '中', '中', '中', '中', '低', '低'],
    '對於企業財務面衝擊': ['中高', '低', '中高', '中', '低', '低', '低', '低', '低', '中', '低', '中', '中', '中', '中', '中', '低', '低']
}

df = pd.DataFrame(data)

# 對於企業財務面衝擊和對於企業ESG面的衝擊的映射
impact_mapping = {'低': 1, '中': 2, '中高': 3, '高': 4}
financial_mapping = {'低': 1, '中': 2, '中高': 3, '高': 4}

df['對於企業ESG面的衝擊數值'] = df['對於企業ESG面的衝擊'].map(impact_mapping)
df['對於企業財務面衝擊'] = df['對於企業財務面衝擊'].map(financial_mapping)

# 初始化Dash應用
app = dash.Dash(__name__)

# 初始數據
initial_data = {
    '風險': [f'Risk {i+1}' for i in range(5)],
    '對於企業ESG面的衝擊': ['中', '低', '中高', '中', '低'],
    '對於企業財務面衝擊': ['中', '低', '中高', '中', '低']
}

df = pd.DataFrame(initial_data)

# 可能性和影響強度的映射
impact_mapping = {'低': 1, '中': 2, '中高': 3, '高': 4}
financial_mapping = {'低': 1, '中': 2, '中高': 3, '高': 4}

# 創建Dash應用佈局
app.layout = html.Div([
    html.H1("S1S2矩陣圖"),
    dcc.Upload(
        id='upload-data',
        children=html.Div(['拖放或 ', html.A('選擇文件')]),
        style={
            'width': '100%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
            'textAlign': 'center', 'margin': '10px'
        },
        multiple=False
    ),
    html.Div(id='output-data-upload'),
    dcc.Graph(id='risk-matrix'),
    html.Div(id='dropdown-container')
])

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return html.Div(['不支持此文件類型。'])
        return df
    except Exception as e:
        print(e)
        return html.Div(['處理此文件時出錯。'])

@app.callback(
    Output('output-data-upload', 'children'),
    Output('dropdown-container', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_output(contents, filename):
    if contents is None:
        return dash_table.DataTable(data=df.to_dict('records'), page_size=10), create_dropdowns(df)
    
    df = parse_contents(contents, filename)
    if isinstance(df, pd.DataFrame):
        return dash_table.DataTable(data=df.to_dict('records'), page_size=10), create_dropdowns(df)
    else:
        return df, []

def create_dropdowns(df):
    return [html.Div([
        html.Label(f'{risk} 對於企業ESG面的衝擊:'),
        dcc.Dropdown(
            id={'type': 'impact-dropdown', 'index': i},
            options=[{'label': k, 'value': v} for k, v in impact_mapping.items()],
            value=impact_mapping.get(df.at[i, '對於企業ESG面的衝擊'], 1)
        ),
        html.Label(f'{risk} 對於企業財務面衝擊:'),
        dcc.Dropdown(
            id={'type': 'financial-dropdown', 'index': i},
            options=[{'label': k, 'value': v} for k, v in financial_mapping.items()],
            value=financial_mapping.get(df.at[i, '對於企業財務面衝擊'], 1)
        )
    ]) for i, risk in enumerate(df['風險'])]

@app.callback(
    Output('risk-matrix', 'figure'),
    [Input({'type': 'impact-dropdown', 'index': dash.dependencies.ALL}, 'value'),
     Input({'type': 'financial-dropdown', 'index': dash.dependencies.ALL}, 'value')]
)
def update_risk_matrix(*args):
    impact_values, financial_values = args

    # 創建背景熱圖數據
    x = np.array([1, 2, 3, 4, 5])
    y = np.array([1, 2, 3, 4])
    z = np.array([
        [1, 2, 3, 4, 5],
        [2, 4, 6, 8, 10],
        [3, 6, 9, 12, 15],
        [4, 8, 12, 16, 20]
    ])

    # 背景熱圖
    heatmap = go.Heatmap(
        x=x, y=y, z=z,
        colorscale=[
            [0, 'rgb(255,255,224)'], [0.25, 'rgb(255,255,0)'],
            [0.5, 'rgb(255,165,0)'], [0.75, 'rgb(255,69,0)'],
            [1, 'rgb(255,0,0)']
        ],
        showscale=False
    )

    # 風險點
    scatter = go.Scatter(
        x=financial_values,
        y=impact_values,
        mode='markers+text',
        text=df['風險'],
        textposition='top center',
        marker=dict(size=10, color='rgba(0,0,0,0.8)'),
    )

    layout = go.Layout(
        xaxis=dict(
            tickmode='array', tickvals=list(financial_mapping.values()),
            ticktext=list(financial_mapping.keys()), title='對於企業財務面衝擊'
        ),
        yaxis=dict(
            tickmode='array', tickvals=list(impact_mapping.values()),
            ticktext=list(impact_mapping.keys()), title='對於企業ESG面的衝擊'
        ),
        title='S1S2矩陣圖'
    )

    return {'data': [heatmap, scatter], 'layout': layout}

if __name__ == '__main__':
    app.run_server(debug=True)