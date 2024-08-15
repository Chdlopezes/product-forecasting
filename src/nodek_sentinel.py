import pandas as pd
import threading
from statsmodels.tsa.seasonal import STL
from apscheduler.schedulers.background import BackgroundScheduler
from src import utils


class Sentinel():
    def __init__(self, store_name, initialize_data=False):
        self.store_name = store_name
        self.min_item_orders = 20
        if store_name == "Uhtil":
            self.orders_price_threshold = 200000
        elif store_name == "JO":
            self.orders_price_threshold = 300000
        self.data = pd.DataFrame()        
        if initialize_data:
            if store_name == "Uhtil":
                self.data = pd.read_csv("data/uhtil_orders.csv")
            elif store_name == "JO":
                self.data = pd.read_csv("data/JO_orders.csv")
        self.lock = threading.Lock()
        self.time_range = 60 # in days
        
        
    def start(self, from_date):
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=self.retrieve_and_store_orders_data, 
            kwargs={"store_name": self.store_name, "data_from_str": from_date},
            trigger='interval',
            hours=24
        )
        scheduler.start()
                            
    def retrieve_and_store_orders_data(self, store_name, data_from_str, date_to_str=None):
        # Retrieve from external API
        shopify_orders_response_data = utils.get_store_orders_data_from_shopify_api(
            store_name=store_name, 
            date_from=data_from_str, 
            date_to=date_to_str            
        )
        shopify_orders_df = utils.convert_orders_json_response_to_df(shopify_orders_response_data)
        # check if sales data has enough sales to be considered
        shopify_orders_df = utils.remove_days_with_low_sales(shopify_orders_df, price_threshold=self.orders_price_threshold)
        new_df = shopify_orders_df
        # Convert to Dataframe        
        new_df["date"] = pd.to_datetime(new_df["date"])
        if not self.data.empty:
            # check the latest date in current  data
            latest_date = self.data["date"].max()
            # from new_df select only rows with date > latest_date
            new_df = new_df[new_df["date"] > latest_date]
        with self.lock:
            self.data = pd.concat([self.data, new_df])       
            # drop data older than time_range
            last_date_to_keep = pd.Timestamp.now() - pd.Timedelta(days=self.time_range)
            self.data = self.data[self.data["date"] > last_date_to_keep]            
        
    def get_items_df(self):
        with self.lock:
            items_df = self.data.groupby("item_gid").agg(
                name=("name", "first"),
                n_orders=("item_gid", "count")                
            ).reset_index()
            items_df = items_df[items_df["n_orders"] > self.min_item_orders]
            return items_df
    
    def get_time_series(self, item_gid, frequency):
        # convert self.data to a pandas series whose index is date
        with self.lock:
            if frequency == "daily":
                item_orders_df_daily, item_orders_stats = utils.get_aggregated_orders_by_day(orders_df=self.data, item_gid=item_gid)
                time_series = utils.remove_consecutive_zeros_and_get_time_series(
                    item_orders_df_daily, 
                    allowed_consecutive_zeros=30,
                    time_range_frequency="D"
                )
            elif frequency == "weekly":
                item_orders_df_weekly, item_orders_weekly_stats = utils.get_aggregated_orders_by_week(orders_df=self.data, item_gid=item_gid)
                time_series = utils.remove_consecutive_zeros_and_get_time_series(
                    item_orders_df_weekly, 
                    allowed_consecutive_zeros=2, 
                    time_range_frequency="W"
                )                
            return time_series
            
    def get_stlf_manual_forecast_figure(self, time_series, params):
        time_series_decomposition = STL(
            time_series, 
            period=params.get("period"), 
            trend=params.get("trend_smooth"), 
            seasonal=params.get("seasonal_smooth")
        ).fit()       
         
        return time_series_decomposition
    
    def get_forecast_series(self, curve_series, model, method, n_preds):
        if model == "ets":
            forecast_series = utils.ets_forecast(curve_series, method, n_preds)
        elif model == "arima":
            forecast_series = utils.arima_forecast(curve_series, method, n_preds)                
        return forecast_series

            