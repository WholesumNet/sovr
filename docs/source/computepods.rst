Compute Pods
============
Overview
--------
Golem is a peer-to-peer compute marketplace where requestors(those who need to get some compute done) and providers(those who provide their computer in exchange for $) are matched together in a decentralised way. A typical program on Golem is usually a set of ``payload(inputs)``, ``scripts``, ``logs``, and ``outputs`` with *scripts* controlling the logic of the whole running session. Note however that this is a loose definition of a Golem program as there is no such pre-defined structure and developers are free to layout their program files in any manner the wish and the layout Sovr uses is only for the sake of tidiness. 

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


What is a Compute Pod?
----------------------
A compute pod is the main building block of the Sovr Protocol that provide an easy to use scheme to manage Golem compute session. Compute pods can be run, persisted, shared, and forked by users in a decentralized way. This allows them to be viewed as portable compute objects. Compute pods might experience various independent stages during their lifetime:

- *Running*

  A running compute pod is simply a Golem program. An example of running a compute pod via Sovr CLI is shown below:

  .. code-block:: console

    python src/cli.py --recipe src/templates/pods/blender/recipe.py --run


- *Persisting*

  A compute pod can be saved(persisted) to the FairOS-DFS with the ``--persist`` option of Sovr CLI. When persisting, if the ``public`` property of the recipe is set to **True**, the compute pod is also shared to the outside world. An example of persisting is shown below: 

  .. code-block:: console

    python src/cli.py --recipe src/templates/pods/blender/recipe.py --persist

- *Forking*

  Forking is the opposite of persisting and as its name implies, brings a public pod to the user, allowing her to build upon other people's work. ``--fork`` option is employed to fork compute pods. an example of forking is shown below:

  .. code-block:: console

    python src/cli.py --fork 2cf98c3...23ee9a

Besides working with compute pods, Sovr CLI provides means to maintain the overall status of itself and compute pods. ``--persist-self`` for example, persists a copy of Sovr CLI(the ``src/`` directory) on Swarm and shares it as a measure of redundancy. Another set of options revolve around the maintenance of compute pods with ``--list-pods`` providing a list of current compute pods and ``--generate-pod-registry`` creating a registry of compute pods as users could have several other pods too and it is important to track compute pods down.

Payload and output
^^^^^^^^^^^^^^^^^^
The notion of *payload* is very important for a compute pod as it provides means to communicate with other compute pods. A recipe defines what payload the compute pod expects. There are two types of payloads: *internal*, and *external*. An internal payload is simply the set of local files stored in the ``payload`` property's directory while an external paylaod is a set of references to public pods. The following snippet shows and example of an external payload:

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

As you can see the paylaod requires external resource stored on public pods that need to be forked before a compute pod could use them. This is taken care of by the Sovr CLI when running a compute pod. All external payloads are stored in the ``paylaod/external`` direcory.
Once a compute pod is ready to be persisted, the recipe could ask for its output to be shared. An example of a output sharing is given below:

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

The message of computes pod is simple yet powerful. Using compute pods, people can autmate things and build on top of others' work.

Tasks
-----
A *task* is a set of independent compute pods loosely chained together to undertake a complex job. The following image demonstrates a visual conception of tasks.
  
  .. image:: https://raw.githubusercontent.com/LickliderCircle/sovr/main/docs/assets/task.png

A task is defined in a json file and has the following look and feel:

.. code-block:: text

  {
    "name": "some sequence",
    "pods": [
      "96dd1...59670",
      "e3f8c...55eb4"
    ]
  }

Where the ``pods`` property defines a list of compute pods that constitute the task. To run a task you can invoke the Sovr CLI as below:

.. code-block:: console

  python src/cli.py --task foo/task.json

Running a task involves forking and running individual compute pods. After each compute pod is run, the contents of the *output* is copied to the next compute pod's *paylaod/external* directory, thus enabling dependency of compute pods to each other. To get your feet wet with tasks, there is an example task in ``src/templates/tasks/ml/keras/task.json`` where 5 images are sent to different pre-trained Keras models to be classified.


Quick dive
----------
To make this introduction to compute pods solid, an example is provided here that let's you run and examine a compute pod we have already persisted in Swarm.

1. Set up a user within the FairOS-DFS environment
  We assume that FairOS-DFS tools are located at **./bee/** and our system's architecture is the common 64-bit "x86_64" known as *amd64*
  
  - Open a terminal window and run(replace the postage block id Swarm gave you with *foobar*)

    .. code-block:: console

      ./bee/dfs-linux-amd64 server --postageBlockId "foobar"

  - In another terminal tab/window, run

    .. code-block:: console

      ./bee/dfs-cli-linux-amd64

    Now that you are inside the FairOS-DFS CLI, let's create a user named *sam* or name it as you like
    
    .. code-block:: console

      user new sam

    Provide a password for *sam* and exit the FairOS-DFS CLI.

  - Open your favourite text editor and write the following text in it then save it in the Sovr CLI's ``src`` directory(I hope you've already clonned Sovr CLI, if not please consult :doc:`usage`) as ``creds.json``.

    .. code-block:: text

      {
        "username": "sam",
        "password": "sam's password"
      }

2. Set Golem up as described here :doc:`usage`

3. Fork, run, and persist a compute pod
  While in the same terminal tab/window, make sure you are at Sovr CLI's directory ``sovr`` and the virtual environment you set up at :doc:`usage` is activated.
  
  - To fork a compute pod containing a `XCeption` Keras image classification model, run

    .. code-block:: console

      python src/cli.py --fork a61d11e7335ed41e56494ae4bee5446f7785737938a35454e3190c5ccae283ea

    Once the forking is complete, you would have ``XCeption`` directory at your current woking directory, feel free to explore it.

  - To run the forked `XCeption` compute pod, run

    .. code-block:: console

      python src/cli.py --recipe src/XCeption/recipe.py --run

    This will send your compute pod's stuff to Golem nodes and once done, your compute pod's results are ready at ``XCeption/outupt`` along with any logs at ``XCeption/logs``. For this specific compute pod, the actual result is ``XCeption/output/preds.json`` which is the top 5 classes the model thought the five input images are.

  - If you are satisfied with the outputs or just interested in saving your compute pod on Swarm, run

    .. code-block:: console

      python src/cli.py --recipe src/XCeption/recipe.py --persist

    If there are no harmless errors, you should get a message on the successful persistence of your compute pod along with a sharing reference key if your recipe's ``public`` property was *True*. 

Congrats, you have completed your very first compute pod journey!

As an alternative to forking, there are some template compute pods and tasks in the ``src/templates`` directory, feel free to examine them. 












  
