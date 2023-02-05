# Sovr
Sovr integrates the Golem network's compute prowess into the FairOS-DFS and the Swarm network's storage facilities. The whole idea revolves around the concept of compute pods. A compute pod is simply a set of files that define how a Golem task should run, what are the inputs, outputs, and finally where the logs are going to be held. All these files are finally stored in decentralized storage of the DFS and Swarm. The tool that is in charge of persisting, sharing, and running compute pods is the Sovr CLI.  

## Documentation
Documentation is available at: http://sovr.rtfd.io/  

## Motives
There is an essay about current efforts and future directions of computers here: https://github.com/rezahsnz/lure/blob/main/lure.pdf

## CLI 
<pre>
usage: cli.py [-h] [--init] [--recipe RECIPE] [--persist-self]
              [--persist | --fork FORK | --run | --import-pod IMPORT_POD | --list-pods | --generate-pod-registry]

Sovr command line interface

optional arguments:
  -h, --help            show this help message and exit
  --init                Walks you through a wizard to initialize a new pod or
                        task.
  --recipe RECIPE       Specify a recipe file
  --persist-self        Persist the CLI itself and make it public. Caution:
                        remove any credentials(password files, ...) before
                        proceeding.
  --persist             Persist pod to dfs
  --fork FORK           Fork a public pod, a reference key is expected
  --run                 Run the pod/task
  --import-pod IMPORT_POD
                        Imports a pod to local filesystem, a pod name is
                        expected
  --list-pods           List all pods
  --generate-pod-registry
                        Generate a new pod registry by looking into all pods

</pre>
