# ROS 2 MCP graph inspection

This optional tool is ready for local stdio clients after setup. It is separate
from the dependency-free harness. No client registration or robot connection is
performed by setup. The active ROS 2 skill selects its usage procedure only for
ROS 2 plus `ros_mcp_server` work.

## Install and start

From the harness root, with Python 3 and pip available:

```sh
sh tools/ros-mcp-server/setup.sh
sh tools/ros-mcp-server/run.sh --help
```

Setup downloads pinned uv 0.13.5, a Python 3.12 runtime and dependencies from
upstream's `uv.lock` into `.runtime/`. The source version is pinned; Python's
3.12 patch release is selected by uv at setup time. First setup needs network
access. Runtime caches and build output are ignored by Git and the harness
source manifest; the entrypoint, lockfile and original runtime source are pinned.
Repeat setup after an approved source update. No startup-time dependency
download occurs in `run.sh`.

Configure a project-scoped MCP client with these process settings, replacing
the path and endpoint with the project's approved values:

```text
transport: stdio
command: sh
arguments:
  /absolute/path/to/shared-harness/tools/ros-mcp-server/run.sh
  --rosbridge-ip
  127.0.0.1
  --rosbridge-port
  9090
  --timeout
  5
```

The address above is an example, not a discovered robot. Use a specific IPv4
address, port 1..65535 and timeout >0..30 seconds. ROS 2 rosbridge with rosapi
must already be available at that endpoint. The current profile supports the
`/rosapi` service namespace and ROS 2 service types. It does not perform ROS
version auto-detection, network discovery, ROS installation or rosbridge launch.
Use a trusted private/tunnelled endpoint: upstream's connection is `ws://`, not
TLS. Do not expose it publicly. Different service namespaces require scoped
compatibility work; do not silently change the target to make the tool work.

MCP initialization and tool listing do not contact rosbridge. The first
explicit query does. Project/client action authorization still applies. A
configured stdio command is not evidence that the current assistant has the
tool, or that a robot is connected; inspect actual tool availability first.
This repository does not write global Codex/Claude configuration.

## Exposed tools and limits

Nine tools: `get_nodes`, `get_node_details`, `get_topics`, `get_topic_type`,
`get_topic_details`, `get_message_details`, `get_services`, `get_service_type`,
`get_service_details`. They query graph and interface metadata.

The entrypoint removes every other tool, registers no prompts/resources, fixes
the endpoint at startup, and permits only reviewed rosapi metadata services.
No publishing, subscription/image saving, arbitrary service call, action goal,
parameter mutation, endpoint switch, network scan or control mode is exposed.
Using upstream `server.py` bypasses this bounded profile and is not the supported
harness entrypoint. Real control needs its own scope and integration review.

The adapter checks operation, correlation ID, service, success flag and expected
metadata fields. Transport failures and partial/malformed responses raise MCP
tool errors; they cannot become a successful empty graph. Requests are
serialized on the connection. This does not validate graph freshness, QoS,
physical state, real-time performance or safety. Upstream descriptions/examples
are hints, not proof that any named robot, node or service exists.

## Reproducibility and verification

Original runtime subset: [robotmcp/ros-mcp-server](https://github.com/robotmcp/ros-mcp-server/tree/476591ac058f58cae810cc775e50b51f8d3d757c),
version 3.1.2, Apache-2.0. Exact file hashes and included paths are in
[provenance.json](provenance.json). Upstream files are unmodified; the inspection
entrypoint is a separate harness adapter. Examples, media and CI are omitted.
The lockfile installs dependencies, including image dependencies required by
upstream imports, even though image tools are not exposed. This review is not
a comprehensive transitive dependency security audit.

```sh
tools/ros-mcp-server/.runtime/venv/bin/python -B tools/ros-mcp-server/test_inspect_server.py -v
python3 -B -m unittest discover -s tests -v
python3 -B scripts/fixture_runner.py
```

The tool suite runs real stdio initialization/listing and in-process mocked
queries, checks denied actions and malformed/error responses, and makes no live
ROS connection. Robot/simulator behavior and client UI discovery remain separate
integration checks. To remove this installation, first remove any project
client registration you added, stop its process, then remove only this tool's
`.runtime/`. Revert the scoped source commit to roll back the harness change.
