import os
import time

import requests
from dotenv import dotenv_values

BASE_URL = dotenv_values(".env").get("BASE_URL")


def get_access_token():
    expires = int(os.getenv("EXPIRES", 0))

    if expires <= int(time.time()):
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "client_id": os.environ["CLIENT_ID"],
            "client_secret": os.environ["CLIENT_SECRET"],
            "grant_type": "client_credentials",
        }
        response = requests.post(os.environ["AUTH_URL"], headers=headers, data=payload)
        response.raise_for_status()
        content = response.json()
        os.environ["ACCESS_TOKEN"] = content["access_token"]
        os.environ["EXPIRES"] = str(content["expires"])
    return os.environ["ACCESS_TOKEN"]


def get_headers():
    access_token = get_access_token()
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


def get_products():
    response = requests.get(f"{BASE_URL}/products", headers=get_headers())
    response.raise_for_status()
    products = response.json()["data"]
    return {p["name"]: p["id"] for p in products}


def get_product(item_id):
    response = requests.get(f"{BASE_URL}/products/{item_id}", headers=get_headers())
    response.raise_for_status()
    return response.json()["data"]


def get_cart(cart_ref):
    response = requests.get(f"{BASE_URL}/carts/{cart_ref}", headers=get_headers())
    response.raise_for_status()
    return response.json()["data"]


def add_to_cart(cart, item_id, quantity):
    payload = {
        "id": item_id,
        "type": "cart_item",
        "quantity": int(quantity),
    }
    response = requests.post(
        f"{BASE_URL}/carts/{cart}/items",
        headers=get_headers(),
        json={"data": payload},
    )
    response.raise_for_status()
    return


def remove_from_cart(cart, item_id):
    response = requests.delete(
        f"{BASE_URL}/carts/{cart}/items/{item_id}", headers=get_headers()
    )
    response.raise_for_status()
    return


def get_cart_items(cart):
    response = requests.get(f"{BASE_URL}/carts/{cart}/items", headers=get_headers())
    response.raise_for_status()
    return response.json()


def get_file_link(file_id):
    response = requests.get(f"{BASE_URL}/files/{file_id}", headers=get_headers())
    response.raise_for_status()
    return response.json()["data"]["link"]["href"]


def create_customer(name, email):
    payload = {
        "type": "customer",
        "name": name,
        "email": email,
    }
    response = requests.post(
        f"{BASE_URL}/customers",
        headers=get_headers(),
        json={"data": payload},
    )
    response.raise_for_status()
    return response.json()["data"]["id"]


def find_customer(email):
    payload = {"filter": f"eq(email,{email})"}
    response = requests.get(
        f"{BASE_URL}/customers", headers=get_headers(), params=payload
    )
    response.raise_for_status()
    return response.json()["data"]


def get_customers():
    response = requests.get(f"{BASE_URL}/customers", headers=get_headers())
    response.raise_for_status()
    return response.json()["data"]
