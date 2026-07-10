import os

import requests
from dotenv import load_dotenv


load_dotenv()

PROFILE_URL = "https://api.dhan.co/v2/profile"


def get_profile() -> dict:
    access_token = os.getenv("DHAN_ACCESS_TOKEN")

    if not access_token:
        raise RuntimeError("DHAN_ACCESS_TOKEN .env file me missing hai.")

    response = requests.get(
        PROFILE_URL,
        headers={
            "access-token": access_token,
            "Accept": "application/json",
        },
        timeout=15,
    )

    try:
        data = response.json()
    except ValueError:
        data = {
            "error": "Dhan ne valid JSON response nahi diya.",
            "status_code": response.status_code,
        }

    if response.status_code != 200:
        raise RuntimeError(
            f"Dhan API error {response.status_code}: {data}"
        )

    return data
