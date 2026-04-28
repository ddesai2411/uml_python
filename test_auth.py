#!/usr/bin/env python
# coding: utf-8

import json
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# Load config (assuming it's in the same directory or adjust path)
with open('config.ebuilder.json', 'r') as f:
    config = json.load(f)

url = config['hostname'] + "/api/v2/authenticate"

form = {
    "grant_type": "password",
    "username": config['username'],
    "password": config['password'],
}

data = urlencode(form).encode("utf-8")
req = Request(url, data=data, method="POST")
req.add_header("Content-Type", "application/x-www-form-urlencoded")

try:
    with urlopen(req, timeout=30.0) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        text = resp.read().decode(charset)
        payload = json.loads(text)
        print("Authentication successful!")
        print(f"Token type: {payload.get('token_type')}")
        expires_in = payload.get('expires_in')
        print(f"Expires in: {expires_in} seconds")
        issuance_time = time.time()
        expiration_time = issuance_time + expires_in
        print(f"Token issued at: {time.ctime(issuance_time)}")
        print(f"Token expires at: {time.ctime(expiration_time)}")
        print(f"Access token (first 20 chars): {payload.get('access_token')[:20]}...")
except HTTPError as e:
    print(f"Authentication failed with HTTP {e.code}: {e.reason}")
    try:
        body = e.read().decode("utf-8", errors="replace")
        print(f"Response body: {body}")
    except Exception:
        print("Could not read error body.")
except URLError as e:
    print(f"Network error: {e}")
except json.JSONDecodeError as e:
    print(f"Invalid JSON response: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")