import os
import requests
from requests.structures import CaseInsensitiveDict
from requests_toolbelt.multipart.encoder import MultipartEncoder

BASE_ADDRESS = 'http://localhost:9090/v1'

def new_pod(_cookie: str,
            _pod_name: str,
            _password: str) -> None:
  '''
  Create a new pod in dfs
  '''
  response = requests.post(
        f'{BASE_ADDRESS}/pod/new',
        headers = CaseInsensitiveDict([
          ('Cookie', _cookie),
        ]),
        json = {
          'pod_name': _pod_name,
          'password': _password
        },
      )
  if response.status_code != 201: 
    print(f'Failed to create the pod. status_code: `{response.status_code}`' \
          f', message: `{response.json()["message"]}`')

def open_pod(_cookie: str,
             _pod_name: str,
             _password: str) -> None:
  '''
  Open a pod in dfs
  '''
  response = requests.post(
    f'{BASE_ADDRESS}/pod/open',
    headers = CaseInsensitiveDict([
      ('Cookie', _cookie),
    ]),
    json = {
      'pod_name': _pod_name,
      'password': _password
    },
  )
  if response.status_code != 200:    
    print(f'Pod could not be openned. status_code: `{response.status_code}, message: `{response.json()["message"]}`')

def download_content(_cookie: str,
                     _pod_name: str,
                     _from: str) -> bytes:
  '''
  Download some content from dfs
  '''
  print(f'Downloading `{_from}`...')
  mp_encoder = MultipartEncoder(
    fields = {
      'pod_name': _pod_name,
      'file_path': _from,
    }
  )
  response = requests.get(
    f'{BASE_ADDRESS}/file/download',
    data = mp_encoder,
    headers = {
      'Content-Type': mp_encoder.content_type,
      'Cookie': _cookie
    }    
  )
  content = None
  if response.status_code == 200:
    content = response.content
  else:
    print(f'Download failed, status_code: {response.status_code}, message: {response.json()["message"]}')
  return content  

def download_file(_cookie: str,
                  _pod_name: str,
                  _from: str,
                  _to: str) -> None:
  '''
  Download a file from dfs
  ''' 
  content = download_content(_cookie = _cookie, _pod_name = _pod_name,
                             _from = _from)
  if not content:
    return
  with open(_to, 'wb') as f:
      f.write(content)  
  print(f'Download succeeded and saved to `{_to}`.')

def upload_file(_cookie: str,
                _pod_name: str,
                _pod_dir: str,
                _local_filepath: str) -> dict :
  '''
  Upload a file to dfs
  '''
  print(f'Uploading `{_local_filepath}`...')
  mp_encoder = MultipartEncoder(
    fields = {
      'pod_name': _pod_name,
      'dir_path': _pod_dir,
      'block_size': '64000', # 64 kb
      'files': (os.path.basename(_local_filepath), open(_local_filepath, 'rb')),
    }
  )
  response = requests.post(
    f'{BASE_ADDRESS}/file/upload',
    data = mp_encoder,
    headers = {
      'Content-Type': mp_encoder.content_type,
      'Cookie': _cookie
    }
  )  
  return {
    'status_code': response.status_code,
    'message': response.json()['message'] if response.status_code != 200 else ''
  }

def remove_file(_what: str) -> None:
  '''
  Safe-remove a local file
  '''
  if os.path.exists(_what):
    os.remove(_what) 
