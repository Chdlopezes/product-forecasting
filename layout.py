from dash import html, dcc

forecast_layout = html.Div([
    html.Div(
        [        
            html.Div(
                [
                    html.Label("Decomposition Method"),
                    dcc.Dropdown(
                        id="decompositionDropdown",        
                        options={
                            "trend": "Trend",
                            "seasonal_adjusted": "Seasonal Adjusted",
                            "normal": "Normal"
                        },
                        value="trend"
                    ),
                    html.Div(id="selectedDecomposition", style={"display": "none"})
                ],
                className="dropdown-container",        
            ),
            html.Div(id="chartDataUpdated", style={"display": "none"}),
            html.Div(
                [
                    html.Label("Model"),
                    dcc.Dropdown(
                        id="modelDropdown",        
                        options={
                            "ets": "Exponential Smoothing",
                            "arima": "ARIMA",                        
                        },
                        value="ets"
                    )
                ],
                className="dropdown-container",        
            ),       
            html.Div(
                [
                    html.Label("Forecast Method"),
                    dcc.Dropdown(
                        id="forecastDropdown",        
                        options={
                            "sse": "Simple Exponential",
                            "trend_add": "Trend Additive",
                            "seasonal_add": "Seasonal Additive",
                            "trend_seasonal_add": "Trend and Seassonal Additive"
                        },
                        value="sse"
                    )
                ],
                className="dropdown-container",        
            ),                 
        ],
        className="header-container"    
    ),
    html.Div([                
        html.Div([
            html.Div([
                html.Label("Select Item"),
                dcc.Dropdown(
                    id="itemsDropdown",
                    options={
                        "gid://Gizmo/Item/1": "Item 1",
                        "gid://Gizmo/Item/2": "Item 2",
                        "gid://Gizmo/Item/3": "Item 3",
                    },
                    value="gid://Gizmo/Item/1" 
                ),            
                html.Div(id="selectedItem", style={"display": "none"})                    
            ], className="dropdown-container"),     
            html.Div([
                html.Label("Data Frequency"),
                dcc.Dropdown(
                    id="frequencyDropdown",
                    options={
                        "daily": "Diaria",
                        "weekly": "Semanal",
                    },
                    value="daily"
                )                            
            ], className="dropdown-container"),            
        ],className="chart-header"),                                
        html.Div(id="updatedParams", style={"display": "none"}),
        html.Div([
            dcc.Graph(
                id="chart", 
                className="figure-container",
                figure={}
            ),         
            html.Div([                
                html.Label("Period"),
                dcc.Slider(
                    id="periodSlider",
                    min=1,
                    max=10,
                    step=1,
                ),
                html.Label("Trend Smooth"),
                dcc.Slider(
                    id="trendSlider",
                    min=0,
                    max=10,
                    step=1,
                ),
                html.Label("Seasonal Smooth"),
                dcc.Slider(
                    id="seasonalSlider",
                    min=0,
                    max=10,                    
                ),                                
                dcc.Checklist(
                    id="addSeasonalCheck",
                    options={"true": "Add Seasonal Fluctuation"},
                    value=[],
                )
            ], className="graph-options-container"),
        ], className="graph-container"),  
        
        html.Div([
            html.Div([
                html.Label("Num Predictions"),
                dcc.Slider(
                    id="predictionsSlider",
                    min=1,
                    max=10,
                    step=1,
                    value=1
                )                            
            ], className="dropdown-container"),            
        ], className="footer-container"),

    ], className="chart-container"),
    
    html.Div(children=[], id="messageDiv" )        
], className="main-container") 