Compute Pods
============
Overview
--------
Golem is a peer-to-peer compute marketplace where requestors and providers are matched together in a decentralised way. A typical program on Golem is usually a set of ``payload(inputs)``, ``scripts``, ``logs``, and ``outputs`` with *scripts* controlling the logic of the whole running session. Note that this is a loose definition of a Golem program as there is no pre-defined structure and developers are free to layout their program files in any manner way the wish, but for the sake of tidiness lets agree on an informal layout for Golem programs here where 4 directories, mentioned above, constitute a Golem program.

A compute pod is a `logical directory structure <https://docs.fairos.fairdatasociety.org/docs/fairOS-dfs/introduction#pod--logical-drive>`_ that contains directories and files representing a program that can be run on Golem. To differentiate a compute pod from typical pods, recall that users might have other pods in their wallet too, a ``.recipe`` file is stored at the root of the compute pods, e.g. ``/segmentation-job.recipe``. A recipe is a json file with the following look and feel:

.. code-block:: text

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

- ``name``
  
  This property identifies the compute pod within the FairOS-DFS and thus should be unique for every compute pod.

- ``description``

  A description of the objective of the compute pod

- ``author``

  The author of the compute pod

- ``version``

  Version number

- ``public``

  Whether the compute pod should be shared with others

- ``golem``

  Defines a Golem program

  - ``exec``

    The command that starts a Golem session run  

  - ``script``

    The logic of the Golem program is out here

  - ``payload``

    Defines the payload(input) of the Golem program

  - ``output``

    The output of the Golem program 

  - ``log``

    The logs of any Golem session runs


Compute Pods
------------
Compute pods are the main building block of the Sovr Protocol and provide an easy to use scheme to manage Golem compute objects. Compute pods can be run, persisted, shared, and forked by users in a decentralized way. This allows them to be viewed as portable compute objects. Compute pods might experience various independent stages during their lifetime:

- *Running*

  A running compute pod is simply a Golem program. An example of running is shown below:

  .. code-block:: console

    python src/cli.py --recipe src/templates/pods/blender/recipe.py --run


- *Persisting*

  A compute pod can be persisted to the FairOS-DFS with the ``--persist`` option of CLI. When persisting, if the ``public`` property of the recipe is set to **True**, the compute pod is also shared to the outside world. An example of persisting is shown below: 

  .. code-block:: console

    python src/cli.py --recipe src/templates/pods/blender/recipe.py --persist

- *Forking*

  Forking is the opposite of persisting and as its name implies, brings a public pod to the user, allowing her to build upon other people's work. ``--fork`` option is employed to fork compute pods. an example of forking is shown below:

  .. code-block:: console

    python src/cli.py --fork 2cf98c3...23ee9a

Besides working with compute pods, Sovr CLI provide means to maintain the overall auditing and maintenance of itself and compute pods. ``--persist-self`` for exaample, persists a copy of the CLI(the ``src/`` directory) on Swarm and shares it as a measure of redundancy. Another set of options revolve around the maintenance of compute pods with ``--list-pods`` providing a list of current compute pods and ``--generate-pod-registry`` creating a registry of compute pods as users could have several other pods too.

Payload and output
^^^^^^^^^^^^^^^^^^
The notion of *payload* is very important for compute pods as it provides means to communicate with other compute pods. A recipe defines what payload the compute pod expects and there are two types of payloads: internal, and external. An internal payload is simply set of files stored in the ``payload`` property's value's directory while an external paylaod is a set of references to public pods. The following snippet defines an external payload:

.. code-block:: text

  "golem": {
    .
    .
    .
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
  }, 

As you can see the paylaod requires external stuff stored on public pods that need to be forked before a compute pod could run. This is taken care of by the Sovr CLI when running starts by downlaoding the external payload into the ``paylaod/external`` direcory.
Once the compute pod is ready to be persisted, the recipe could demand the output to be shared too. An example of a output sharing is given below:

.. code-block:: text

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

This brings us to the point where the need to chain tasks is felt.

Tasks
-----
A task is 

Quick dive
^^^^^^^^^^

   
