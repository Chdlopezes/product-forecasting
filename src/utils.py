from datetime import datetime, timedelta
import time
import numpy as np
import pandas as pd
from src.shopify_api import Shops
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.api import SimpleExpSmoothing, Holt, ExponentialSmoothing

def get_all_shopify_data_from_shopify_api(date_str, store_name):
    date_object = datetime.strptime(date_str, "%Y-%m-%d")
    if store_name == "uhtil":
        store = Shops.Uhtil()
        
    elif store_name == "jo":
        store = Shops.JO()
                    
    full_response_data = []
    for day in range(30 + 1):     
        to_date_str = date_object.strftime("%Y-%m-%d")    
        from_date_obj = date_object - timedelta(days=1)
        from_date_str = from_date_obj.strftime("%Y-%m-%d")
        date_object = from_date_obj
        
        print(f"Getting the info from date:{from_date_str} to date: {to_date_str} ...")        
        all_orders = store.get_all_orders(date_str=from_date_str, end_date_str=to_date_str)
        black_list_emails = ["Unknown", "xxxxxx@gmail.com", "joshoescolombia@gmail.com"]                
        full_response_data = []
        print(f"INFO: Processing {len(all_orders)} orders")
        for i, order_dict in enumerate(all_orders, start=1) :            
            print("***" * 15)
            print(f"INFO: Processing order {i} of {len(all_orders)}")
            if order_dict["customer_email"] not in black_list_emails: 
                order_items = store.get_all_order_items(order_dict["gid"])                
                order_full_dict = order_dict | {"order_items": order_items}
                full_response_data.append(order_full_dict)
                time.sleep(0.3)
        time.sleep(0.5)
        full_response_data.append(full_response_data)      
                
    return full_response_data

def get_store_orders_data_from_shopify_api(store_name, date_from, date_to=None):    
    if store_name == "Uhtil":
        store = Shops.Uhtil()
        
    elif store_name == "JO":
        store = Shops.JO()
                        
    print(f"Getting the info from date:{date_from} to date: {date_to} ...")        
    all_orders = store.get_all_orders(date_str=date_from, end_date_str=date_to)
    black_list_emails = ["Unknown", "xxxxxx@gmail.com", "joshoescolombia@gmail.com"]                
    full_response_data = []
    print(f"INFO: Processing {len(all_orders)} orders")
    for i, order_dict in enumerate(all_orders, start=1) :            
        print("***" * 15)
        print(f"INFO: Processing order {i} of {len(all_orders)}")
        if order_dict["customer_email"] not in black_list_emails: 
            order_items = store.get_all_order_items(order_dict["gid"])                
            order_full_dict = order_dict | {"order_items": order_items}
            full_response_data.append(order_full_dict)
            time.sleep(0.3)
    time.sleep(0.5)    
            
    return full_response_data

    
def convert_orders_json_response_to_df(full_response_data):
    records_dict = []
    if len(full_response_data) == 0:
        return pd.DataFrame()
    
    for data_dict in full_response_data: 
        for order_item in data_dict['order_items']:
            records_dict.append({
                'order_gid': data_dict['gid'],
                'date': data_dict['createdAt'],
                'customer_email': data_dict['customer_email'],
                'item_gid': order_item['gid'],
                'name': order_item['name'],
                'product': order_item['product'],
                'product_gid': order_item['product_gid'],
                'quantity': int(order_item['quantity']),
                'price': int(float(order_item['price']))               
            })

    orders_df = pd.DataFrame(records_dict)
    orders_df["date"] = pd.to_datetime(orders_df["date"])
    orders_df["date"] = orders_df["date"].apply(lambda x: x.strftime("%Y-%m-%d"))
    return orders_df    


def remove_days_with_low_sales(orders_df, price_threshold):        
        agg_dates_orders_df = orders_df.groupby(by="date").agg({
            "quantity": "sum",
            "price": "sum"
        })
        filtered_dates = agg_dates_orders_df[agg_dates_orders_df["price"] >= price_threshold].index.values        
        print(f"Dates with sales below {price_threshold}: {len(agg_dates_orders_df) - len(filtered_dates)}")
        print(f"Sales before filtering: {len(orders_df)}")
        orders_df = orders_df[orders_df["date"].isin(filtered_dates)]
        print(f"Sales after filtering: {len(orders_df)}")
        return orders_df
        

def get_aggregated_orders_by_day(orders_df, item_gid):
        item_df_raw = orders_df[orders_df["item_gid"] == item_gid]
        item_name = item_df_raw["name"].values[0]
        print("item_name: ", item_name)
        item_df_groupped = item_df_raw.groupby("date").agg({    
            "item_gid": "first",
            "name": "first",
            "product": "first",
            "product_gid": "first",
            "quantity": "sum",
            "price": "sum"
        })
        
        item_df_groupped = item_df_groupped.reset_index()
        dates = pd.to_datetime(item_df_groupped["date"])
        min_date = dates.min()
        max_date = dates.max()
        item_date_range = pd.date_range(start=min_date, end=max_date, freq="D")
        item_date_range = [date.strftime("%Y-%m-%d") for date in item_date_range]
        item_time_series = []
        for item_date in item_date_range:
            filtered_row = item_df_groupped[item_df_groupped["date"].str.contains(item_date)]    
            if filtered_row.empty: 
                item_time_series_record = {
                    "date": item_date,
                    "quantity": 0
                }
            else:
                item_time_series_record = {
                    "date": item_date,
                    "quantity": filtered_row["quantity"].values[0]
                }
            item_time_series.append(item_time_series_record)

        item_time_series_df_daily = pd.DataFrame(item_time_series)        
        item_time_series_daily_stats= {
            "name": item_name,
            "mean": item_time_series_df_daily["quantity"].mean(),
            "std": item_time_series_df_daily["quantity"].std(),
            "request_quantity": np.ceil(item_time_series_df_daily["quantity"].mean() + item_time_series_df_daily["quantity"].std())
        }
        return item_time_series_df_daily, item_time_series_daily_stats

def get_aggregated_orders_by_week(orders_df, item_gid):
        # first get the aggregaded orders by day
        item_time_series_df = get_aggregated_orders_by_day(orders_df, item_gid)[0]
        # Group by weeks        
        item_time_series_df["date"] = pd.to_datetime(item_time_series_df["date"])
        item_time_series_df_weekly = item_time_series_df.set_index("date")
        item_time_series_df_weekly = item_time_series_df_weekly.resample("W").agg("sum").reset_index()
        weekly_sales_mean = item_time_series_df_weekly["quantity"].mean()
        weekly_sales_std = item_time_series_df_weekly["quantity"].std()
        item_time_series_df_weekly_stats= {
            "mean": weekly_sales_mean,
            "std": weekly_sales_std,
            "request_quantity": np.ceil(weekly_sales_mean + weekly_sales_std)
        }                        
        return item_time_series_df_weekly, item_time_series_df_weekly_stats

def remove_consecutive_zeros_and_get_time_series(df, allowed_consecutive_zeros, time_range_frequency):
    clean_df = df.copy(deep=True)
    if allowed_consecutive_zeros < len(clean_df):        
        mask = clean_df["quantity"] == 0
        for i in range(1, allowed_consecutive_zeros):
            mask = (mask) & (clean_df["quantity"].shift(i) == 0)
        mask_idx = mask[mask].index.values    
        mask_idx_list = list(mask_idx)    
        for i in range(1, allowed_consecutive_zeros):
            mask_idx_list += list(mask_idx - i)        
        mask_idx_list = list(set(mask_idx_list))
        clean_df = clean_df.drop(mask_idx_list)                
    index = pd.date_range(end=datetime.now(), periods=len(clean_df), freq=time_range_frequency)
    time_series = pd.Series(clean_df["quantity"].values, index=index)
    return time_series


def get_model_predictions(fitted_model, n_predictions):
    model_simulation_df= fitted_model.simulate(
        n_predictions, 
        repetitions=100,
        error="mul",
        random_errors="bootstrap",
        random_state=12
    )       
    model_simulation_df = model_simulation_df.dropna()    
    
    final_forecast = model_simulation_df.median(axis=1)            
    final_forecast = final_forecast.apply(lambda x: x if x >= 0 else 0)
    return final_forecast


def ets_forecast(curve_series, method, n_preds):
    if method == "sse":
        fitted_model = SimpleExpSmoothing(curve_series, initialization_method="estimated").fit() 
    elif method == "seasonal_add":
        fitted_model = ExponentialSmoothing(
            curve_series,
            trend=None, 
            seasonal="add", 
            damped_trend=False, 
            initialization_method="estimated",
            use_boxcox=False
        ).fit()     
        
        
    elif method == "trend_add":
        fitted_model = ExponentialSmoothing(
            curve_series,
            trend="add", 
            seasonal=None, 
            damped_trend=True, 
            initialization_method="estimated",
            use_boxcox=False
        ).fit()     
        
    elif method == "trend_seasonal_add":
        fitted_model = ExponentialSmoothing(
            curve_series,
            trend="add", 
            seasonal="add", 
            damped_trend=True, 
            initialization_method="estimated",
            use_boxcox=False
        ).fit()
    else: 
        raise ValueError("method must be one of: 'sse', 'seasonal_add', 'trend_add', 'trend_seasonal_add'")
    
    fitted_model_forecast = get_model_predictions(
        fitted_model=fitted_model, 
        n_predictions=n_preds,         
    )
    
    return fitted_model_forecast
       
     
def arima_forecast(curve_series, method):
    pass