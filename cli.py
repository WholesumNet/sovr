import os
import sys
import json
import argparse
import urllib
import requests
from requests.structures import CaseInsensitiveDict
from requests_toolbelt.multipart.encoder import MultipartEncoder
import subprocess
import shutil

BASE_ADDRESS = 'http://localhost:9090/v1'
Headers = {}

PodRegistry = 'ComputePodRegistry'
PodRegistryFilePath = "Registry.json"

def login(username: str, password: str) -> str :  
  ''' 
  login to dfs server
  '''
  response = requests.post(
    f'{BASE_ADDRESS}/user/login',
    json = {
      'user_name': username,
      'password': password
    },
    headers = {'content-type': 'application/json'}
  )
  cookie = None
  if response.status_code != 200:    
    print(f'Authentication failed, status_code: `{response.status_code}`, message: `{response.json()["message"]}\n`'
          f'Please check `creds.json` file and try again.')    
  else:
    cookie = response.headers['Set-Cookie']
  return cookie

def open_pod(cookie: str, pod_name: str, password: str) -> None:
  '''
  open a pod
  '''
  response = requests.post(
    f'{BASE_ADDRESS}/pod/open',
    headers = CaseInsensitiveDict([
      ('Cookie', cookie),
    ]),
    json = {
      'pod_name': pod_name,
      'password': password
    },
  )
  if response.status_code != 200:    
    print(f'Pod could not be openned. status_code: `{response.status_code}, message: `{response.json()["message"]}`')

def download_file(_cookie: str, _pod_name: str,
                  _from: str, _to: str) -> None: 
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
      'Cookie': cookie
    }
    # headers = CaseInsensitiveDict([
    #   ('Cookie', _cookie),
    #   ('content-type', 'application/json')
    # ]),
    # json = {
    #   'pod_name': _pod_name,
    #   'file_path': _from
    # },
  )
  if response.status_code != 200:   
    print(f'Download failed, status_code: {response.status_code}, message: {response.json()["message"]}')
    return
  with open(_to, 'wb') as f:
      f.write(response.content)  
  print(f'Download successed and saved to `{_to}`.')

def upload_file(cookie: str, pod_name: str, pod_dir: str,
                local_filepath: str) -> dict :
  '''
  upload a file to dfs
  '''
  print(f'Uploading `{local_filepath}`...')
  mp_encoder = MultipartEncoder(
    fields = {
      'pod_name': pod_name,
      'dir_path': pod_dir,
      'block_size': '64000', # 64 kb
      'files': (os.path.basename(local_filepath), open(local_filepath, 'rb')),
    }
  )
  response = requests.post(
    f'{BASE_ADDRESS}/file/upload',
    data = mp_encoder,
    headers = {
      'Content-Type': mp_encoder.content_type,
      'Cookie': cookie
    }
  )  
  return {
    'status_code': response.status_code,
    'message': response.json()['message'] if response.status_code != 200 else ''
  }

def remove_file(_what: str) -> None:
  if os.path.exists(_what):
    os.remove(_what) 

def persist(recipe: dict, cookie: str, password: str) -> None:
  '''
  persist compute pod on the FDS and register it
  '''
  if not recipe: 
    return
  # create a pod and open it
  pod_name = recipe['name']
  print(f'Persisting pod `{pod_name}`...')
  headers = CaseInsensitiveDict([
    ('Cookie', cookie),
    ('content-type', 'application/json'),
  ])
  response = requests.post(
    f'{BASE_ADDRESS}/pod/new',
    headers = headers,
    json = {
      'pod_name': pod_name,
      'password': password
    },
  )
  if response.status_code != 201:
    print(f'Pod creation failed, ignore this if pod is being updated.' \
          f' status_code: `{response.status_code}`, message: `{response.json()["message"]}`')
  open_pod(cookie = cookie, pod_name = pod_name, password = creds['password'])
  # zip and upload 
  print('Uploading pod...')
  shutil.make_archive(f'{pod_name}', 'zip', f'./{pod_name}')
  res = upload_file(cookie = cookie, pod_name = pod_name,
                    pod_dir = '/', local_filepath = f'./{pod_name}.zip')
  if res['status_code'] != 200:
    print(f'Failed to persist pod, status_code: {res["status_code"]}, message: {res["message"]}')
    return    
  
  # let's share
  if recipe.get('public'):
    print('Sharing pod...')
    response = requests.post(
      f'{BASE_ADDRESS}/pod/share',
      headers = headers,
      json = {
        'pod_name': pod_name,
        'password': password
      },
    )
    if response.status_code == 200:
      print(f'Pod is now public. For future forks, please note this reference key: ' \
            f'`{response.json()["pod_sharing_reference"]}`')
    else:
      print(f'Failed to share the pod, status_code: {response.status_code}, message: {respons.json()["message"]}')  
  
  # register it in the pod registry
  # pod registry is a json file that holds a list of all pods persisted
  print('Registering pod...')
  print('Attempting to create the pod registry, may fail if already created.')
  response = requests.post(
      f'{BASE_ADDRESS}/pod/new',
      headers = headers,
      json = {
        'pod_name': PodRegistry,
        'password': password
      },
    )
  if response.status_code != 201: 
    print(f'Failed to create the pod registry. status_code: `{response.status_code}`' \
          f', message: `{response.json()["message"]}`')
  open_pod(cookie = cookie, pod_name = PodRegistry, password = creds['password'])

  # download registry, load it, update it, and save it back
  remove_file(f'./{PodRegistryFilePath}')  
  download_file(_cookie = cookie, _pod_name = PodRegistry,
                _from = f'/{PodRegistryFilePath}',
                _to = f'./{PodRegistryFilePath}')
  
  pod_registry = {}
  if os.path.exists(f'./{PodRegistryFilePath}'):
    with open(f'./{PodRegistryFilePath}', 'r') as f:
      pod_registry = json.loads(f.read())
  pod_registry[pod_name] = recipe
  with open(f'./{PodRegistryFilePath}', 'w') as f:
    f.write(json.dumps(pod_registry))
  res = upload_file(cookie = cookie, pod_name = PodRegistry,
                    pod_dir = '/', local_filepath = f'{PodRegistryFilePath}')
  if res['status_code'] == 200:
    print("Pod registered successfully.")
  else:
    print(f'Registration failed. status_code: `{upload_status_code}`, message: `{res["message"]}`')

def pods(_cookie: str, _password: str) -> dict:
  '''
  get all pods
  '''
  remove_file(f'./{PodRegistryFilePath}')
  open_pod(cookie = _cookie, pod_name = PodRegistry, password = _password)
  download_file(_cookie = cookie, _pod_name = PodRegistry,
                _from = f'/{PodRegistryFilePath}',
                _to = f'./{PodRegistryFilePath}')    
  pod_registry = None
  if os.path.exists(f'./{PodRegistryFilePath}'):
    with open(f'./{PodRegistryFilePath}', 'r') as f:
      pod_registry = json.loads(f.read())  
  else:
    print('No pods were found in the registry. If you think the pod registry is' \
          ' corrupted, please consult the --fix-registry option in the help.')
  return pod_registry

def importPod(_cookie: str, _password: str, _pod_name: str) -> None:
  '''
  download a pod into local filesystem
  '''
  print(f'Importing pod `{_pod_name}`...')
  remove_file(f'./{_pod_name}.zip')
  open_pod(cookie = _cookie, pod_name = _pod_name, password = _password)
  download_file(_cookie = _cookie, _pod_name = _pod_name,
                _from = f'/{_pod_name}.zip',
                _to = f'./{_pod_name}.zip')
  if not os.path.exists(f'./{_pod_name}.zip'):
    print('Import failed.')
    return  
  shutil.unpack_archive(f'{_pod_name}.zip', '.', 'zip')
  print(f'Pod is ready at `{_pod_name}` directory, ' \
        f'now it can be run with\n' \
        f'`python cli.py --recipe {_pod_name}/{_pod_name}.recipe --run`')

def runPod(recipe: dict) -> None:
  '''
  Runs a compute pod on Golem
  '''
  if not recipe: 
    return
  golem = recipe['golem']
  command = f'{golem["exec"]}'.split(' ')
  command[-1] = f'{recipe["name"]}/{command[-1]}'
  print(f'Running pod {command}...')
  proc = subprocess.Popen(command)  
  proc.wait()
  print(f'Exit code: {proc.returncode}')
  print('Pod execution finished.')

def fork(_cookie: str, _password: str, _reference: str) -> None:
  '''
  Fork a public pod
  '''
  pod_info = {}
  print(f'Forking public pod `{_reference}`...')
  print('Requesting pod info...')
  response = requests.get(
    f'{BASE_ADDRESS}/pod/receiveinfo',
    headers = CaseInsensitiveDict([
      ('Cookie', _cookie),
    ]),
    params = {
      'sharing_ref': _reference,
    },
  )
  if response.status_code == 200:
    pod_info = response.json()
    print(f'Got some info about the pod: {pod_info}')
  else:
    print(f'Failed to get any info about the pod. status_code: {response.status_code}, message: {response.json()["message"]}')
    return

  response = requests.get(
    f'{BASE_ADDRESS}/pod/receive',
    headers = CaseInsensitiveDict([
      ('Cookie', _cookie),
    ]),
    params = {
      'sharing_ref': _reference,
    },
  )
  if response.status_code == 200:
    print(f'Pod forked successfully.')
  else:    
    print(f'Failed to fork pod, status_code: `{response.status_code}`, message: `{response.json()["message"]}`')
    return

  # open pod
  importPod(_cookie = _cookie, _password = _password, _pod_name = pod_info['pod_name'])

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Sovr command line interface')
  group = parser.add_mutually_exclusive_group()
  parser.add_argument('--recipe',
                      help = 'specify a recipe file')
  group.add_argument('--persist', action = 'store_true',
                      help = 'Persist pod to dfs')
  group.add_argument('--fork',
                      help = 'Fork a public pod, a reference key is expected')  
  group.add_argument('--run', action = 'store_true',
                      help = 'Run the pod')
  group.add_argument('--import-pod',
                     help = 'Imports a pod to local filesystem, a pod name is expected')
  group.add_argument('--list-pods', action = 'store_true',
                     help = 'List all pods')
  args = parser.parse_args()
  
  creds = None
  with open('./creds.json', 'r') as f:
    creds = json.loads(f.read())
  if not creds:
    print(
    """
      No credential file was found, please provide a
      `creds.json` file with the following format:
      
      {
       "username": "foo",
       "password": "bar"
      }

      Where "username" and "password" are valid within the FairOS-DFS.      
    """)
    exit()
  
  # login
  cookie = login(creds['username'], creds['password'])
  if not cookie:
    exit() 
  print('Successfully logged in.')

  # import recipe, if any  
  recipe = {}
  if args.recipe:
    with open(args.recipe, 'r') as f:
      recipe = json.loads(f.read())  
  # if not recipe:
  #   print(
  #   """
  #   Warning: No recipe file was provided, a typical recipe file is as follows:

  #   {
  #     "name": "blender",
  #     "description": "Blender requestor pod that renders a .blend file.",
  #     "version": "1.0",
  #     "author": "greenpepe",
  #     "public": true,
  #     "golem": {
  #       "exec": "python3 script/blender.py",
  #       "script": "script",
  #       "payload": "payload",
  #       "output": "output",
  #       "log": "logs"
  #     }
  #   }
  #   """)
  if args.persist:
    persist(recipe, cookie, creds['password'])  
  elif args.fork:
    fork(args.fork, cookie, creds['password'])
  elif args.run:
    runPod(recipe)
  elif args.import_pod:
    importPod(_cookie = cookie, _password = creds['password'], _pod_name = args.import_pod)
  elif args.list_pods:
    pod_registry = pods(_cookie = cookie, _password = creds['password'])
    print(pod_registry)
  else:
    print('Nothing to be done.')
  
