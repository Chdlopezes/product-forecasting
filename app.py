import os
from datetime import datetime, timedelta
from flask import Flask, request, url_for
from dash import Dash, Input, Output, State
from api.flask_api import APIBlueprint 
from layout import forecast_layout
import json
import requests
import plotly.graph_objects as go
import pandas as pd 

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
        self.selected_brand = "Uhtil"
        self.items_dict = {}
        self.selected_item_gid = None
        self.selected_item_name = None
        self.time_series = []
        self.frequency = None
        self.decomposed_time_series = {
            "trend": {},
            "seasonal": {},
            "residual": {}
        }
        self.stfl_params = {}
        self.forecast_params = {
            "model": None,
            "forecast_method": None,
            "forecast_curve": None,
            "n_preds": None            
        }
        self.forecast_data = {}
        self.current_figure = {}
        
    

    def setup_routes(self):        
        @self.flask_server.route("/test", methods=["GET"])
        def index():
            return "Welcome to test", 200
                
        
    def setup_dash_callbacks(self):
        # Define the callbacks    
        self.app.callback(
            Output("update_data_status", "children"),
            Input("update_data_btn", "n_clicks"),
        )(self.update_data)      
        
        
        self.app.callback(
            Output("itemsDropdown", "options"),
            Input("selectBrandDropdown", "value"),
            Input("update_data_status", "children"),
        )(self.update_brand_or_data)  
                
        
        self.app.callback(            
            Output("selectedItem", "children"),
            [
                Input("itemsDropdown", "value"),
                Input("frequencyDropdown", "value"),
                Input("update_interval", "n_intervals"),                
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
            Output("chart", "figure", allow_duplicate=True),
            Input("updatedDecomposedTimeSeries", "children"),            
            prevent_initial_call=True
        )(self.update_chart_with_decomposed_data)
        
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
            Output("forecastData", "children"),     
            Input("forecastButton", "n_clicks"),                        
        )(self.update_forecast_data)
        
        self.app.callback(
            Output("chart", "figure", allow_duplicate=True),
            Input("forecastData", "children"),            
            prevent_initial_call=True
        )(self.update_chart_with_forecast_data)
        
        self.app.callback(
            Output("exportButton", "disabled"),
            Input("forecastData", "children"),
        )(self.check_export_button)
        
        self.app.callback(
            Input("exportButton", "n_clicks"),
        )(self.handle_export_button)
                

    def initialize_request(self):
        self.base_url = request.host_url    
    
    def update_data(self, n_clicks):
        if n_clicks > 0:
            request_url = url_for('api.update_data', _external=True)
            response = requests.get(
                request_url
            )
            if response.status_code == 200:
                return "updated"               
            else:
                raise Exception("Failed to update data")            
    
    def update_brand_or_data(self, brand, updated_data_msg):        
        api_blueprint.set_sentinel(brand=brand)
        self.selected_brand = brand
        request_url = url_for('api.get_brand_items', _external=True)
        response = requests.get(
            request_url, 
            params={
                "brand": brand
            }
        )
        if response.status_code == 200:
            self.items_dict = response.json()           
            return self.items_dict
    
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
                                                 
    def update_time_series(self, item, frequency, n_intervals):
        print("Updated Time Series: {n_intervals}")
        # make a request to the API which retreives the sales dupdatedParamsata for given item and frequency        
        request_url = url_for('api.get_item_data', _external=True)
        # Get the time series provided item
        response = requests.get(
            request_url, 
            params={
                "item_gid": item, 
                "frequency": frequency
            }
        )
        self.selected_item_gid = item
        self.selected_item_name = self.items_dict.get(item)
        self.time_series = response.json() 
        self.frequency = frequency       
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
            "params": self.stfl_params,
            "frequency": self.frequency
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
    def update_chart_with_decomposed_data(self, decomposed_time_series_msg):
        # make the plot with plotly express
        dates = list(self.decomposed_time_series["trend"].keys())
        
        trend_data = list(self.decomposed_time_series["trend"].values())
        seasonal_data = list(self.decomposed_time_series["seasonal"].values())
        residual_data = list(self.decomposed_time_series["residual"].values())
        if not trend_data or not seasonal_data or not residual_data:
            print("No decomposed data to plot")
            return {}        
        seasonal_adjusted_data = [x + y for x, y in zip(trend_data, residual_data)]
        full_data = [x + y for x, y in zip(seasonal_adjusted_data, seasonal_data)]        
        
        fig = go.Figure()
        
        trend_data = go.Scatter(
            x=dates,
            y=trend_data,
            mode="lines",
            name="Trend",
            opacity=0.7,
            line = dict(color="blue")
        )
        
        seasonal_adjusted_figure = go.Scatter(
            x=dates,
            y=seasonal_adjusted_data,
            mode="lines",
            name="Seasonal Adjusted",  
            opacity=0.5,
            line=dict(color="#ff3c4c")          
        )
        
        full_data_figure = go.Scatter(
            x=dates,
            y=full_data,
            mode="lines+markers",
            name="Original Data",            
            marker=dict(color="green", size=5, symbol="square"),
        )
        
        fig.add_traces([trend_data, seasonal_adjusted_figure, full_data_figure])
        self.current_figure = fig
        return fig
    
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
        dates = self.decomposed_time_series["trend"].keys()  
        seasonal_adjusted_data = {date: self.decomposed_time_series["trend"][date] + self.decomposed_time_series["residual"][date] for date in dates}
        full_data = {date: seasonal_adjusted_data[date] + self.decomposed_time_series["seasonal"][date] for date in dates}
        if n_clicks > 0:
            request_url = url_for('api.get_forecast_data', _external=True)
            headers = {"Content-Type": "application/json"}
            curve = self.forecast_params["forecast_curve"]
            if curve == "trend":
                curve_data = self.decomposed_time_series["trend"]
            elif curve == "seasonal_adjusted":
                curve_data = seasonal_adjusted_data
            else:
                curve_data = full_data
            
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
        
        return f"Updated forecast data"
    
    def update_chart_with_forecast_data(self, forecast_data_msg):
        if not self.current_figure:
            return {}
        
        fig = go.Figure(self.current_figure)
        
        if forecast_data_msg:
            dates = list(self.forecast_data.keys())
            forecast_data = list(self.forecast_data.values())
            forecast_data_figure = go.Scatter(
                x=dates,
                y=forecast_data,
                mode="markers",
                marker=dict(
                    symbol="star",
                ),                
                name="forecast"
            )
            fig.add_traces([forecast_data_figure])
            
            return fig
        
        return fig
    
    def check_export_button(self, forecast_data):
        if self.forecast_data:
            return False
        return True
    
    def handle_export_button(self, n_clicks):
        if n_clicks > 0:
            date_from = datetime.now().strftime("%Y-%m-%d")
            date_to = datetime.now() + timedelta(days=self.forecast_params['n_preds'])
            date_to = date_to.strftime("%Y-%m-%d")
            print("***" * 30)
            if not os.path.isdir(f"data/results/{self.selected_brand}"):
                os.makedirs(f"data/results/{self.selected_brand}")
                
            file_name = f"forecast_{date_from}.csv"
            if not os.path.isfile(f"data/results/{self.selected_brand}/{file_name}"):
                export_df = pd.DataFrame(columns=["item_name", "forecast_model", "forecast_method", "forecast_curve", "pred_from", "pred_to", "value"])
            else:
                export_df = pd.read_csv(f"data/results/{self.selected_brand}/{file_name}")
            
            # Update the export_df with new data
            item_name = self.selected_item_name
            forecast_model = self.forecast_params["model"]
            forecast_method = self.forecast_params["forecast_method"]
            forecast_curve = self.forecast_params["forecast_curve"]
            value = sum(list(self.forecast_data.values()))
            value = round(value, 2)
            update_row = export_df.loc[
                (export_df["item_name"] == item_name) & (export_df["forecast_model"] == forecast_model) & (export_df["forecast_method"] == forecast_method)
            ] 
            if update_row.empty:
                update_index = len(export_df)
            else:
                update_index = update_row.index
            
            export_df.loc[update_index] = [item_name, forecast_model, forecast_method, forecast_curve, date_from, date_to, value]
            export_df.to_csv(f"data/results/{self.selected_brand}/{file_name}", index=False)

    # Define the run method
    def run(self):
        self.flask_server.run(debug=True)
    

if __name__ == '__main__':
    app = FlaskDashApp()
    app.run()