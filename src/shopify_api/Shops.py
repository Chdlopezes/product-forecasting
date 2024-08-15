import os
import json
import time
import dotenv
import shopify
import pathlib


class Shop:
    def __init__(self):
        self.gql = pathlib.Path(f"src/shopify_api/gql_queries.graphql").read_text()
        dotenv.load_dotenv(".env")

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

    def get_all_variants(self):
        has_next_page = True
        cursor = None

        all_variants = []
        page = 0
        while has_next_page:
            variants_query = shopify.GraphQL().execute(
                query=self.gql,
                variables={"itemsByPage": 50, "cursor": cursor},
                operation_name="GetVariants",
            )

            variants_json = json.loads(variants_query)
            for variant in variants_json["data"]["productVariants"]["nodes"]:
                variant_dict = {
                    "gid": variant["id"],
                    "title": f"{variant['product']['title']} - {variant['title']}",
                    "barcode": variant["barcode"],
                }
                all_variants.append(variant_dict)

            has_next_page = variants_json["data"]["productVariants"]["pageInfo"][
                "hasNextPage"
            ]
            if has_next_page:
                cursor = variants_json["data"]["productVariants"]["pageInfo"][
                    "endCursor"
                ]
                page += 1
            else:
                break

        return all_variants

    def get_dated_orders(self, start_date, end_date, excluded=[]):
        has_next_page = True
        cursor = None
        query = f"processed_at:>'{start_date}' AND processed_at:<'{end_date}' AND NOT financial_status:voided"

        orders = []
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

                order_dict = {
                    "gid": order["id"],
                    "title": f"{order['name']}",
                }
                orders.append(order_dict)

            has_next_page = orders_json["data"]["orders"]["pageInfo"]["hasNextPage"]
            if has_next_page:
                cursor = orders_json["data"]["orders"]["pageInfo"]["endCursor"]
                page += 1
            else:
                break

        return orders

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
    
    def get_product(self, gid):
        if "gid" in str(gid):
            id = int(gid.split("/")[-1])
        else:
            id = gid

        product = shopify.Product.find(id)

        return product

    def get_variant(self, gid):
        if "gid" in str(gid):
            id = int(gid.split("/")[-1])
        else:
            id = gid

        variant = shopify.Variant.find(id)

        return variant

    def get_variant_info(self, gid):
        variant_query = shopify.GraphQL().execute(
            query=self.gql,
            variables={"variant_id": gid},
            operation_name="GetVariantInfo",
        )

        variant_json = json.loads(variant_query)

        return variant_json
    
    def get_product_info(self, gid):
        product_query = shopify.GraphQL().execute(
            query=self.gql,
            variables={"product_id": gid},
            operation_name="GetProductInfo",
        )

        product_json = json.loads(product_query)

        return product_json

    def get_order(self, gid):
        if "gid" in str(gid):
            id = int(gid.split("/")[-1])
        else:
            id = gid

        order = shopify.Order.find(id)

        return order

    def get_orders(self, date_str):
        orders_query = shopify.GraphQL().execute(
            query=self.gql,
            variables={"query": f"created_at:>{date_str}"},
            operation_name="GetOrders",
        )

        orders_json = json.loads(orders_query)

        order_gids = []
        for node in orders_json["data"]["orders"]["edges"]:
            order_id = node["node"]["id"]
            order_gids.append(order_id)

        return order_gids

    def get_order_items(self, gid):
        order_query = shopify.GraphQL().execute(
            query=self.gql, variables={"order_id": gid}, operation_name="GetOrderItems"
        )

        order_json = json.loads(order_query)

        order_items = []
        for node in order_json["data"]["order"]["lineItems"]["edges"]:
            name = node["node"]["name"]

            if not node["node"]["variant"]:
                continue

            item = {
                "gid": node["node"]["variant"]["id"],
                "name": name,
                "quantity": node["node"]["quantity"],
            }
            order_items.append(item)

        return order_items

    def get_order_items2(self, gid):
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
                try:
                    image_url = order_item["node"]["variant"]["image"]["url"]
                except TypeError:
                    try:
                        image_url = order_item["node"]["product"]["featuredImage"][
                            "url"
                        ]
                    except TypeError:
                        continue

                if int(order_item["node"]["currentQuantity"]) == 0:
                    continue
                if int(order_item["node"]["unfulfilledQuantity"]) == 0:
                    continue

                item = {
                    "item_order_number": order_json["data"]["order"]["name"],
                    "gid": order_item["node"]["variant"]["id"],
                    "name": order_item["node"]["name"],
                    "product": order_item["node"]["product"]["title"],
                    "variant": order_item["node"]["variant"]["title"],
                    "quantity": order_item["node"]["unfulfilledQuantity"],
                    "image_url": image_url,
                    "price": order_item["node"]["variant"]["price"],
                    "product_gid": order_item["node"]["product"]["id"],
                    "vendor": order_item["node"]["product"]["vendor"],
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
                variant = order_item["node"]["variant"]
                if not variant:
                    continue
                                    
                quantity = order_item["node"]["quantity"]
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

    def get_order_info(self, order_gid):
        order_info_query = shopify.GraphQL().execute(
            query=self.gql,
            variables={"order_id": order_gid},
            operation_name="GetOrderInfo",
        )
        order_info_json = json.loads(order_info_query)
        total_price = order_info_json["data"]["order"]["currentTotalPriceSet"][
            "shopMoney"
        ]["amount"]
        total_price = int(float(total_price))
        order_info = {
            "id": order_info_json["data"]["order"]["id"],
            "name": order_info_json["data"]["order"]["name"],
            "note": order_info_json["data"]["order"]["note"],
            "tags": order_info_json["data"]["order"]["tags"],
            "address1": order_info_json["data"]["order"]["shippingAddress"]["address1"],
            "address2": order_info_json["data"]["order"]["shippingAddress"]["address2"],
            "city": order_info_json["data"]["order"]["shippingAddress"]["city"],
            "client_name": order_info_json["data"]["order"]["shippingAddress"]["name"],
            "phone": order_info_json["data"]["order"]["shippingAddress"][
                "phone"
            ].replace(" ", ""),
            "created_at": order_info_json["data"]["order"]["createdAt"],
            "total_price": total_price,
        }

        return order_info

    def order_update(self, orderUpdate_input):
        order_update_response = shopify.GraphQL().execute(
            query=self.gql,
            variables={"input": orderUpdate_input},
            operation_name="orderUpdate",
        )
        return order_update_response

    def get_order_fulfilment_info(self, order_gid):
        time.sleep(0.35)
        order_query = shopify.GraphQL().execute(
            query=self.gql,
            variables={"order_id": order_gid},
            operation_name="GetOrderFulfillmentInfo",
        )
        order_json = json.loads(order_query)

        return order_json

    def get_order_fulfillment_order(self, order_gid):
        order_info_query = shopify.GraphQL().execute(
            query=self.gql,
            variables={"order_id": order_gid},
            operation_name="GetOrderFulfillmentOrders",
        )
        order_info_json = json.loads(order_info_query)
        order_info = {
            "fulfillmentOrder": order_info_json["data"]["order"]["fulfillmentOrders"][
                "edges"
            ][0]["node"]["id"],
            "fulfillmentOrderLineItems": order_info_json["data"]["order"][
                "fulfillmentOrders"
            ]["edges"][0]["node"]["lineItems"]["edges"],
        }

        return order_info

    def get_orders_items(self, order_gids):
        all_items = []
        for order_gid in order_gids:
            order_items = self.get_order_items(order_gid)
            all_items += order_items

        return all_items

    def get_orders_items2(self, order_gids):
        all_items = []
        for order_gid in order_gids:
            order_items = self.get_order_items2(order_gid)
            all_items += order_items

        return all_items

    def create_draft_order(self, order_params):
        draft_order_response = shopify.GraphQL().execute(
            query=self.gql,
            variables={"input": order_params},
            operation_name="draftOrderCreate",
        )

        print(draft_order_response)

    def create_order_fulfillment(self, order_fulfillment_params):
        fulfillment_response = shopify.GraphQL().execute(
            query=self.gql,
            variables={
                "fulfillment": order_fulfillment_params,
                "message": "Preparado desde Nodek Ops (opt2)",
            },
            operation_name="fulfillmentCreateV2",
        )

        print(fulfillment_response)

    def product_create(self, createProduct_ProductInput):
        page = 0
        cursor = None
        has_next_page = True
        data = {
            "product_gid": None,
            "product_title": None,
            "product_vendor": None,
            "variants": [],
        }

        while has_next_page:
            page += 1
            product_create_response = shopify.GraphQL().execute(
                query=self.gql,
                variables={
                    "input": createProduct_ProductInput,
                    "itemsByPage": 88,
                    "cursor": cursor,
                },
                operation_name="productCreate",
            )
            product_create_response_json = json.loads(product_create_response)

            if not data["product_gid"]:
                data["product_gid"] = product_create_response_json["data"][
                    "productCreate"
                ]["product"]["id"]
                data["product_title"] = product_create_response_json["data"][
                    "productCreate"
                ]["product"]["title"]
                data["product_vendor"] = product_create_response_json["data"][
                    "productCreate"
                ]["product"]["vendor"]

            for variant_json in product_create_response_json["data"]["productCreate"][
                "product"
            ]["variants"]["edges"]:
                variant_data = {
                    "variant_gid": variant_json["node"]["id"],
                    "variant_title": variant_json["node"]["title"],
                    "variant_sku": variant_json["node"]["sku"],
                }
                data["variants"].append(variant_data)

            has_next_page = product_create_response_json["data"]["productCreate"][
                "product"
            ]["variants"]["pageInfo"]["hasNextPage"]
            if has_next_page:
                cursor = product_create_response_json["data"]["productCreate"][
                    "product"
                ]["variants"]["pageInfo"]["endCursor"]
            else:
                break

        return data

    def add_product_media(self, media_params):
        media = media_params["media"]
        productId = media_params["productId"]
        add_product_media_response = shopify.GraphQL().execute(
            query=self.gql,
            variables={"media": media, "productId": productId},
            operation_name="productCreateMedia",
        )
        add_product_media_response_json = json.loads(add_product_media_response)
        print(
            f"    INFO: Shops.add_product_media is loading {len(media)} images; wait {len(media)*1.1} seconds..."
        )
        time.sleep(1.3 + len(media) * 1.1)

        return add_product_media_response_json

    def get_location_id(self):
        get_location_response = shopify.GraphQL().execute(
            query=self.gql, operation_name="GetLocationId"
        )
        location_response_json = json.loads(get_location_response)

        return location_response_json["data"]["location"]["id"]

    def get_variant_inventory_item(self, variant_gid):
        product_query = shopify.GraphQL().execute(
            query=self.gql,
            variables={"id": variant_gid},
            operation_name="GetVariantInventoryItem",
        )

        product_json = json.loads(product_query)

        return product_json

    def product_variant_update_stock(
        self, variant_gid, stock, location_id, operation="update"
    ):
        variant_inventoryItem = shopify.GraphQL().execute(
            query=self.gql,
            variables={
                "id": variant_gid,
                "locationId": location_id,
            },
            operation_name="GetVariantInventoryItem",
        )
        variant_inventoryItem_json = json.loads(variant_inventoryItem)
        try:
            inventoryLevel_gid = variant_inventoryItem_json["data"]["productVariant"][
                "inventoryItem"
            ]["inventoryLevel"]["id"]
        except:
            return None
        inventoryQuantity_0 = variant_inventoryItem_json["data"]["productVariant"][
            "inventoryQuantity"
        ]
        if operation == "update":
            stock_delta = stock
        elif operation == "reset":
            stock_delta = stock - inventoryQuantity_0
        else:
            raise NotImplementedError("Whatcha doing, mate?")

        InventoryAdjustQuantityInput = {
            "inventoryLevelId": inventoryLevel_gid,
            "availableDelta": stock_delta,
        }
        stock_update_response = shopify.GraphQL().execute(
            query=self.gql,
            variables={"input": InventoryAdjustQuantityInput},
            operation_name="inventoryAdjustQuantity",
        )
        stock_update_response_json = json.loads(stock_update_response)

        return stock_update_response_json

    def get_collections(self):
        has_next_page = True
        cursor = None

        all_collections = []
        page = 0
        while has_next_page:
            collections_query = shopify.GraphQL().execute(
                query=self.gql,
                variables={"itemsByPage": 10, "cursor": cursor},
                operation_name="GetCollections",
            )
            collections_json = json.loads(collections_query)
            for collection_node in collections_json["data"]["collections"]["edges"]:
                collection = {
                    "gid": collection_node["node"]["id"],
                    "title": collection_node["node"]["title"],
                    "handle": collection_node["node"]["handle"],
                    "description": collection_node["node"]["description"],
                    "seo_title": collection_node["node"]["seo"]["title"],
                    "seo_description": collection_node["node"]["seo"]["description"],
                }
                all_collections.append(collection)

            has_next_page = collections_json["data"]["collections"]["pageInfo"][
                "hasNextPage"
            ]
            if has_next_page:
                cursor = collections_json["data"]["collections"]["pageInfo"][
                    "endCursor"
                ]
                page += 1
            else:
                break

        return all_collections

    def update_collection_seo(self, collectionUpdate_input):
        update_collection_response = shopify.GraphQL().execute(
            query=self.gql,
            variables={"input": collectionUpdate_input},
            operation_name="collectionUpdateSEO",
        )
        print(update_collection_response)
    
    def get_products(self):
        has_next_page = True
        cursor = None

        all_products = []
        page = 0
        while has_next_page:
            products_query = shopify.GraphQL().execute(
                query=self.gql,
                variables={"itemsByPage": 25, "cursor": cursor},
                operation_name="GetProducts",
            )
            products_json = json.loads(products_query)
            for product_node in products_json["data"]["products"]["edges"]:
                product = {
                    "gid": product_node["node"]["id"],
                    "title": product_node["node"]["title"],
                    "seo_title": product_node["node"]["seo"]["title"],
                    "seo_description": product_node["node"]["seo"]["description"],
                }
                all_products.append(product)

            has_next_page = products_json["data"]["products"]["pageInfo"][
                "hasNextPage"
            ]
            if has_next_page:
                cursor = products_json["data"]["products"]["pageInfo"][
                    "endCursor"
                ]
                page += 1
            else:
                break

        return all_products
    
    def get_products_for_siigo(self):            
        has_next_page = True
        cursor = None
        query = f"status:active"
        print("Getting Products for Siigo...")  
        all_products = []
        page = 0
        while has_next_page:
            products_query = shopify.GraphQL().execute(
                query=self.gql,
                variables={"itemsByPage": 25, "cursor": cursor, "query": query},
                operation_name="GetProductsForSiigo",
            )
            products_json = json.loads(products_query)
            for product_node in products_json["data"]["products"]["edges"]:
                product = {
                    "gid": product_node["node"]["id"],
                    "max_price": product_node["node"]["priceRangeV2"]["maxVariantPrice"]["amount"],
                    "min_price": product_node["node"]["priceRangeV2"]["minVariantPrice"]["amount"],
                    "title": product_node["node"]["title"],
                    "seo_title": product_node["node"]["seo"]["title"],
                    "seo_description": product_node["node"]["seo"]["description"],
                }
                if not product["min_price"] == product["max_price"]:
                    print("WARNING: Min and Max prices are different for product: ", product["title"])
                    continue
                product["price"] = product["min_price"]
                product["gid_code"] = product["gid"].split("/")[-1]
                all_products.append(product)

            has_next_page = products_json["data"]["products"]["pageInfo"][
                "hasNextPage"
            ]
            if has_next_page:
                cursor = products_json["data"]["products"]["pageInfo"][
                    "endCursor"
                ]
                page += 1
            else:
                break

        return all_products
                    

    def create_collection(self, collectionCreate_input):
        create_collection_response = shopify.GraphQL().execute(
            query=self.gql,
            variables={"input": collectionCreate_input},
            operation_name="collectionCreate",
        )
        print(create_collection_response)

    def get_3p_order_items(self, all_items):
        all_line_items = []
        for item in all_items:
            manufacturer = self.get_item_manufacturer_vendor(item)
            try:
                if "jpg" in item["image_url"]:
                    print()
                    print(item["image_url"])
                    print(f"INFO: Shops.get_3p_order_items - try if jpg")
                    image_url_split = item["image_url"].split(".jpg")
                    item_image_url = (
                        f"{image_url_split[0]}_256x.jpg{image_url_split[1]}"
                    )
                elif "png" in item["image_url"]:
                    print()
                    print(f"INFO: Shops.get_3p_order_items - try else png")
                    image_url_split = item["image_url"].split(".png")
                    item_image_url = (
                        f"{image_url_split[0]}_256x.png{image_url_split[1]}"
                    )
                else:
                    item_image_url = "https://media.istockphoto.com/id/1147544807/es/vector/no-imagen-en-miniatura-gr%C3%A1fico-vectorial.jpg?s=1024x1024&w=is&k=20&c=jMNMEtHs4WCgUd9WCoR2gcKdD0UAOFoTROlutZRWNLE="
            except IndexError:
                print(f"INFO: Shops.get_3p_order_items - except")
                try:
                    print(f"INFO: Shops.get_3p_order_items - except try")
                    first_split = item["image_url"].split("?v")
                    base, version = first_split[0], first_split[1]
                    formatless_base, format = (
                        ".".join(base.split(".")[:-1]),
                        base.split(".")[-1],
                    )
                    item_image_url = f"{formatless_base}_256x.{format}?v{version}"
                except:
                    item_image_url = "https://media.istockphoto.com/id/1147544807/es/vector/no-imagen-en-miniatura-gr%C3%A1fico-vectorial.jpg?s=1024x1024&w=is&k=20&c=jMNMEtHs4WCgUd9WCoR2gcKdD0UAOFoTROlutZRWNLE="
            print(f"OUT: {item_image_url}")

            line_item = {
                "item_name": item["name"],
                "item_product": item["product"],
                "item_variants": item["variant"],
                "item_vendor": manufacturer,
                "item_quantity": item["quantity"],
                "item_order_number": item["item_order_number"],
                "item_unit_price": item["price"],
                "item_img_url": item_image_url,
            }

            all_line_items.append(line_item)

        return all_line_items



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

        self.nodek_api_session = shopify.Session(SHOP_URL, "2023-10", TOKEN)
        shopify.ShopifyResource.activate_session(self.nodek_api_session)


