"""ROS 2 graph inspection via pinned upstream tools; no actuation tools."""

from __future__ import annotations

import argparse
import asyncio
import ipaddress
import json
import math

from fastmcp import FastMCP
from ros_mcp.tools.nodes import register_node_tools
from ros_mcp.tools.services import register_service_tools
from ros_mcp.tools.topics import register_topic_tools
from ros_mcp.utils.websocket import WebSocketManager


# Explicit names, not upstream readOnlyHint annotations or a name-prefix rule.
ALLOWED_TOOLS = frozenset({
    "get_nodes", "get_node_details", "get_topics", "get_topic_type",
    "get_topic_details", "get_message_details", "get_services",
    "get_service_type", "get_service_details",
})
ALLOWED_SERVICES = frozenset({
    "nodes", "node_details", "topics", "topic_type", "publishers",
    "subscribers", "message_details", "services", "service_type",
    "service_request_details", "service_response_details", "service_node",
})
RESPONSE_FIELDS = {
    "nodes": {"nodes": list}, "node_details": {"publishing": list, "subscribing": list, "services": list},
    "topics": {"topics": list, "types": list}, "topic_type": {"type": str},
    "publishers": {"publishers": list}, "subscribers": {"subscribers": list},
    "message_details": {"typedefs": list}, "services": {"services": list},
    "service_type": {"type": str}, "service_request_details": {"typedefs": list},
    "service_response_details": {"typedefs": list}, "service_node": {"node": str},
}


class InspectionConnection(WebSocketManager):
    """Reject failed/mismatched responses before upstream tools can lose errors."""

    def request(self, message: dict, timeout: float | None = None) -> dict:
        service = message.get("service", "")
        if (message.get("op") != "call_service"
                or service not in {"/rosapi/" + name for name in ALLOWED_SERVICES}):
            raise ValueError("Only reviewed /rosapi metadata queries are supported")
        # Serialize the entire exchange, not just individual send/receive calls.
        with self.lock:
            error = self.send(message)
            if error:
                raise RuntimeError(error)
            raw = self.receive(timeout)
            if raw is None:
                raise RuntimeError("No response from rosbridge; graph state is unknown")
            try:
                response = json.loads(raw)
            except (ValueError, TypeError) as exc:
                raise RuntimeError("Invalid rosbridge JSON response") from exc
            if not isinstance(response, dict):
                raise RuntimeError("Expected a rosbridge response object")
            if (response.get("op") != "service_response"
                    or response.get("id") != message.get("id")
                    or response.get("service") != service):
                raise RuntimeError("Mismatched rosbridge response; retry after diagnosis")
            if (response.get("error") or response.get("result") is not True
                    or not isinstance(response.get("values"), dict)):
                raise RuntimeError("Rosbridge query failed or returned malformed values")
            expected = RESPONSE_FIELDS[service.rsplit("/", 1)[-1]]
            if any(not isinstance(response["values"].get(key), kind) for key, kind in expected.items()):
                raise RuntimeError("Missing or invalid metadata fields; graph state is unknown")
            if service.endswith("/topics") and len(response["values"]["topics"]) != len(response["values"]["types"]):
                raise RuntimeError("Topic names/types have inconsistent lengths")
            return response


async def build_server(host: str, port: int, timeout: float) -> FastMCP:
    # An explicit endpoint is required. Do not inherit ambient robot settings.
    address = ipaddress.ip_address(host)
    if address.version != 4 or address.is_unspecified or address.is_multicast:
        raise ValueError("Use a specific IPv4 rosbridge address")
    if not 1 <= port <= 65535 or not math.isfinite(timeout) or not 0 < timeout <= 30:
        raise ValueError("Port must be 1..65535 and timeout must be >0 and <=30 seconds")
    server = FastMCP("ros2-inspect")
    connection = InspectionConnection(str(address), port, default_timeout=timeout)
    register_node_tools(server, connection)
    register_service_tools(server, connection)
    register_topic_tools(server, connection)
    for name in list(await server.get_tools()):
        if name not in ALLOWED_TOOLS:
            server.remove_tool(name)
    if set(await server.get_tools()) != ALLOWED_TOOLS:
        raise RuntimeError("Upstream inspection tool contract changed; review required")
    # No resources/prompts are registered: no alternate path to file or robot actions.
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rosbridge-ip", required=True)
    parser.add_argument("--rosbridge-port", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()
    server = asyncio.run(build_server(args.rosbridge_ip, args.rosbridge_port, args.timeout))
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
