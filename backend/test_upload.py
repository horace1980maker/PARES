import requests, os

url = 'http://127.0.0.1:8001/subir-pdf'
file_path = os.path.join('backend', 'dummy.pdf')
with open(file_path, 'rb') as f:
    files = {'archivo': f}
    # No additional fields; defaults will be used
    response = requests.post(url, files=files)
    print('Status code:', response.status_code)
    print('Response JSON:', response.json())
