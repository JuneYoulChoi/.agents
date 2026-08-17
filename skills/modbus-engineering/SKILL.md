---
name: modbus-engineering
description: Design, implement, review, debug, migrate, secure, or verify Modbus device and software integration. Use for Modbus TCP, RTU or serial line, clients/servers/gateways, unit IDs, function codes, coils/discrete inputs/input or holding registers, register maps, word and byte order, scaling, polling, timeouts, retries, write authority, device simulation, protocol interoperability, or Modbus-to-ROS/service integration.
---

# Modbus Engineering

Treat the register map and transaction behavior as an external interface
contract. A language library is an implementation choice, not the protocol.

## Entry gate

Require intake, external entity/interface architecture, UC/FA/QAS, and a Modbus
`TECH-*` record. Brownfield work requires device/firmware/manual, transport,
roles/topology, register map, timing, current library/gateway, observed traffic
or tests, write permissions, failure behavior, and safety/security ownership.

## Workflow

1. Read [references/engineering-practices.md](references/engineering-practices.md).
2. Define client/server/gateway and TCP/RTU boundaries, addressing/unit IDs,
   function codes, register map, data representation, read/write authority,
   timing, freshness, errors, and compatibility.
3. Invoke `$language-engineering` for the selected binding and
   `$ros2-engineering`/`$grpc-engineering` only for an approved bridge boundary.
4. Route host/port/serial settings, unit IDs, polling, timeout/retry, register
   variants, scaling, and credentials/cert references through configuration.
5. Verify golden request/response vectors, endian/word order, boundary values,
   exceptions/timeouts/reconnect, malformed/partial traffic, device/gateway
   simulation, representative hardware, load/timing, writes/safety, and docs.

## Result and exit

Return transport/topology, register-map contract, representation, polling and
freshness, error/recovery, write/safety/security, binding/configuration,
verification, docs, and open points. Block writes or deployment when register
semantics, addressing/order/scaling, authority, freshness, or safety is unknown.
