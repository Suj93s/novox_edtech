import requests
import json
import os

url = "https://doyxtvzfwjauhsfblxez.supabase.co/functions/v1/chat"
headers = {
    "Content-Type": "application/json"
}
# We don't have a valid auth token easily, so this will get 401. 
# Wait, let's just run it to see if it's reachable.
res = requests.post(url, headers=headers, json={"message": "hello", "session_id": "123"})
print(res.status_code)
print(res.text)
