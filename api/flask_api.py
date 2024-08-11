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
        time_series_df = self.sentinel.get_time_series(item_gid=item_gid, frequency=frequency)
        # convert the dataframe to a list of dictionaries
        data = time_series_df.to_dict(orient="records")    
        return jsonify(data)

    def get_decomposed_data(self):
        if request.method == "POST":
            payload = request.get_json()
            # The data comes from requests library in the form requests.get(url, data={"time_series": [...], "params": {...} }) So I need to parse it            
            time_series = payload.get("time_series", None)
            if not time_series:
                return {"message": "time_series is required"}, 400        
            params = payload.get("params", None)
            if not params:
                return {"message": "params is required"}, 400
            time_series_df = pd.DataFrame(time_series)
            if not time_series_df.empty:
                time_series_df["date"] = pd.to_datetime(time_series_df["date"])                
            decomposed_df = self.sentinel.get_stlf_manual_forecast_figure(time_series_df, params)
            decomposed_time_series = decomposed_df.to_dict(orient="records")            
            return jsonify(decomposed_time_series)



