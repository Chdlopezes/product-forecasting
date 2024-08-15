from flask import Blueprint, jsonify, request
from src.nodek_sentinel import Sentinel
import pandas as pd
from datetime import datetime

today_date_str = datetime.today().strftime("%Y-%m-%d")
uhtil_sentinel = Sentinel(store_name="Uhtil", initialize_data=True)
uhtil_sentinel.start(from_date=today_date_str)
jo_sentinel = Sentinel(store_name="JO", initialize_data=False)
jo_sentinel.start(from_date=today_date_str)

class APIBlueprint():
    def __init__(self):
        self.api_bp = Blueprint('api', __name__)
        self.brand = ""
        self.sentinel = uhtil_sentinel
        self.register_routes()        
            
    def register_routes(self):
        self.api_bp.route('/')(self.index)
        self.api_bp.route("get_brand_items", methods=["GET"])(self.get_brand_items)
        self.api_bp.route("/data", methods=["GET"])(self.get_data)
        self.api_bp.route("/api/get_decomposed_data", methods=["POST"])(self.get_decomposed_data)
        self.api_bp.route("/api/get_forecast_data", methods=["POST"])(self.get_forecast_data)

    def set_sentinel(self, brand):
        self.brand = brand
        if brand == "Uhtil":            
            self.sentinel = uhtil_sentinel
        elif brand == "JO":            
            self.sentinel = jo_sentinel
        
    def index(self):
        return 'Welcome to the main page. Go to /dash for the Dash app or /api/data for the API.'
                
    
    def get_brand_items(self):
        brand = request.args.get("brand")
        if not brand:
            return {"message": "brand is required"}, 400
        items_df = self.sentinel.get_items_df()
        items_dict = dict(zip(items_df["item_gid"], items_df["name"]))        
        return jsonify(items_dict)
    
    def get_data(self):        
        item_gid = request.args.get("item_gid")
        frequency = request.args.get("frequency")        
        if not item_gid:
            return {"message": "item_gid is required"}, 400
        if not frequency:
            return {"message": "frequency is required"}, 400
        # TODO : Implement in sentinel mehtod from and to        
        time_series = self.sentinel.get_time_series(item_gid=item_gid, frequency=frequency)
        # convert the dataframe to a list of dictionaries
        time_series_dict = {item.strftime("%Y-%m-%d %H:%M:%S"): value for item,value in  time_series.items()}
        return jsonify(time_series_dict)

    def get_decomposed_data(self):
        if request.method == "POST":
            payload = request.get_json()
            # The data comes from requests library in the form requests.get(url, data={"time_series": [...], "params": {...} }) So I need to parse it            
            time_series = payload.get("time_series", None)
            params = payload.get("params", None)            
            if not params:
                return {"message": "params is required"}, 400
            if not time_series or len(time_series) <= 20:
                return {"message": "time_series too short or missing"}, 400                    
            if not veryfy_stfl_params_dict(params):
                return {"message": "invalid stfl params"}, 400
                
            time_series_df = pd.Series(time_series)
            if not time_series_df.empty:
                time_series_df.index = pd.to_datetime(time_series_df.index)
            decomposed_df = self.sentinel.get_stlf_manual_forecast_figure(time_series_df, params)            
            decomposed_time_series = {
                "trend": {date.strftime("%Y-%m-%d %H:%M:%S"): value for date,value in decomposed_df.trend.items()},
                "seasonal":{date.strftime("%Y-%m-%d %H:%M:%S"): value for date,value in decomposed_df.seasonal.items()},
                "residual": {date.strftime("%Y-%m-%d %H:%M:%S"): value for date,value in decomposed_df.resid.items()},
            }
            return jsonify(decomposed_time_series)
        
    def get_forecast_data(self):
        if request.method == 'POST':
            request_data = request.get_json()
            curve = request_data["curve"]
            model = request_data["model"]
            method = request_data["method"]
            n_preds = request_data["n_preds"]
            forecast_series = self.sentinel.get_forecast_series(curve, model, method, n_preds)
            # convert the pandas series to dict in order to return it
            forecast_series_dict = {date.strftime("%Y-%m-%d %H:%M:%S"): value for date,value in forecast_series.items()}
            return jsonify(forecast_series_dict)


def veryfy_stfl_params_dict(ets_params_dict):
    if ets_params_dict.get("period", None):
        if ets_params_dict.get("trend_smooth", None):
            if ets_params_dict.get("seasonal_smooth", None):                
                return True
    return False