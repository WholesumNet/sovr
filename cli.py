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

BASE_ADDRESS = "http://localhost:9090/v1"

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
  if response.status_code == 200:
    return response.headers['Set-Cookie']
  else:
    print('status_code: {}'.format(response.status_code))
    return None

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
  if response.status_code == 200:
    print('pod openned successfully.')
  else:
    print('status_code: {}'.format(response.status_code))  

def upload_file(cookie: str, pod_name: str, pod_dir: str, local_filepath: str) -> None :
  '''
  Upload a file to dfs
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
  if response.status_code == 200:
    print(f'Completed successfully.')
  else:
    print(f'Failed with status code of {response.status_code}.')

def persist(recipe: dict, cookie: str, password: str) -> None:
  '''
  makes a copy of the compute pod on Swarm
  '''
  if not recipe: 
    return
  print('Persisting the compute pod to dfs...')
  # create a pod and open it
  headers = CaseInsensitiveDict([
    ('Cookie', cookie),
    ('content-type', 'application/json'),
  ])
  response = requests.post(
    f'{BASE_ADDRESS}/pod/new',
    headers = headers,
    json = {
      'pod_name': recipe['name'],
      'password': password
    },
  )
  if response.status_code == 200:
    print('pod created successfully.')
  else:
    print('status_code: {}'.format(response.status_code))
  open_pod(cookie = cookie, pod_name = recipe['name'], password = creds['password'])  
  # zip and upload 
  print('Uploading pod...')
  shutil.make_archive(f'{recipe["name"]}', 'zip', f'./{recipe["name"]}')
  upload_file(cookie = cookie, pod_name = recipe['name'],
              pod_dir = '/', local_filepath = f'./{recipe["name"]}.zip')
  print('Done.')
  
  # share
  if recipe.get('public'):
    print('Sharing the pod...')
    response = requests.post(
      f'{BASE_ADDRESS}/pod/share',
      headers = headers,
      json = {
        'pod_name': recipe['name'],
        'password': password
      },
    )
    if response.status_code == 200:
      print(f'Pod is public now. To fork, please note this reference down: {response.json()["pod_sharing_reference"]}')
    else:
      print('status_code: {}'.format(response.status_code))  
    print('Done.')

def run_pod(recipe: dict) -> None:
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

def fork(reference: str, cookie: str, password: str) -> None:
  '''
  Fork a public pod
  '''
  pod_info = {}
  print('Forking pod...')
  print('Requesting pod info...')
  response = requests.get(
    f'{BASE_ADDRESS}/pod/receiveinfo',
    headers = CaseInsensitiveDict([
      ('Cookie', cookie),
    ]),
    params = {
      'sharing_ref': reference,
    },
  )
  if response.status_code == 200:
    pod_info = response.json()
    print(f'Pod info received: {pod_info}')
  else:
    print('status_code: {}'.format(response.status_code))
    print(f'No info for `{reference}` pod.')
    return

  print('Forking pod...')
  response = requests.get(
    f'{BASE_ADDRESS}/pod/receive',
    headers = CaseInsensitiveDict([
      ('Cookie', cookie),
    ]),
    params = {
      'sharing_ref': reference,
    },
  )
  if response.status_code == 200:
    print(f'Pod forked successfully.')
  else:
    print('status_code: {}'.format(response.status_code))
    print(f'Failed to fork/receive `{reference}` pod.')
    return

  # open pod
  pod_name = pod_info['pod_name']
  open_pod(cookie = cookie, pod_name = pod_name, password = password)
  # download it
  response = requests.get(
    f'{BASE_ADDRESS}/file/download',
    headers = CaseInsensitiveDict([
      ('Cookie', cookie),
      ('content-type', 'application/json')
    ]),
    json = {
      'pod_name': pod_name,
      'file_path': f'/{pod_name}.zip'
    },
  )
  if response.status_code == 200:
    print(f'Pod downloaded successfully.')
  else:
    print('status_code: {}'.format(response.status_code))
    print(f'Failed to download `{reference}` pod.')
    return
  # unpck and bingo!
  shutil.unpack_archive(f'{pod_name}.zip', '.', 'zip')
  print(f'Pod is ready at {pod_name} directory!, ' \
        f'now it can be run with\n' \
        f'`python cli.py --recipe {pod_name}/{pod_name}.recipe --run`')

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Sovr command line interface')
  parser.add_argument('--recipe', help = 'specify a recipe file')
  parser.add_argument('--persist', action = 'store_true', help = 'Persist pod to dfs')
  parser.add_argument('--fork', help = 'Fork a public pod, reference is expected')  
  parser.add_argument('--run', action='store_true', help = 'Run the pod')
  args = vars(parser.parse_args())
  
  creds = None
  with open('./creds.json', 'r') as f:
    creds = json.loads(f.read())
  
  # login
  cookie = login(creds['username'], creds['password'])
  if not cookie:
    print('Authentication failed, please check `creds.json` file.')
    exit() 
  print('Successfully logged in.')

  # import recipe, if any
  '''
  A typical recipe:
  {
    "name": "blender",
    "description": "Blender requestor pod that renders a .blend file.",
    "version": "1.0",
    "author": "greenpepe",
    "public": true,
    "golem": {
      "exec": "python3 script/blender.py",
      "script": "script",
      "payload": "payload",
      "output": "output",
      "log": "logs"
    }
  }
  '''  
  recipe = {}
  if args['recipe']:
    with open(args['recipe'], 'r') as f:
      recipe = json.loads(f.read())  
  if not recipe:
    print('Warning: invalid recipe.')
  # persist  
  if args['persist']:
    persist(recipe, cookie, creds['password'])  
  # fork the pod
  if args['fork']:
    fork(args['fork'], cookie, creds['password'])
  # run the pod    
  if args['run']:
    run_pod(recipe)
  
