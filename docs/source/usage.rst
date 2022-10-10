Usage
=====

.. _installation:

Prerequisites
-------------
There are few steps that need to be done before using the CLI:

- **Swarm**
  To setup the Swarm node, you need to consult https://docs.ethswarm.org/docs. Once your node is up, fund your wallet(you can request funds from Swarm discord), deploy a chequebook, and bingo! 
- **FairOS-DFS**
  To setup the FairOS-DFS tools, You need two files: `dfs-linux...` and `dfs-cli-linux...` which can be downloaded from https://github.com/fairDataSociety/fairOS-dfs. Please consult https://docs.fairos.fairdatasociety.org/docs/fairOS-dfs/introduction for further information on customizing FairOS-DFS.
  FairOS-DFS provides abstractions that facilitate the storage of fairly complex objects on Swarm so it needs a running Swarm node. Once the Swarm node and a FairOS-DFS server are up, you need to create a user(assuming the FairOS-DFS tools are located at `./bee`):
    Fire the dfs-cli:
    .. code-block:: console

      ./bee/dfs-cli-linux-[*your arch*]
    And then create a user:
    .. code-block:: console

      user new *alice*
    Provide a password for the new user and the initial setup is complete. 

- **Golem**
 Golem is needed to run compute pods, so please consult https://handbook.golem.network/requestor-tutorials/flash-tutorial-of-requestor-development to set it up.

Now that you have a working environment for Swarm, FairOS-DFS, and Golem, it is time to start using the Sovr CLI.

CLI
---
Before use Sovr CLI, you need to have a virtual environment set up and activated with required libraries, make sure `requests-toolbelts` and `yapapi` are installed.
To get the Sovr CLI, fork it from Github:

.. code-block:: console

  git clone https://github.com/LickliderCircle/sovr.git

If you needed help, just invoke Sovr CLI with `--help` argument:
.. code-block:: console
  >  usage: cli.py [-h] [--recipe RECIPE] [--persist-self]
                [--persist | --fork FORK | --run | --import-pod IMPORT_POD | --list-pods | --generate-pod-registry | --task TASK]

  >  Sovr command line interface

  >   optional arguments:
  >    -h, --help            show this help message and exit
  >    --recipe RECIPE       specify a recipe file
  >    --persist-self        Persist the CLI itself and make it public. Caution:
  >                          remove any credentials(password files, ...) before
  >                          proceeding.
  >    --persist             Persist pod to dfs
  >    --fork FORK           Fork a public pod, a reference key is expected
  >    --run                 Run the pod
  >    --import-pod IMPORT_POD
  >                          Imports a pod to local filesystem, a pod name is
  >                          expected
  >    --list-pods           List all pods
  >    --generate-pod-registry
  >                          Generate a new pod registry by looking into all pods
  >    --task TASK           Fork, import, and finally run all compute pods
  >                          requested in a task description file, a task
  >                          description file is expected.
