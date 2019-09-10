# About

This repository contains an example loop implementation for Flowbster. The loop
itself is implemented in a component external to Flowbster - `looper`. Every
component in the example is run inside containers using Docker.

# Architecture

There are two main components participating in this example:
- the Flowbster workflow,
- the `looper` component.

## The Flowbster workflow

The workflow is really simple:
- there is a `PREPROCESS` node which receives an input file, does some
pre-processing on it (in the example, it checks if the received data is an
integer), and forwards the result to the actual processing node, `PROCESS`.
- the `PROCESS` node gets the data from `PREPROCESS`, and does the processing on
it. In the example, it decreases the value received by one, but more detailed
scenarios are also available. Finally, the results of processing are sent to the
last node, `POSTPROCESS`.
- the `POSTPROCESS` node could be used to perform any post-processing on the
results received from the `PROCESS` node. In the example, it simply copies the
data processed to the received component, `looper`.

Notes:
- the `PREPROCESS` and `POSTPROCESS` nodes can be modified to perform e.g.
database operations as necessary
- it is possible to scale the `PROCESS` node in the workflow, in this case it is
advised to make the `ṖOSTPROCESS` node a collector node, which receives the
results of the different parallel processing, so can perform the post-processing
on the different results.

## `looper` node

This component acts as a data receiver for the Flowbster workflow, and is also
an evaluator of the results. Based on the result of the workflow, it can decide
to re-submit the workflow with the intermediate result produced so far.

# Running

The following steps are necessary to run the workflow with the `looper`
component:
1. Start the `looper` component.
2. Update the Flowbster workflow configuration to use the `looper` component's
IP address as the received address.
3. Start up the infrastructure for the workflow (with Occopus).
4. Send a setup request to `looper` component with the IP address of the
`PREPROCESS` node.
5. Submit workflow.

## Start the `looper` component

As the example is using Docker, the following steps can be used to start the
`looper` component:
```
$ cd looper
$ docker build -t looper:latest .
...
$ docker run --name looper -p 6000:6000 looper:latest
 * Serving Flask app "looper" (lazy loading)
 * Environment: production
...
```

This will make the `looper` component start (using name `looper`), with its
output visible.

The IP address of the component can be queried with `docker inspect`:
```
$ docker inspect looper
[
    {
        "Id": "370846077ab33fe863a17ba5a142132c377631dcb82b126d74cd57f07360e38e",
        ...
        "NetworkSettings": {
            ...
            "IPAddress": "172.17.0.4",
            ...
    }
]
```

## Update Flowbster workflow configuration

Enter the `workflow` directory. In file `infra-flowbster-ga-wf.yaml`, change
the value of the `gather_ip` property to the IP address of the `looper`
component, e.g.:
```
...
variables:
    flowbster_global:
            gather_ip: &gatherip 172.17.0.4
...
```

## Start the workflow's infrastructure

Assuming a properly configured Occopus environment for usage with Docker,
start up the infrastructure for the workflow:
```
$ occopus-import node_defs/node_definitions.yaml
Successfully imported nodes: docker_flowbster_node
$ occopus-build infra-flowbster-ga-wf.yaml
...
** 2019-09-10 13:46:15,659	Health checking for node 'PREPROCESS'/'ce221c1b-3bdc-476e-80ad-6f7c327645a6'
** 2019-09-10 13:46:15,689	Health checking result: ready
** 2019-09-10 13:46:15,706	Health checking for node 'PROCESS'/'37104023-dabc-4948-9434-6b6d503951ce'
** 2019-09-10 13:46:15,736	Health checking result: ready
** 2019-09-10 13:46:15,753	Health checking for node 'POSTPROCESS'/'99ba3d0e-4f20-49e2-afea-7d8388fddd81'
** 2019-09-10 13:46:15,783	Health checking result: ready
** 2019-09-10 13:46:15,790	Submitted infrastructure: 'b1c5e33f-dcd4-4c26-87ea-1ea1f25e166a'
** 2019-09-10 13:46:15,805	List of nodes/ip addresses:
** 2019-09-10 13:46:15,806	PREPROCESS:
** 2019-09-10 13:46:15,806	  172.17.0.6 (ce221c1b-3bdc-476e-80ad-6f7c327645a6)
** 2019-09-10 13:46:15,806	PROCESS:
** 2019-09-10 13:46:15,806	  172.17.0.5 (37104023-dabc-4948-9434-6b6d503951ce)
** 2019-09-10 13:46:15,806	POSTPROCESS:
** 2019-09-10 13:46:15,806	  172.17.0.4 (99ba3d0e-4f20-49e2-afea-7d8388fddd81)
b1c5e33f-dcd4-4c26-87ea-1ea1f25e166a
```
In the above log the IP address of the different nodes can be found.

## Setup `looper`

With the workflow's infrastructure and `looper` running, we can tell `looper`
which IP (the IP of `PREPROCESS`) it must connect to when resubmitting the
workflow:
```
$ curl -X POST -F ip=172.17.0.6 http://172.17.0.4:6000/setup
{"message":"target IP successfully set to \"172.17.0.6\""}
```

## Submit workflow

Once every component is up and properly configured, the initial data can be
sent to the `PREPROCESS` node:
```
$ cd workflow/submit
$ ./flowbster-submit.sh -h 172.17.0.6 -i input-description-for-vina.yaml -d input-data.txt
HOSTIP : 172.17.0.6
JOBFILE : input-description-for-vina.yaml
DATAFILES: input-data.txt
Instance 1 :
Workflow instance id: 2019-09-10-13-51-46-255505-unique-id-of-the-wf
Adding input file: input-data.txt
Files: {'input-data.txt': <open file 'input-data.txt', mode 'rb' at 0x7fc16cbc5e40>}
```

At this point, the `looper` component's output can be checked when the loop
terminates.

# Modify `looper`

The file `looper.py` has a function called `checkloop()`. This function is used
to check if the loop should be terminated, or the workflow needs to resubmitted
with the intermediate results:

```
def checkloop(f):
    with open(f) as content:
        value = int(content.read())
        if value == 1:
            log.info('FINISHED!!!')
        else:
            log.info("Step %d, invoking again..." % value)
```

This function is called for each file received from the `POSTPROCESS` node,
so the code must be prepared to check only relevant files. The code here checks
a simple exit condition, which can be extended as needed. The `else` branch is
responsible for submitting the intermediate result to the `PREPROCESS` node,
please see the code for details.
