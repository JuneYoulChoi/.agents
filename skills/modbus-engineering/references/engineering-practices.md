# Modbus engineering practices

## Contract and representation

- Version the device/firmware and register map. For every point record logical
  name, table (coil/discrete/input/holding), documented address and library
  offset convention, function code, access, width, type, byte/word order, scale,
  unit, valid/sentinel range, update rate, and compatibility notes.
- Distinguish protocol reference numbering from zero-based PDU/library
  addresses explicitly. Never infer a 32-bit/float order or signedness from one
  plausible sample.
- Bound contiguous reads/writes to device limits and semantic ownership. Avoid
  coupling unrelated register groups merely to reduce transactions.

## Transport, timing, and behavior

- For TCP, own endpoint, unit ID/gateway semantics, transaction correlation,
  connection pooling/serialization, timeout, reconnect, and stale response
  behavior. For RTU, own port/baud/parity/data/stop bits, slave ID, framing
  timing, CRC, bus arbitration, and turnaround.
- Define polling cadence, jitter, concurrency, device capacity, caching,
  freshness timestamp/quality, missed polls, backoff, and recovery. Do not retry
  non-idempotent writes blindly.
- Map Modbus exception responses, transport failures, partial data, invalid
  values, device reboot/config changes, and gateway failure into explicit
  application state. Preserve last value only with a visible stale/quality flag.

## Safety, security, and verification

- Separate read and write authority. Validate ranges/interlocks and require
  confirmation/audit for safety-relevant writes. A successful protocol response
  is not proof the physical process reached the commanded state.
- Treat legacy Modbus as untrusted on segmented industrial networks; apply
  gateway/firewall/allowlist/monitoring and approved secure transport where the
  architecture supports it. Never expose a device directly by convenience.
- Verify known vectors, address offsets, every data representation, min/max/
  sentinel, exception codes, timeout/reconnect/stale, malformed/partial frames,
  concurrent clients/bus load, simulator plus representative device, write
  interlocks/feedback, security boundary, and register-map documentation.

Primary sources: Modbus Application Protocol and Serial Line/TCP implementation
guides, exact device vendor register documentation, and project industrial
safety/security policy.
