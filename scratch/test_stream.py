import os
from supabase import create_client, Client
import requests
import json

url: str = "https://doyxtvzfwjauhsfblxez.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRveXh0dnpmd2phdWhzZmJseGV6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE0ODQ4MjksImV4cCI6MjA5NzA2MDgyOX0.BwD1P0z_ZkPndN0GZ4H_mX874nED_Jc4zM_5lXJOh3Y"
supabase: Client = create_client(url, key)

res = supabase.auth.sign_in_with_password({"email": "test2@example.com", "password": "password123"})
access_token = res.session.access_token

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

data = {
    "message": "how can we use flutter globally",
    "session_id": "dashboard-session-flutter",
    "course_name": "Flutter & Dart"
}

response = requests.post(f"{url}/functions/v1/chat", headers=headers, json=data, stream=True)
print("Status:", response.status_code)
for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
