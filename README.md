# Sovr
## Intro
Sovr integrates the Golem network's compute prowess into the FairOS-DFS and the Swarm network. The whole idea revolves around the concept of compute pods. A compute pod is a set of files that provide the means to run a Golem task, save it to the  DFS, and share it with others. With the help of Swarm and  DFS, the user is in charge of all the stuff required to run a compute pod.    
A compute pod is a directory structure containing a `recipe` file. This recipe determines how the pod is managed and what to expect from. Here's a sample recipe file:  
<pre>
{
  "name": "blender",
  "description": "Blender requestor pod that renders a .blend file.",
  "version": "1.0",
  "author": "reza",
  "public": true,
  "golem": {
    "exec": "python3 script/blender.py",
    "script": "script",
    "payload": "payload",
    "output": "output",
    "log": "logs"
  }
}  
</pre>
The `name` property identifies the pod within the DFS. The `public` property indicates whether to share the pod with others. The `golem` property defines Golem specific stuff with `exec` being the executable command to run the pod, the `script` property defining the directory that contains the actual Golem script files, the `payload` property defining the directory that contains the input files, the `output` property defining the folder that gets the output of a Golem session run, and finally the `logs` property defining the folder where the logs are stored.  
## Prerequisites
The Sovr CLI requires Swarm, FairOS-DFS, and the Golem tooling:
- To setup a Swarm node please consult https://docs.ethswarm.org/docs/  
- To setup the FairOS-DFS, please consult https://docs.fairos.fairdatasociety.org/docs/fairOS-dfs/introduction  
If you are not familiar with the Docker system, please use the binaries as they are rather easier to set up.  
- To setup Golem, please consult https://handbook.golem.network/requestor-tutorials/flash-tutorial-of-requestor-development  
Once the Swarm node(a light node is sufficient) and the FairOS-DFS server are up you can start working with CLI.  
You would also need a valid account within the DFS environment. To create one, please open the DFS-CLI(usually found as `dfs-cli-amd64`, ...) and use the `user new` command. Remember to the credentials after you've created your user.

## Where to get Sovr's CLI?
Initially, Sovr is available here and you can just fork this repository and start.  

## How to run?
- Make sure you have the right credentials for the FairOS-DFS account. CLI expects a `creds.json` file in the `src` with the following data:  
  <pre>
  {
    "username": "foo",
    "password": "bar"
  }
  </pre>  
- Get a virtual environment and install necessary libraries. You'd need typical ones like `yapapi`, `requests`, `requests-toolbelt`...  
- To get you started, we have prepared some templates in the `src/templates` folder that you can use right away. For example, to run the Blender task on Golem, get Golem's Yagna server up, initialize it(all documented with the Golem docs shared aboved), and invoke `python3 src/cli.py --recipe src/templates/blender/recipe.json --run`  
- Once Golem task is finished, observe the contents of the `src/templates/blender/logs` and `src/templates/blender/output`. Now that you have run your task on Golem, it's time to save it on DFS. To save your compute pod, invoke `python3 src/cli.py --recipe foo/recipe.json --persist`.  Under the hood, Swarm and DFS sort things out and save your stuff. Please note that if your recipe file has set the `public` property to `true`, your pod gets shared publicly and you receive a `sharing reference key`.  
- Once persisted, a compute pod resides within DFS until it gets garbage collected. Meanwhile, you can share your `sharing reference key` with anyone who can in turn spin up the CLI and fork your compute pod using the `--fork` option.  
Note that the Swarm and DFS nodes should be configured to point to the `goerli` endpoints.

## Features
The CLI's `--help` and `--describe` provide enough resources for you to begin, but here we list some feaures of the CLI that might be of interest to you:
- `--persist-self` takes a copy of the `src` folder and saves it to the DFS as a public shared pod.
- `--list-pods` shows a list of all registered compute pods.
- `--import-pod` downloads a pod from DFS and puts it in the local filysystem. This is the opposite of the `--persist` option.
- `--generate-pod-registry` creates a pod registry where all compute pods of the user are managed. Each compute pod contains a .zip file and a `recipe.json` file at the `/` of the pod. This option performs a soft look up of all pods and adds them to the registry. A pod registry is necessary since each user could have tens of other pods and this way we make sure we have a soft-way of knowing what's being stored.