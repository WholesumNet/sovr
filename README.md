# Sovr
## Introduction
Sovr integrates the Golem network's compute prowess into the FairOS-DFS and the Swarm network's storage facilities. The whole idea revolves around the concept of compute pods. A compute pod is simply a set of files that define how a Golem task should run, what are the inputs, outputs, and finally where the logs are going to be held. All these files are finally stored in decentralized storage of the DFS and Swarm. The tool that is in charge of persisting, sharing, and running compute pods is the Sovr CLI.  
A compute pod is a directory structure containing a `recipe` file. This recipe described in a JSON file and determines the various properties of a compute pod. Here's a sample recipe file:  
<pre>
"recipe.json":
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
- The `name` property identifies the pod within the DFS. 
- The `public` property indicates whether to share the pod with others. 
- The `golem` property defines Golem specific stuff with the `exec` preperty being the executable command to run the pod, the `script` property defining the directory that contains the actual Golem script files, the `payload` property defining the directory that contains the input files, the `output` property defining the folder that gets the output of a Golem session run, and finally the `logs` property defining the folder where the logs are stored. To facilitate compute pods' communication, a pod can expect to receive the payload from another publicly shared pod. To enable this, change the `payload` property to look as follows:
<pre>
  "golem": {
    .
    .
    .
    "payload": {
      "refs": [
        "ej38b1...",
        "1a20fd...",
        .
        .
        .
      ],
    },
    .
    .
    .
  },  
</pre>
Once the compute is going to be ran, the payload is fetched and put into the `payload/external` directory and ready to be used. Note that a compute pod can use several external public pods as payload, hence the `refs` array. To add symmetry to this scheme, the output of a compute pod can also be shared when persisting a pod. To enable this, change the `output` property to look as follows:
<pre>
  "golem": {
    .
    .
    .
    "output": {
      "share": "output/results",      
    },
    .
    .
    .
  },  
</pre>
The `output/results` directory is then shared(when persisting) as a standalone pod ready to be used by other compute pods. One of the consequences of compute pods' communication, is the emergence of more interesting ways of computing. This brings us to the notion of tasks.  
## Tasks
A task is a sequence of compute pods with podN's output feeding into podN+1's payload, enabling more complex models of computation. The following figure demonstrates a typical task consisting of 4 individual compute pods:  
<p align="center">
  <img src="https://raw.githubusercontent.com/LickliderCircle/sovr/main/docs/assets/task.png" />  
</p>
Here each compute pod could receive the payload from previous compute pod's `output`, any public pod, and the stuff already in its `payload` directory. A task is described in a task description JSON file with the following structure:  
<pre>
"some-seq.json"
{
  "name": "some sequence",
  "pods": [
    "96dd1...59670",
    "e3f8c...55eb4"
  ]
}
</pre>  
Here the `pods` property expects an array of public compute pods' references. To start a task simply invoke the CLI with `--task some-seq.json`. Each compute pod of the task is then fetched and run sequentially until the output of the whole taks is ready in the `output` directory of the last pod.  

## Prerequisites
The Sovr CLI requires Swarm, FairOS-DFS, and the Golem tooling:
- To setup the Swarm node please consult https://docs.ethswarm.org/docs/  
- To setup the FairOS-DFS, please consult https://docs.fairos.fairdatasociety.org/docs/fairOS-dfs/introduction  
If you are not familiar with the Docker system, please use the binaries as they are rather easier to set up.  
- To setup Golem, please consult https://handbook.golem.network/requestor-tutorials/flash-tutorial-of-requestor-development  

Once the Swarm node(a light node is sufficient) and the FairOS-DFS server are up, you can start working with Sovr CLI.  
You would also need a valid account within the DFS environment. To create one, please open the DFS-CLI(usually found as `dfs-cli-amd64`, ...) and use the `user new` command. Remember to save the credentials after you've created your user.  
Note that the Swarm and DFS nodes should be configured to point to the `goerli` endpoints.

## Where to get Sovr CLI?
Initially, Sovr is available here and you can just fork this repository and start.  

## How to run?
- Make sure you have the right credentials for the FairOS-DFS account. CLI expects a `creds.json` file in the `src` folder with the following data:  
  <pre>
  {
    "username": "foo",
    "password": "bar"
  }
  </pre>  
- Get a virtual environment and install necessary libraries. You'd need typical ones like `yapapi`, `requests`, `requests-toolbelt`...  
- To get you started, we have prepared some templates in the `src/pods/templates` and `src/templates/tasks` directories that you can use right away. For example, to run the Blender task on Golem, get Golem's Yagna server up, initialize it(all documented with the Golem docs shared aboved), and invoke `python3 src/cli.py --recipe src/templates/pods/blender/recipe.json --run`  
- Once Golem task is finished, observe the contents of the `src/templates/pods/blender/logs` and `src/templates/pods/blender/output`. Now that you have run your task on Golem, it's time to save it on DFS. To save your compute pod, invoke `python3 src/cli.py --recipe src/templates/pods/blender/recipe.json --persist`.  Under the hood, Swarm and DFS sort things out and save your stuff. Please note that if your recipe file has set the `public` property to `true`, your pod gets shared publicly and you receive a `reference key`.  
- Once persisted, a compute pod resides within DFS until it gets garbage collected. Meanwhile, you can share your `reference key` with anyone who can in turn spin up the CLI and fork your compute pod using the `--fork` option.  

## CLI 
<pre>
usage: cli.py [-h] [--recipe RECIPE] [--persist-self]
              [--persist | --fork FORK | --run | --import-pod IMPORT_POD | --list-pods | --generate-pod-registry | --task TASK]

Sovr command line interface

optional arguments:
  -h, --help            show this help message and exit
  --recipe RECIPE       specify a recipe file
  --persist-self        Persist the CLI itself and make it public. Caution:
                        remove any credentials(password files, ...) before
                        proceeding.
  --persist             Persist pod to dfs
  --fork FORK           Fork a public pod, a reference key is expected
  --run                 Run the pod
  --import-pod IMPORT_POD
                        Imports a pod to local filesystem, a pod name is
                        expected
  --list-pods           List all pods
  --generate-pod-registry
                        Generate a new pod registry by looking into all pods
  --task TASK           Fork, import, and finally run all compute pods
                        requested in a task description file, a task
                        description file is expected.
</pre>
