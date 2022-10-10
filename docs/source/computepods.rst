Compute Pods
============
Overview
--------
Golem is a peer-to-peer compute marketplace where requestors and providers are matched together in a decentralised way. A typical program on Golem is usually a set of ``payload(inputs)``, ``scripts``, ``logs``, and ``outputs`` with scripts controlling the logic of the whole running session. Note that this is a loose definition of a Golem program as there is no pre-defined structure and developers are free to layout their program files in any manner way the wish, but for the sake of tidiness lets agree on an informal layout for Golem programs here where 4 directories, mentioned above, constitute a Golem program.

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

The description of recipe properties, although clear, is provided here:

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

How to run
^^^^^^^^^^

Tasks
-----

How to run
^^^^^^^^^^

   
