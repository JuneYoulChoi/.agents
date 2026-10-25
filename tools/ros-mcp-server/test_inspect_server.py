"""Offline protocol tests: no ROS installation, robot or network connection."""

import asyncio
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from fastmcp import Client
from fastmcp.exceptions import ToolError
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from inspect_server import ALLOWED_TOOLS, InspectionConnection, build_server


class ResponseTests(unittest.TestCase):
    def setUp(self):
        self.connection = InspectionConnection("127.0.0.1", 9090)
        self.message = {"op": "call_service", "service": "/rosapi/nodes", "id": "test", "args": {}}
        self.response = {"op": "service_response", "service": "/rosapi/nodes", "id": "test",
                         "result": True, "values": {"nodes": []}}

    def test_legitimate_empty_graph_is_preserved(self):
        with patch.object(self.connection, "send", return_value=None), \
             patch.object(self.connection, "receive", return_value=json.dumps(self.response)):
            self.assertEqual(self.connection.request(self.message), self.response)

    def test_transport_failure_never_turns_into_empty_graph(self):
        with patch.object(self.connection, "send", return_value="connection refused"), \
             patch.object(self.connection, "receive") as receive:
            with self.assertRaisesRegex(RuntimeError, "connection refused"):
                self.connection.request(self.message)
            receive.assert_not_called()

    def test_timeout_malformed_failed_and_mismatched_responses_raise(self):
        bad = [None, "not-json", "[]", json.dumps({"error": "timeout"})]
        for delta in ({"id": "other"}, {"service": "/other"}, {"result": False},
                      {"values": {}}, {"values": {"nodes": "invalid"}}, {"op": "publish"}):
            bad.append(json.dumps(dict(self.response, **delta)))
        for raw in bad:
            with self.subTest(raw=raw), patch.object(self.connection, "send", return_value=None), \
                 patch.object(self.connection, "receive", return_value=raw):
                with self.assertRaises(RuntimeError):
                    self.connection.request(self.message)

    def test_unreviewed_wire_operation_is_rejected_before_network(self):
        for message in ({"op": "publish", "topic": "/cmd_vel"},
                        {"op": "call_service", "service": "/robot/reset"}):
            with patch.object(self.connection, "send") as send:
                with self.assertRaises(ValueError):
                    self.connection.request(message)
                send.assert_not_called()


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_discovery_does_not_connect_or_expose_alternate_actions(self):
        with patch("websocket.create_connection") as connect:
            server = await build_server("127.0.0.1", 9090, 1.0)
            async with Client(server) as client:
                self.assertEqual({t.name for t in await client.list_tools()}, ALLOWED_TOOLS)
                self.assertEqual(await client.list_resources(), [])
                self.assertEqual(await client.list_prompts(), [])
                for tool in ("publish_once", "call_service", "send_action_goal", "set_parameter",
                             "delete_parameter", "connect_to_robot", "ping_robots", "subscribe_once"):
                    with self.assertRaises(ToolError):
                        await client.call_tool(tool, {})
            connect.assert_not_called()

    async def test_failed_query_is_mcp_error_and_success_has_real_observation(self):
        server = await build_server("127.0.0.1", 9090, 1.0)
        async with Client(server) as client:
            with patch.object(InspectionConnection, "send", return_value="offline"):
                with self.assertRaises(ToolError):
                    await client.call_tool("get_nodes", {})
            response = {"op": "service_response", "service": "/rosapi/nodes",
                        "id": "get_nodes_request_1", "result": True, "values": {"nodes": ["/sim"]}}
            with patch.object(InspectionConnection, "send", return_value=None), \
                 patch.object(InspectionConnection, "receive", return_value=json.dumps(response)):
                result = await client.call_tool("get_nodes", {})
                self.assertEqual(result.data["nodes"], ["/sim"])

    async def test_invalid_endpoint_port_and_timeout_fail_before_connection(self):
        for host, port, timeout in (("0.0.0.0", 9090, 1), ("example.org", 9090, 1),
                                    ("127.0.0.1", 0, 1), ("127.0.0.1", 9090, float("nan")),
                                    ("127.0.0.1", 9090, 31)):
            with self.subTest(host=host, port=port, timeout=timeout), self.assertRaises(ValueError):
                await build_server(host, port, timeout)

    async def test_real_stdio_initialize_and_tool_listing(self):
        tool_root = Path(__file__).resolve().parent
        params = StdioServerParameters(command="sh", args=[str(tool_root / "run.sh"),
            "--rosbridge-ip", "127.0.0.1", "--rosbridge-port", "1"],
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        async def check():
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    self.assertEqual({t.name for t in result.tools}, ALLOWED_TOOLS)
        await asyncio.wait_for(check(), timeout=30)


if __name__ == "__main__":
    unittest.main()
