import urllib
import requests

BASE_ADDRESS = 'http://localhost:9090/v1'

def login(_username: str, _password: str) -> str :  
  ''' 
  login to dfs server
  '''
  response = requests.post(
    f'{BASE_ADDRESS}/user/login',
    json = {
      'user_name': _username,
      'password': _password
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