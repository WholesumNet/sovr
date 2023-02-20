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
  persist compute pod/task to DFS
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
  print('Uploading pod...')
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
      print(f'Failed to share the pod, status_code: {response.status_code}, message: {response.json()["message"]}')  
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
  # share output of the compute pod
  if recipe.get('golem'):
    output = recipe['golem']['output']
    if type(output) == dict:
      '''
      Share a subdir of the output as a public pod
      .
      .
      .
      "golem": {
        "exec": "python3 script/blender.py",
        "script": "script",
        "payload": {
          "pod": "ej38x1...1a20fd",
          "files": ["/aloha/mahalo.blend"]
        },
        "output": {
          "share": "output/actuals"
        },
        "log": "logs"
      }
      .
      .
      .
      '''
      output_pod_name = 'output-' + pod_name
      helpers.remove_file(f'./{output_pod_name}.zip')
      output_share_dir = pathlib.Path(f'{_recipe_path}/{output["share"]}').resolve()
      shutil.make_archive(f'{output_pod_name}', 'zip', f'{output_share_dir}')
      helpers.new_pod(_cookie = _cookie, _password = creds['password'],
                      _pod_name = output_pod_name)
      helpers.open_pod(_cookie = _cookie, _password = creds['password'],
                       _pod_name = output_pod_name)    
      res = helpers.upload_file(_cookie = _cookie, _pod_name = output_pod_name,
                                _pod_dir = '/', _local_filepath = f'./{output_pod_name}.zip')
      if res['status_code'] != 200:
        print(f'Failed to share the output, status_code: {res["status_code"]}, message: {res["message"]}')    


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

def importExternalPayload(_cookie: str,
                          _password: str,
                          _where: str,
                          _payload: list) -> dict:
  ''' 
  Fork and import the payload
  A typical recipe with external payload:
   .
   .
   .
   "golem": {
    "exec": "python3 script/blender.py",
    "script": "script",
    "payload": [
      {
        "ref": "ej38b1...",
        "data": "/data.zip"
      },
      {
        "ref": "1a20fd...",
        "data": "/jake/lime.zip"
      },
      .
      .
      .
    ],
    },
    .
    .
    .
  '''
  if type(_payload) is not list:
    return 
  shutil.rmtree(path = f'{_where}/payload/external', ignore_errors = True)  
  try:
    os.mkdir(f'{_where}/payload/external')
  except:
    pass
  for p in _payload:
    ref = p['ref']
    ext_data = p['data']
    print(f'Importing External payload `{ref}`...')
    pod_info = fork(_cookie = _cookie, _password = _password,
                    _reference = ref, _where = _where, _should_import = False)
    if not pod_info:
      print('Failed to import the payload.')
      continue
    pod_name = pod_info['pod_name']
    helpers.open_pod(_cookie = _cookie, _pod_name = pod_name,
                     _password = _password)    
    external_path = f'{_where}/payload/external/'
    external_zip = f'{_where}/payload/external/{ref}.zip'    
    helpers.download_file(_cookie = _cookie, _pod_name = pod_name,
                          _from = f'{ext_data}',
                          _to = external_zip)
    # add the external payload to the payload/external/ref directory
    shutil.unpack_archive(external_zip,
                          external_path)
    helpers.remove_file(external_zip)

def importPod(_cookie: str,
              _password: str,
              _pod_name: str,
              _where: str = '.') -> None:
  '''
  download a pod into the local filesystem
  '''
  print(f'Importing pod `{_pod_name}`...')
  helpers.remove_file(f'{_where}/{_pod_name}.zip')
  helpers.open_pod(_cookie = _cookie, _pod_name = _pod_name, _password = _password)
  helpers.download_file(_cookie = _cookie, _pod_name = _pod_name,
                        _from = f'/{_pod_name}.zip',
                        _to = f'{_where}/{_pod_name}.zip')
  if not os.path.exists(f'{_where}/{_pod_name}.zip'):
    print('Import failed.')
    return  
  shutil.unpack_archive(f'{_where}/{_pod_name}.zip', f'{_where}/{_pod_name}')
  helpers.remove_file(f'{_where}/{_pod_name}.zip')  
  print(f'Pod is ready at `{_where}/{_pod_name}` directory, ' \
        f'now it can be run with\n' \
        f'`python cli.py --recipe {_where}/{_pod_name}/{_pod_name}.recipe --run`')

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

def runPod(_cookie: str,
           _password: str, 
           _recipe: dict, 
           _base_path: str = '.') -> None:
  '''
  Runs a compute pod on Golem
  '''
  if not _recipe: 
    print('Invalid recipe.')
    return
  print(f'base path: `{_base_path}`')
  golem = _recipe['golem']
  # fork and import payload if it is an external dependency
  importExternalPayload(_cookie = _cookie, _password = _password,
                        _where = _base_path, _payload = golem['payload'])

  command = [item.replace('[@]', f'{_base_path}/')
             for item in golem["exec"].split(' ')]
  # command[-1] = f'{_base_path}/{command[-1]}'
  print(f'Running pod `{" ".join(command)}`...')
  proc = subprocess.Popen(command)  
  proc.wait()
  print(f'Exit code: {proc.returncode}')
  print('Pod execution finished.')

def fork(_cookie: str,
         _password: str,
         _reference: str,
         _where: str = '.',
         _should_import: bool = True) -> None:
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
    pp = pprint.PrettyPrinter()    
    pp.pprint(pod_info)
  else:
    print(f'Failed to get any info about the pod. status_code: {response.status_code}, message: {response.json()["message"]}')
    return None

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
    print(f'Failed to fork the pod, status_code: `{response.status_code}`, message: `{response.json()["message"]}`')

  if _should_import:
    importPod(_cookie = _cookie, _password = _password,
              _pod_name = pod_info['pod_name'], _where = _where)
  return pod_info

def runTask(_cookie: str,
            _password: str,
            _task: dict,
            _base_path: str = '.') -> None:
  '''
  Given a task recipe file with the following structure, run compute pods
  one by one.
  {
    "name": "ML pipeline",
    "payload": [
      {
        "ref": "a09bb8f37nf72d72739vj7lcn16bxw6xkw9xw983ep00eabx2",
        "data": "/images.zip"
      }
    ],
    "pods": ["0xAA...AA", "0xBB...BB", ..., "0xZZ...ZZ"]
    .
    .
    .
  }
  '''
  task_name = _task['name']
  print(f'Running task `{task_name}`...')
  # try:
  #   os.mkdir(f'{_base_path}/{task_name}')
  # except:
  #   pass
  # copy external payload to each pod
  if _task.get('payload'):
    importExternalPayload(_cookie = _cookie, _password = _password,
                          _where = _base_path, _payload = _task['payload'])
  prev_output = None
  for pod_ref in _task['pods']:
    # fork
    pod_info = fork(_cookie = _cookie, _password = _password,
                    _reference = pod_ref, _where = _base_path)
    if not pod_info:
      print('Failed to finish task completely, forking was problematic.')
      return
    pod_name = pod_info['pod_name']
    recipe = None
    recipe_path = f'{_base_path}/{pod_name}/recipe.json'
    with open(recipe_path, 'r') as f:
      recipe = json.loads(f.read())
    if not recipe:
      print('Failed to finish task completely, recipe file '
            '`{recipe_path}` appears to be invalid.')
      return   
    # copy the output of the previous pod into the current pod
    # shutil.rmtree(path = f'{_base_path}/{pod_name}/payload/external', 
    #               ignore_errors = True)
    # put shared external paylaod
    if _task.get('payload'):
      shutil.copytree(src = f'{_base_path}/payload/external',
      dst = f'{_base_path}/{pod_name}/payload/external',
      dirs_exist_ok = True)
    if prev_output is not None:
      shutil.copytree(src = prev_output,
                      dst = f'{_base_path}/{pod_name}/payload/external',
                      dirs_exist_ok = True)
    runPod(_cookie = _cookie, _password = _password,
           _recipe = recipe, _base_path = f'{_base_path}/{pod_name}')
    prev_output = f'{_base_path}/{pod_name}/output'
  print(f'Task finished and the output is available at `{prev_output}`')      

# <-- Entry point: Main -->
if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Sovr command line interface')
  group = parser.add_mutually_exclusive_group()
  parser.add_argument('--init', action='store_true',
                      help = 'Walks you through a wizard to initialize a new pod or task.')
  parser.add_argument('--recipe',
                      help = 'Specify a recipe file')
  parser.add_argument('--persist-self', action = 'store_true',
                      help = 'Persist the CLI itself and make it public. Caution: remove any credentials(password files, ...) before proceeding.')
  group.add_argument('--persist', action = 'store_true',
                      help = 'Persist pod to dfs')
  group.add_argument('--fork',
                      help = 'Fork a public pod, a reference key is expected')  
  group.add_argument('--run', action = 'store_true',
                      help = 'Run the pod/task')
  group.add_argument('--import-pod',
                     help = 'Imports a pod to local filesystem, a pod name is expected')
  group.add_argument('--list-pods', action = 'store_true',
                     help = 'List all pods')  
  group.add_argument('--generate-pod-registry', action = 'store_true',
                     help = 'Generate a new pod registry by looking into all pods')
  #group.add_argument('--task',
  #                   help = 'Fork, import, and finally run all compute pods requested in a task description file, a task description file is expected.')
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
    fork(_cookie = cookie, _password = creds['password'],
         _reference = args.fork.strip())

  elif args.run:
    recipe_path = f'{pathlib.Path(args.recipe).parent.resolve()}'
    if recipe.get('golem'):
      runPod(_cookie = cookie, _password = creds['password'],
             _recipe = recipe, _base_path = recipe_path)
    elif recipe['pods']:
      runTask(_cookie = cookie, _password = creds['password'],
              _task = recipe, _base_path = recipe_path)
    else:
      print('No valid recipe for a compute pod or a task was provided.')

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

  elif args.init:
    print('This wizard walks you through the initialization of an empty Pod or Task.\n'
          'Please remember that you can consult documentation at `https://http://sovr.rtfd.io`\n'
          'Invalid answers will resolve to default values.\n'
          'You will be asked a few questions, so let us begin.')
    user_input = input('Is it a `pod` or a `task`? (default value is `pod`): ').lower()
    is_pod = False if user_input == 'task' else True
    project_type = 'Pod' if is_pod else 'Task'
    project_name = input(f'Enter a name for your {project_type}: ')
    project_desc = input(f'Enter the description for your {project_type}: ')
    project_author = input(f'Enter the name of the author of your {project_type}: ')
    user_input = input(f'Enter the version of your {project_type}, default value is `1.0`: ')
    project_version = '1.0' if user_input == '' else user_input
    user_input = input(f'Should your {project_type} be `public`? (default is `yes`): ').lower()
    is_public = False if user_input == 'no' else True
    if is_pod:
      print('Now we are going to fill in the `Golem` properties of the Pod.')
      golem_exec = input(f'What is the `exec` command to run the pod: ')
      user_input = input('Do you have any external payloads? (default is `no`): ').lower()
      payload_is_external = True if user_input == 'yes' else False
      external_payloads = []
      if payload_is_external:
        payload_number = 1
        payload_ref = input(f'Enter the reference key of the payload `{payload_number}` (empty aborts): ').lower()
        paylaod_data_path = input(f'Enter the path of the data within the Pod`: ').lower()        
        while payload_ref is not '':
          external_payloads.append({
              'ref': payload_ref.strip(),
              'data': paylaod_data_path.strip()})
          payload_number = payload_number + 1
          payload_ref = input(f'Enter the reference key of the Pod containing the payload `{payload_number}`, (empty aborts): ').lower()
          paylaod_data_path = input(f'Enter the path of the data within the Pod`: ').lower()
      pod_recipe = {
        'name': project_name.strip(),
        'description': project_desc,
        'author': project_author,
        'version': project_version,
        'public': is_public,
        'golem': {
          'exec': golem_exec,
          'payload': 'payload' if not payload_is_external else external_payloads,
          'output': 'output',
          'logs': 'logs'
        }
      }
      try:
        os.mkdir(f'./{project_name}')
        os.mkdir(f'./{project_name}/logs')
        os.mkdir(f'./{project_name}/output')
        os.mkdir(f'./{project_name}/payload')
      except:
        pass
      with open(f'./{project_name}/recipe.json', 'w') as f:
        f.write(json.dumps(pod_recipe, indent=2))      
      print(f'Pod recipe is saved at `./{project_name}/recipe.json`')
    else:
      user_input = input('Do you have any external payloads? (default is `no`): ').lower()
      payload_is_external = True if user_input == 'yes' else False
      external_payloads = []
      if payload_is_external:
        payload_number = 1
        payload_ref = input(f'Enter the reference key of the payload `{payload_number}`, (empty aborts): ').lower()
        while payload_ref is not '':
          external_payloads.append(payload_ref.strip())
          payload_number = payload_number + 1
          payload_ref = input(f'Enter the reference key of the Pod containing the payload `{payload_number}`, (empty aborts): ').lower()
      task_recipe = {
        'name': project_name.strip(),
        'description': project_desc,
        'author': project_author,
        'version': project_version,
        'public': is_public,
        'pods': external_payloads
      }
      try:
        os.mkdir(f'./{project_name}')
      except:
        pass
      with open(f'./{project_name}/recipe.json', 'w') as f:
        f.write(json.dumps(task_recipe, indent=2))      
      print(f'Task recipe is saved at `./{project_name}/recipe.json`')      
    
  #elif args.task:
  #  task_path = f'{pathlib.Path(args.task).parent.resolve()}'
  #  task = None
  #  with open(args.task, "r") as f:
  #    task = json.loads(f.read())
  #  if task:
  #    runTask(_cookie = cookie, _password = creds['password'],
  #            _task = task, _base_path = task_path)
  #  else:
  #    print('Could not start the task, please make sure the task description file is fine.')
  else:
    print('Nothing to be done.')
  
