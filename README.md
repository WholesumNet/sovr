# Sovr
## Intro
Sovr is an attempt to integrate the Golem network's compute prowess into the FairOS-dfs and the Swarm network. The whole idea revolves around the concept of compute pods.  With the help of Swarm and dfs the user is in charge of all the stuff required to run a DApp. This project is a small step towards the goal of a sophisticated sovereign exosystem where the incentives of a DApp beat those of centralized/cloud apps. An ocean to a man-made pond is what a dapp are to a capp.  
A compute pod is a directory structure containing a `recipe` file, `script`, `payload`, `ouput`, and `log` folders. Here's a sample recipe file:  
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
The `name` property identifies the pod within the dfs. The `public` property is used to share the pod with others. The `golem` property directs how the inputs and outputs of a typical golem session are going to be interacted with. The `exec` property is used to invoke the golem tooling which will use the stuff from the `script` and `payload` properties. The `output` and `log` contain the outputs of a compute session.  
## How to run?
You would need Swarm, FairOS-dfs and the Golem toolsets.  
- Get Swarm node and dfs server up and running as outlined here https://docs.fairos.fairdatasociety.org/docs/  
- Get Golem tools up and running from here https://handbook.golem.network/requestor-tutorials/flash-tutorial-of-requestor-development
- Get a virtual environment and install necessary libraries. You'd need typical ones like `yapapi`, `requests`, ...
- Make sure the `foo/logs` folder exists and then invoke `python3 cli.py --recipe foo/recipe.json --run`
- Once Golem is done, observe the contents of the `foo/log` and `foo/output`. Now you can save your compute pod on the dfs with `python3 cli.py --recipe foo/recipe.json --persist`, 
note that if your recipe file has set the `public` property to `true`, then you'd get a `sharing reference key` that you can pass to the `--fork` command or your friends.  


Another way to start is to fork a template Blender project already shared by us. Invoke `python3 cli.py --fork 2f06c9e6e1a682351104b44f0b6f44714c3d1657ca4e4f03876fbb851913cd76` and wait for it to be pulled into your dfs account and then unpacked inside your current working directory.  
Note that the network should be configured to point to `goerli` endpoints.

## Demo
https://www.youtube.com/watch?v=zRPUyUw-5Ek

