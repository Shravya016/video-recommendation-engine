import os
import requests
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()
FLIC_TOKEN = os.getenv("FLIC_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL")

def make_api_call(endpoint: str, params: dict = None):
    headers = {"Flic-Token": FLIC_TOKEN}
    url = f"{API_BASE_URL}/{endpoint}"
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="API call failed")
    return response.json()

def fetch_paginated_data(endpoint: str, key: str, extra_params: dict = None):
    page = 1
    page_size = 1000
    all_data = []
    while True:
        params = {"page": page, "page_size": page_size}
        if extra_params:
            params.update(extra_params)
        data = make_api_call(endpoint, params)
        items = data.get(key, [])
        all_data.extend(items)
        if len(items) < page_size:
            break
        page += 1
    return all_data

def fetch_all_users():
    return fetch_paginated_data("users/get_all", "users")

def fetch_all_posts():
    return fetch_paginated_data("posts/summary/get", "posts")

def fetch_interactions(interaction_type: str):
    endpoint_map = {
        "view": "posts/view",
        "like": "posts/like",
        "inspire": "posts/inspire",
        "rate": "posts/rating"
    }
    endpoint = endpoint_map.get(interaction_type)
    if not endpoint:
        raise ValueError("Invalid interaction type")
    params = {"resonance_algorithm": "resonance_algorithm_cjsvervb7dbhss8bdrj89s44jfjdbsjd0xnjkbvuire8zcjwerui3njfbvsujc5if"}
    return fetch_paginated_data(endpoint, "interactions", params)