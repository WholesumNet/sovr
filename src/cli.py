import os
import pathlib
import sys
import json
import argparse
import urllib
import requests
from requests.structures import CaseInsensitiveDict
from requests_toolbelt.multipart.encoder import MultipartEncoder
import subprocess
import shutil
import pprint

import helpers
import auth

BASE_ADDRESS = 'http://localhost:9090/v1'

PodRegistry = 'ComputePodRegistry'
PodRegistryFilePath = 'Registry.json'

SharedPodsPod = 'SharedPods'
SharedPodsFilePath = 'SharedPods.json'

def persist_self(_cookie: str,
                 _password: str) -> None:
  '''
  Persist self to dfs
  '''
  pod_name = 'Sovr'
  print(f'Persisting pod `{pod_name}`...')
  headers = CaseInsensitiveDict([
    ('Cookie', _cookie),
    ('content-type', 'application/json'),
  ])
  
  helpers.new_pod(_cookie = _cookie, _password = creds['password'],
                  _pod_name = pod_name)
  helpers.open_pod(_cookie = _cookie, _password = creds['password'],
                   _pod_name = pod_name)
  # zip and upload 
  print('Uploading pod...')
  sovr_dir = pathlib.Path(__file__).parent.resolve()
  shutil.make_archive(f'{pod_name}', 'zip', f'{sovr_dir}')
  res = helpers.upload_file(_cookie = _cookie, _pod_name = pod_name,
                            _pod_dir = '/', _local_filepath = f'./{pod_name}.zip')
  if res['status_code'] != 200:
    print(f'Failed to persist pod, status_code: {res["status_code"]}, message: {res["message"]}')
    return       
  # let's share
  response = requests.post(
    f'{BASE_ADDRESS}/pod/share',
    headers = headers,
    json = {
      'pod_name': pod_name,
      'password': _password
    },
  )
  if response.status_code == 200:
    print(f'Pod is now public. For future forks, please note this reference key: ' \
          f'`{response.json()["pod_sharing_reference"]}`')
  else:
    print(f'Failed to share the pod, status_code: {response.status_code}, message: {respons.json()["message"]}')  

  


def persist(_recipe: dict,
            _recipe_path: str,
            _cookie: str,
            _password: str) -> None:
  '''
  persist compute pod on the FDS and register it
  '''
  if not _recipe: 
    return
  # create pod and open it
  pod_name = _recipe['name']
  print(f'Persisting pod `{pod_name}`...')
  headers = CaseInsensitiveDict([
    ('Cookie', _cookie),
    ('content-type', 'application/json'),
  ])
  
  helpers.new_pod(_cookie = _cookie, _password = creds['password'],
                  _pod_name = pod_name)
  helpers.open_pod(_cookie = _cookie, _password = creds['password'],
                   _pod_name = pod_name)
  # zip and upload 
  print('Uploading pods...')
  recipe_dir = pathlib.Path(_recipe_path).parent.resolve()
  shutil.make_archive(f'{pod_name}', 'zip', f'{recipe_dir}')
  res = helpers.upload_file(_cookie = _cookie, _pod_name = pod_name,
                            _pod_dir = '/', _local_filepath = f'./{pod_name}.zip')
  if res['status_code'] != 200:
    print(f'Failed to persist pod, status_code: {res["status_code"]}, message: {res["message"]}')
    return    
  # upload recipe.json to the root of the pod, handy for later pod discovery
  helpers.upload_file(_cookie = cookie, _pod_name = pod_name,
                      _pod_dir = '/', _local_filepath = f'{recipe_dir}/recipe.json')
  helpers.remove_file(f'./{pod_name}.zip')
  # let's share
  if _recipe.get('public'):
    print('Sharing pod...')
    response = requests.post(
      f'{BASE_ADDRESS}/pod/share',
      headers = headers,
      json = {
        'pod_name': pod_name,
        'password': _password
      },
    )
    if response.status_code != 200:
      print(f'Failed to share the pod, status_code: {response.status_code}, message: {respons.json()["message"]}')  
    else:
      sharing_reference = response.json()['pod_sharing_reference']
      print(f'Pod is now public. For future forks, please note this sharing reference: ' \
            f'`{sharing_reference}`')
      # keep track of the shared pods
      print('Keeping track of the shared pod...')
      helpers.new_pod(_cookie = _cookie, _password = creds['password'],
                       _pod_name = SharedPodsPod)
      helpers.open_pod(_cookie = _cookie, _password = creds['password'],
                       _pod_name = SharedPodsPod)
      # download shared pods list, update it, and save it back
      content = helpers.download_content(_cookie = cookie, _pod_name = SharedPodsPod,
                                         _from = f'/{SharedPodsFilePath}')
      shared_pods = json.loads(content.decode('utf-8')) if content else {}      
      pod_list = shared_pods[pod_name] if pod_name in shared_pods else []      
      pod_list.append({
        'recipe': _recipe,
        'sharing_reference': sharing_reference
        })
      shared_pods[pod_name] = pod_list
      with open(f'./{SharedPodsFilePath}', 'w') as f:
        f.write(json.dumps(shared_pods))
      res = helpers.upload_file(_cookie = _cookie, _pod_name = SharedPodsPod,
                                _pod_dir = '/', _local_filepath = f'./{SharedPodsFilePath}')
      if res['status_code'] == 200:
        print(f'The shared pod is being tracked.')
      else:
        print(f'Failed to keep track of this shared pod. status_code: `{upload_status_code}`, message: `{res["message"]}`')
      helpers.remove_file(f'./{SharedPodsFilePath}')     
  
  # pod registry is a json file that holds a list of all persisted pods
  print('Registering pod...')
  helpers.new_pod(_cookie = _cookie, _password = creds['password'],
                   _pod_name = PodRegistry)
  helpers.open_pod(_cookie = _cookie, _password = creds['password'],
                   _pod_name = PodRegistry)

  # download registry, update it, and save it back
  content = helpers.download_content(_cookie = cookie, _pod_name = PodRegistry,
                                     _from = f'/{PodRegistryFilePath}')
  pod_registry = json.loads(content.decode('utf-8')) if content else {}
  pod_registry[pod_name] = _recipe
  with open(f'./{PodRegistryFilePath}', 'w') as f:
    f.write(json.dumps(pod_registry))
  res = helpers.upload_file(_cookie = _cookie, _pod_name = PodRegistry,
                            _pod_dir = '/', _local_filepath = f'./{PodRegistryFilePath}')
  if res['status_code'] == 200:
    print("Pod registered successfully.")
  else:
    print(f'Registration failed. status_code: `{upload_status_code}`, message: `{res["message"]}`')
  helpers.remove_file(f'./{PodRegistryFilePath}')  

def pods(_cookie: str,
        _password: str) -> dict:
  '''
  retrieve all pods
  '''
  helpers.remove_file(f'./{PodRegistryFilePath}')
  helpers.open_pod(_cookie = _cookie, _pod_name = PodRegistry, _password = _password)
  content = helpers.download_content(_cookie = _cookie, _pod_name = PodRegistry,
                                     _from = f'/{PodRegistryFilePath}')
  pod_registry = json.loads(content.decode('utf-8')) if content else {} 
  # get sharing stat
  helpers.open_pod(_cookie = _cookie, _pod_name = SharedPodsPod, _password = _password)
  content = helpers.download_content(_cookie = _cookie, _pod_name = SharedPodsPod,
                                     _from = f'/{SharedPodsFilePath}')
  shared_pods = json.loads(content.decode('utf-8')) if content else {}
  for (key, value) in shared_pods.items():
    if key in pod_registry:
      pod_registry[key]['sharing_references'] = [p['sharing_reference'] for p in value]
  return pod_registry

def importPod(_cookie: str,
              _password: str,
              _pod_name: str) -> None:
  '''
  download a pod into local filesystem
  '''
  print(f'Importing pod `{_pod_name}`...')
  helpers.remove_file(f'./{_pod_name}.zip')
  helpers.open_pod(_cookie = _cookie, _pod_name = _pod_name, _password = _password)
  helpers.download_file(_cookie = _cookie, _pod_name = _pod_name,
                        _from = f'/{_pod_name}.zip',
                        _to = f'./{_pod_name}.zip')
  if not os.path.exists(f'./{_pod_name}.zip'):
    print('Import failed.')
    return  
  shutil.unpack_archive(f'{_pod_name}.zip', f'./{_pod_name}', 'zip')
  helpers.remove_file(f'./{_pod_name}.zip')
  print(f'Pod is ready at ./`{_pod_name}` directory, ' \
        f'now it can be run with\n' \
        f'`python cli.py --recipe {_pod_name}/{_pod_name}.recipe --run`')

def generatePodRegistry(_cookie: str,
                        _password: str) -> None:
  '''
  Generate pod registry by examinig all pods and adding those with a
  `recipe.json` file at the `/` directory to the registry
  '''
  print('Generating pod registry...')
  headers = CaseInsensitiveDict([
    ('Cookie', _cookie),
    ('content-type', 'application/json'),
  ])
  response = requests.get(
      f'{BASE_ADDRESS}/pod/ls',
      headers = headers,      
    )
  if response.status_code != 200: 
    print(f'Failed to get the list of pods. status_code: `{response.status_code}`' \
          f', message: `{response.json()["message"]}`')
    return

  pod_registry = {}
  for pod_name in response.json()['pod_name']:
    print(f'Examining `{pod_name}`...')
    helpers.open_pod(_cookie = _cookie, _password = _password, _pod_name = pod_name)
    content = helpers.download_content(_cookie = _cookie, _pod_name = pod_name,
                                       _from = '/recipe.json')
    # pass 1: just look for /recipe.json
    if not content:
      print(f'`{pod_name}` is not a compute pod.')
      continue
    recipe = json.loads(content.decode('utf-8'))  
    # @ pass 2: open pod_name.zip and look into it
    # add it to the pod registry
    print(f'{pod_name} is a valid compute and will be added to the registry.')
    pod_registry[pod_name] = recipe

  print('Pod registry: ')
  pp = pprint.PrettyPrinter()    
  for r in pod_registry.values():
    pp.pprint(r)
  print(f'Total pods found: {len(pod_registry)}')
  with open(f'./{PodRegistryFilePath}', 'w') as f:
    f.write(json.dumps(pod_registry))
  # upload the new pod registry to dfs
  helpers.new_pod(_cookie = _cookie, _password = creds['password'],
                   _pod_name = PodRegistry)
  helpers.open_pod(_cookie = _cookie, _password = creds['password'],
                   _pod_name = PodRegistry)
  res = helpers.upload_file(_cookie = _cookie, _pod_name = PodRegistry,
                            _pod_dir = '/', _local_filepath = f'./{PodRegistryFilePath}')
  if res['status_code'] == 200:
    print("Registry was saved successfully.")
  else:
    print(f'Could not save the registry. status_code: `{upload_status_code}`, message: `{res["message"]}`')
  helpers.remove_file(f'./{PodRegistryFilePath}')

def runPod(_recipe: dict) -> None:
  '''
  Runs a compute pod on Golem
  '''
  if not _recipe: 
    return
  golem = _recipe['golem']
  command = f'{golem["exec"]}'.split(' ')
  command[-1] = f'{_recipe["name"]}/{command[-1]}'
  print(f'Running pod {command}...')
  proc = subprocess.Popen(command)  
  proc.wait()
  print(f'Exit code: {proc.returncode}')
  print('Pod execution finished.')

def fork(_cookie: str,
         _password: str,
         _reference: str) -> None:
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

  importPod(_cookie = _cookie, _password = _password,
            _pod_name = pod_info['pod_name'])



if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Sovr command line interface')
  group = parser.add_mutually_exclusive_group()
  parser.add_argument('--recipe',
                      help = 'specify a recipe file')
  parser.add_argument('--persist-self', action = 'store_true',
                      help = 'Persist the CLI itself and make it public. Caution: remove any credentials(password files, ...) before proceeding.')
  parser.add_argument('--describe', action = 'store_true',
                      help = 'More help on how to get started')
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
  group.add_argument('--generate-pod-registry', action = 'store_true',
                     help = 'Generate a new pod registry by looking into all pods')
  args = parser.parse_args()
  
  creds = None  
  with open(f'{pathlib.Path(__file__).parent.resolve()}/creds.json', 'r') as f:
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
  

  if args.describe:    
    print(
    """
    Here\'s a few suggestions on how to use Sovr:    
      - Use template pods available at the `./templates` directory by
        `[--run|--persist] --recipe ./templates/blender/recipe.py`
      - Share the compute pods at the `./templates` directory; remember to set
        the `public` flag of the recipe file to `True` and then persist the pod.
      - Help spread the word by persisting the CLI itself via the 
        `--persist-self` option
      - Go hardcore and create a compute pod for yourself with a recipe that
        resembles the following schema:
        {
          "name": "blender",
          "description": "Blender requestor pod that renders a .blend file.",
          "version": "1.0",
          "author": "john",
          "public": true,
          "golem": {
            "exec": "python3 script/blender.py",
            "script": "script",
            "payload": "payload",
            "output": "output",
            "log": "logs"
          }
        }
    """)

  # login
  cookie = auth.login(creds['username'], creds['password'])
  if not cookie:
    exit() 
  print('Successfully logged in.')

  # import recipe, if any  
  recipe = {}
  if args.recipe:
    with open(args.recipe, 'r') as f:
      recipe = json.loads(f.read())

  if args.persist_self:
    persist_self(_cookie = cookie, _password = creds['password'])

  if args.persist:
    persist(_recipe = recipe, _recipe_path = args.recipe,
            _cookie = cookie, _password = creds['password']) 

  elif args.fork:
    fork(args.fork, cookie, creds['password'])

  elif args.run:
    runPod(recipe)

  elif args.import_pod:
    importPod(_cookie = cookie, _password = creds['password'],
              _pod_name = args.import_pod)

  elif args.list_pods:
    pod_registry = pods(_cookie = cookie, _password = creds['password'])
    pp = pprint.PrettyPrinter()    
    for recipe in pod_registry.values():
      pp.pprint(recipe)
    print(f'Total pods: {len(pod_registry)}')
    if len(pod_registry) == 0:
      print('No pods were found in the registry. If you think the pod registry is' \
          ' corrupted, please consult the --fix-registry option in the help.')

  elif args.generate_pod_registry:
    generatePodRegistry(_cookie = cookie, _password = creds['password'])
    
  else:
    print('Nothing to be done.')
  
