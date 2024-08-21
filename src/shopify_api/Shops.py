import os
import json
import time
import dotenv
import shopify
import pathlib
from dotenv import load_dotenv



class Shop:
    def __init__(self):
        dotenv.load_dotenv(".env")         
        self.gql = pathlib.Path(f"{os.getenv('ROOT_DIR')}/shopify_api/gql_queries.graphql").read_text()
        

    def get_shopify_data(self, object_name):
        attribute = getattr(shopify, object_name)
        data_page = attribute.find(since_id=0, limit=250)

        data = []
        for row in data_page:
            data.append(row)

        while data_page.has_next_page():
            data_page = data_page.next_page()
            for row in data_page:
                data.append(row)

        return data

    
    def get_all_orders(self, date_str, end_date_str=None, excluded=[], query=None):
        has_next_page = True
        cursor = None
        
        if not query:
            if not date_str:
                query = f"created_at:>'2023-01-01' AND NOT fulfillment_status:<=fulfilled AND NOT financial_status:voided"
            
            elif date_str and end_date_str:
                query = f"created_at:>'{date_str}' AND created_at:<='{end_date_str}'"
            else: 
                query = f"created_at:>'{date_str}'"

        orders_records = []
        page = 0
        while has_next_page:
            time.sleep(0.5)
            orders_query = shopify.GraphQL().execute(
                query=self.gql,
                variables={"itemsByPage": 50, "cursor": cursor, "query": query},
                operation_name="GetOrders",
            )

            orders_json = json.loads(orders_query)

            for order in orders_json["data"]["orders"]["nodes"]:
                if int(order["name"].replace("#", "")) in excluded:
                    continue

                if order["cancelledAt"]:
                    continue
                
                try:
                    customer_email = order["customer"]["email"]
                except:
                    customer_email = "Unknown"
                 
                order_dict = {
                    "gid": order["id"],
                    "title": f"{order['name']}",
                    "createdAt": order["createdAt"],
                    "customer_email": customer_email,
                }
                orders_records.append(order_dict)

            has_next_page = orders_json["data"]["orders"]["pageInfo"]["hasNextPage"]
            if has_next_page:
                cursor = orders_json["data"]["orders"]["pageInfo"]["endCursor"]
                page += 1
            else:
                break

        return orders_records
            

    def get_all_order_items(self, gid):
        has_next_page = True
        cursor = None
        order_items = []
        page = 0

        while has_next_page:
            time.sleep(0.35)

            order_query = shopify.GraphQL().execute(
                query=self.gql,
                variables={"order_id": gid, "itemsByPage": 20, "cursor": cursor},
                operation_name="GetOrderItems2",
            )
            order_json = json.loads(order_query)

            for order_item in order_json["data"]["order"]["lineItems"]["edges"]:
                
                product = order_item["node"]["product"]
                if not product:
                    continue
                # TODO: Consider the case when variant is a Pack -> Find related variants
                # in parent product and set the corresponding quantity  for each
                
                variant = order_item["node"]["variant"]
                if not variant:
                    continue
                                    
                quantity = order_item["node"]["quantity"]
                
                ######
                
                if not quantity:
                    continue
                
                item = {
                    "item_order_number": order_json["data"]["order"]["name"],
                    "gid": variant["id"],
                    "name": order_item["node"]["name"],
                    "product": product["title"],
                    "variant": variant["title"],
                    "quantity": quantity,
                    "price": variant["price"],
                    "product_gid": product["id"],
                    "vendor": product["vendor"],
                }

                order_items.append(item)

            has_next_page = order_json["data"]["order"]["lineItems"]["pageInfo"][
                "hasNextPage"
            ]
            if has_next_page:
                cursor = order_json["data"]["order"]["lineItems"]["pageInfo"][
                    "endCursor"
                ]
                page += 1
            else:
                break

        return order_items    



class JO(Shop):
    def __init__(self):
        super().__init__()
        
        self.root_url = "https://admin.shopify.com/store/129754/"

        SHOP_URL = os.getenv("JO_SHOP_URL")
        TOKEN = os.getenv("JO_TOKEN")        

        self.nodek_api_session = shopify.Session(SHOP_URL, "2024-07", TOKEN)
        shopify.ShopifyResource.activate_session(self.nodek_api_session)


class Uhtil(Shop):
    def __init__(self):
        super().__init__()

        self.root_url = "https://admin.shopify.com/store/uhtil/"

        SHOP_URL = os.getenv("UHTIL_SHOP_URL")
        TOKEN = os.getenv("UHTIL_TOKEN")

        self.nodek_api_session = shopify.Session(SHOP_URL, "2024-07", TOKEN)
        shopify.ShopifyResource.activate_session(self.nodek_api_session)


class ParamoProject(Shop):
    def __init__(self):
        super().__init__()

        self.root_url = "https://admin.shopify.com/store/940c12-f6/"
        
        SHOP_URL = os.getenv("UHTIL_SHOP_URL")
        TOKEN = os.getenv("UHTIL_TOKEN")

        self.nodek_api_session = shopify.Session(SHOP_URL, "2023-10", TOKEN)
        shopify.ShopifyResource.activate_session(self.nodek_api_session)


class Serena(Shop):
    def __init__(self):
        super().__init__()

        self.root_url = "https://admin.shopify.com/store/serena/"

        SHOP_URL = os.getenv("UHTIL_SHOP_URL")
        TOKEN = os.getenv("UHTIL_TOKEN")

        self.nodek_api_session = shopify.Session(SHOP_URL, "2024-07", TOKEN)
        shopify.ShopifyResource.activate_session(self.nodek_api_session)

