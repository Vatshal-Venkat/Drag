import requests

url = "http://127.0.0.1:8000/ingest/file"

with open("test.jpg", "wb") as f:
    f.write(b"fake image data")

files = {'file': ('test.jpg', open('test.jpg', 'rb'), 'image/jpeg')}
data = {'session_id': 'test_session'}

response = requests.post(url, files=files, data=data)
print("Status:", response.status_code)
print("Response:", response.text)
