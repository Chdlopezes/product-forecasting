from flask import Flask
from dash import Dash, html, dcc, Input, Output
from api.flask_api import api_bp
from layout import forecast_layout
import pandas as pd


class FlaskDashApp():
    def __init__(self):
        # Intialize Flask server
        self.flask_server = Flask(__name__)
        self.flask_server.register_blueprint(api_bp)
        # Intializer Dash app
        self.app = Dash(__name__, server=self.flask_server, url_base_pathname="/dash/")
        self.app.layout = forecast_layout
        # Define the general variables
        self.time_series = pd.DataFrame()
        self.decomposed_df = pd.DataFrame()       
        self.ets_params = {}         
        # Define the callbacks    
        self.app.callback(
            Output("selectedItem", "children"),
            [
                Input("itemsDropdown", "value"),
                Input("frequencyDropdown", "value"),
            ]            
        )(self.update_time_series)
        self.app.callback(
            Output("updatedParams", "children"),
            [
                Input("periodSlider", "value"),
                Input("trendSlider", "value"),
                Input("seasonalSlider", "value"),
                Input("addSeasonalCheck", "value"),
            ]
        )(self.update_params)    
        self.app.callback(
            Output("selectedDecomposition", "children"),
            [
                Input("selectedItem", "children"),
                Input("updatedParams", "children"),
                Input("decompositionDropdown", "value"),                
            ]            
        )(self.update_decomposed_df)
        self.app.callback(
            Output("chartDataUpdated", "children"),
            [
                Input("selectedDecomposition", "children"),
                Input("modelDropdown", "value"),
                Input("forecastDropdown", "value"),
                Input("predictionsSlider", "value")
            ]
        )(self.update_forecast_df)

    
    def update_time_series(self, item, frequency):
        # make a request to the API which retreives the sales dupdatedParamsata for given item and frequency
        # create a fictitious time series
        self.time_series = pd.DataFrame({"ds": pd.date_range("2022-01-01", periods=10), "y": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
        print("Time Series Callback called")
        return f"Item selected is {item} and frequency is {frequency}"
        
    def update_params(self, period, trend_smooth, seasonal_smooth, add_seasonal):
        self.ets_params = {
            "period": period,
            "trend_smooth": trend_smooth,
            "seasonal_smooth": seasonal_smooth,
            "add_seasonal": add_seasonal
        }
        return "Params updated"
    
    def update_decomposed_df(self, selected_item, updated_params, decomposition_method):
        print(f"Decomposition Callback called")
        print(f"Decomposition Method is {decomposition_method}")
        print(f"Params are: {self.ets_params}")
        return f"Decomposition method is {decomposition_method}"
    
    
    def update_forecast_df(self, selected_decomposition, model, forecast_method, n_predictions):
        print("Forecast Callback called")
        print(f"model selected is: {model}")
        print(f"forecast method is: {forecast_method}")
        print(f"n_predictions is: {n_predictions}")
        
        return "Update chart"
    
    # Define the run method
    def run(self):
        self.flask_server.run(debug=True)
    

if __name__ == '__main__':
    app = FlaskDashApp()
    app.run()