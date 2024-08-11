from flask import Flask, request, url_for
from dash import Dash, Input, Output
from api.flask_api import APIBlueprint
from layout import forecast_layout
import json
import requests

api_blueprint = APIBlueprint()

class FlaskDashApp():
    def __init__(self):
        # Intialize Flask server
        self.flask_server = Flask(__name__)
        self.flask_server.register_blueprint(api_blueprint.api_bp, url_prefix="/api")  
        # Assign routes for flask server
        self.setup_routes()
        # Intialize Dash app
        self.app = Dash(__name__, server=self.flask_server, url_base_pathname="/dash/")
        self.app.layout = forecast_layout          
        self.setup_dash_callbacks()  
        # Define the general variables
        self.time_series = []
        self.decomposed_time_series = []
        self.ets_params = {}
    
        
    def setup_routes(self):        
        @self.flask_server.route("/test", methods=["GET"])
        def index():
            return "Welcome to test", 200
                
        
    def setup_dash_callbacks(self):
        # Define the callbacks    
        self.app.callback(
            Output("itemsDropdown", "options"),
            Input("selectBrandDropdown", "value")
        )(self.update_brand)
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
                

    def initialize_request(self):
        self.base_url = request.host_url    
        
    def update_brand(self, brand):
        request_url = url_for('api.get_brand_items', _external=True)
        response = requests.get(
            request_url, 
            params={
                "brand": brand
            }
        )
        if response.status_code == 200:
            api_blueprint.set_sentinel(brand=brand)
            return response.json()
    
    def update_time_series(self, item, frequency):
        # make a request to the API which retreives the sales dupdatedParamsata for given item and frequency        
        request_url = url_for('api.get_data', _external=True)
        # Get the time series provided item
        response = requests.get(
            request_url, 
            params={
                "item_gid": item, 
                "frequency": frequency
            }
        )
        self.time_series = response.json()        
        print("Internal Time series updated")
        return f"Internal Time series updated"
        
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
        request_url = url_for('api.get_decomposed_data', _external=True)
        data = {
            "time_series": self.time_series,
            "params": self.ets_params
        }        
        response = requests.post(
            request_url,
            data = json.dumps(data),
            headers = {"Content-Type": "application/json"}            
        )
        
        if response.status_code == 200:
            self.decomposed_time_series = response.json()
        
        return f"Updated decomposed time series"
    
    
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