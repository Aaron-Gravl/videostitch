import requests

url = "http://127.0.0.1:5000/process"
payload = {
    "hooks": ["hook1.mp4", "hook2.mp4"],
    "bodies": ["body1.mp4", "body2.mp4"],
    "ctas": ["cta1.mp4", "cta2.mp4"]
}

response = requests.post(url, json=payload)
print(response.json())
