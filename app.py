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
        self.decomposed_time_series = {
            "trend": [],
            "seasonal": [],
            "residual": []
        }
        self.stfl_params = {}
        self.forecast_params = {
            "model": None,
            "forecast_method": None,
            "forecast_curve": None,
            "n_preds": None            
        }
    

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
            Output("periodSlider", "min"),
            Output("periodSlider", "max"),
            Output("trendSlider", "min"),
            Output("trendSlider", "max"),
            Output("seasonalSlider", "min"),
            Output("seasonalSlider", "max"),
            Input("frequencyDropdown", "value")
        )(self.update_stfl_params)        
        
        self.app.callback(
            Output("updatedParams", "children"),
            [
                Input("periodSlider", "value"),
                Input("trendSlider", "value"),
                Input("seasonalSlider", "value"),                
            ]
        )(self.update_params)    
        
        self.app.callback(
            Output("updatedDecomposedTimeSeries", "children"),
            [
                Input("selectedItem", "children"),
                Input("updatedParams", "children"),                
            ]            
        )(self.update_decomposed_df)
        
        # Create a Callback to Display STFL Decomposed Chart
        
        self.app.callback(            
            Output("forecastMethodDropdown", "options"),            
            Input("modelDropdown", "value")
        )(self.update_model)
        
        self.app.callback(        
            Input("forecastMethodDropdown", "value"),            
        )(self.update_forecast_method)
                
        self.app.callback(                   
            Input("curveDropdown", "value"),
        )(self.update_forecast_curve)
        
        self.app.callback(            
            Input("predictionsSlider", "value"),
        )(self.update_n_preds)
        
        self.app.callback(
            Output("forecastButton", "disabled"),
            [
                Input("forecastMethodDropdown", "value"),
                Input("curveDropdown", "value"),
                Input("predictionsSlider", "value"),
            ]           
        )(self.check_forecast_button)
        
        self.app.callback(
            Input("forecastButton", "n_clicks"),
        )(self.update_forecast_data)

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
    
    def update_stfl_params(self, frequency):
        print("Update stfl Callback called")
        if frequency == "daily":
            period_min = 2
            period_max = 6
            trend_smooth_min = 3
            trend_smooth_max = 31
            seasonal_smooth_min = 3
            seasonal_smooth_max = 31            
        elif frequency == "weekly":
            period_min = 1
            period_max = 3
            trend_smooth_min = 3
            trend_smooth_max = 5
            seasonal_smooth_min = 3
            seasonal_smooth_max = 5
        
        return (
            period_min,
            period_max,
            trend_smooth_min, 
            trend_smooth_max, 
            seasonal_smooth_min, 
            seasonal_smooth_max
        )
                                                                
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
        
    def update_params(self, period, trend_smooth, seasonal_smooth):
        self.stfl_params = {
            "period": period,
            "trend_smooth": trend_smooth,
            "seasonal_smooth": seasonal_smooth,            
        }
        return "Params updated"
    
    def update_decomposed_df(self, selected_item, updated_params):
        print(f"Decomposition Callback called")        
        print(f"Params are: {self.stfl_params}")
        request_url = url_for('api.get_decomposed_data', _external=True)
        data = {
            "time_series": self.time_series,
            "params": self.stfl_params
        }        
        response = requests.post(
            request_url,
            data = json.dumps(data),
            headers = {"Content-Type": "application/json"}            
        )
        
        if response.status_code == 200:
            self.decomposed_time_series = response.json()
        
        return f"Updated decomposed time series"
    
    # def function to graph the decomposed time series
    
    def update_model(self, model_selected):        
        if model_selected == "ets":            
            options={
                "sse": "Simple Exponential",
                "trend_add": "Trend Additive",
                "seasonal_add": "Seasonal Additive",
                "trend_seasonal_add": "Trend and Seassonal Additive"
            }                    
        
        elif model_selected == "arima":
            options={
                "arima_exp": "Arima Exp",                
                "arima_seasonal": "Arima Seasonal",                
            }        
        else:
            return {}
        
        self.forecast_params["model"] = model_selected
        return options
    
    
    def update_forecast_method(self, forecast_method):
        if forecast_method: 
            self.forecast_params["forecast_method"] = forecast_method        
    
    def update_forecast_curve(self, forecast_curve):
        if forecast_curve: 
            self.forecast_params["forecast_curve"] = forecast_curve        
    
    def update_n_preds(self, n_preds):
        if n_preds: 
            self.forecast_params["n_preds"] = n_preds        
    
    def check_forecast_button(self, forecast_method, forecast_curve, n_preds):
        for param_value in self.forecast_params.values():
            if not param_value:
                return True
        return False
    
    def update_forecast_data(self, n_clicks):
        if n_clicks > 0:
            request_url = url_for('api.get_forecast_data', _external=True)
            headers = {"Content-Type": "application/json"}
            curve = self.forecast_params["forecast_curve"]
            if curve == "trend":
                curve_data = self.decomposed_time_series["trend"]
            elif curve == "seasonal_adjusted":
                curve_data = self.decomposed_time_series["trend"] 
                + self.decomposed_time_series["residual"]
            else:
                curve_data = self.decomposed_time_series["trend"] 
                + self.decomposed_time_series["seasonal"] 
                + self.decomposed_time_series["residual"]
            
            payload = {"curve": curve_data} | self.forecast_params
            
            response = requests.post(
                request_url,
                data = json.dumps(payload),
                headers = headers                
            )
            
            if response.status_code == 200:
                self.forecast_data = response.json()
                
            else:
                raise Exception("Failed to get forecast data")
    
    # Define the run method
    def run(self):
        self.flask_server.run(debug=True)
    

if __name__ == '__main__':
    app = FlaskDashApp()
    app.run()