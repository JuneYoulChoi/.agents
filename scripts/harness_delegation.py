"""Bounded native-worker receipts. Does not spawn, cancel, or contact providers."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from harness_validator import ContractError
from harness_workflow import _conflict

CONTEXT_BYTES = 16384
RESULT_BYTES = 8192


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def current_skill(state: dict) -> str:
    if state['status'] != 'active':
        raise ContractError('work requires an active task')
    execution = state['execution']
    return execution['queue'][execution['cursor']]


def usage_summary(state: dict) -> dict:
    records = list(state['execution'].get('work_records', {}).values())
    totals = {'input_tokens': 0, 'output_tokens': 0}
    unknown = 0
    for record in records:
        usage = record.get('result', {}).get('usage')
        if not usage or usage['status'] != 'reported':
            unknown += 1
        else:
            for key in totals:
                totals[key] += usage[key]
    return {'scope': 'worker_input_output_only', 'reported': totals,
            'unavailable_or_pending': unknown,
            'reported_units': len(records) - unknown,
            'total_worker_tokens': None if unknown else sum(totals.values()),
            'savings': 'not_measured'}


def prepare(state: dict, request: dict, target: Path, now: float | None = None) -> dict:
    """Mutate a locked state copy and return the only context to send a worker."""
    now = time.time() if now is None else now
    skill = current_skill(state)
    plan = state['route']['work_plan']
    units = {u['id']: u for u in plan['units']}
    if not isinstance(request.get('unit_id'), str):
        raise ContractError('unit_id must be a string')
    unit = units.get(request['unit_id'])
    if unit is None or unit.get('skill_id') != skill:
        raise ContractError('unit must be bound to the current skill')
    records = state['execution'].setdefault('work_records', {})
    if unit['id'] in records:
        raise ContractError('unit already prepared; retry requires a newly reviewed work unit')
    if any(records.get(dep, {}).get('status') != 'completed' for dep in unit.get('depends_on', [])):
        raise ContractError('work dependencies have not joined')
    if request.get('input_revision') != unit['input_revision']:
        raise ContractError('work input revision mismatch')
    checks = request.get('checks', {})
    if (not isinstance(checks, dict) or any(checks.get(key) is not True for key in
            ('authority', 'capability', 'revision', 'ownership', 'tools'))):
        raise ContractError('fresh adapter authority/capability/revision/ownership/tool checks required')
    evidence = request.get('evidence_ids')
    if not isinstance(evidence, list) or not evidence or any(not isinstance(e, str) or not e.strip() for e in evidence):
        raise ContractError('adapter checks require evidence IDs')
    mode = request.get('mode')
    if mode not in ('native', 'serial'):
        raise ContractError('work mode must be native or serial')
    delegation = state['intake'].get('delegation', {})
    if mode == 'native' and (any(delegation.get(k) is not True for k in
            ('requested', 'authorized', 'available')) or any(not delegation.get(k) for k in
            ('benefit_evidence_ids', 'authorization_evidence_ids', 'capability_evidence_ids'))):
        raise ContractError('native delegation lacks authority/capability/benefit evidence')
    running = [r for r in records.values() if r['status'] == 'running']
    if any(now >= r['deadline'] for r in running):
        raise ContractError('expired work must be recorded and cancelled before more dispatch')
    capacity = plan['max_workers'] if mode == 'native' else 1
    if len(running) >= capacity or any(r['mode'] == 'serial' for r in running):
        raise ContractError('worker capacity exceeded')
    if any(_conflict(unit, units[r['unit_id']]) for r in running):
        raise ContractError('work ownership/resource conflict')
    target = target.resolve(strict=True)
    for path in unit.get('read_paths', []) + unit.get('write_paths', []):
        resolved = (target / path).resolve()
        if resolved != target and target not in resolved.parents:
            raise ContractError('work path escapes target through symlink')
        if resolved != target / path:
            raise ContractError('aliased work paths require canonical paths before dispatch')
    timeout = delegation.get('timeout_seconds', 300)
    budget = delegation.get('worker_token_budget')
    usage = usage_summary(state)
    if budget is not None and (usage['unavailable_or_pending'] or
            sum(usage['reported'].values()) >= budget):
        raise ContractError('worker token budget exhausted or usage unknown; no further dispatch')
    packet = {'schema_version': 1, 'task_id': state['task_id'], 'skill_id': skill,
              'unit': unit, 'task_goal': state['intent']['goal'], 'constraints': state['intent'].get('constraints', []),
              'context_policy': 'fresh_context_no_history_no_recursive_delegation',
              'result_max_bytes': RESULT_BYTES,
              'timeout_seconds': timeout, 'mode': mode}
    # Deliberately exclude intake, route, conversation, other units and prior outputs.
    if len(json.dumps(packet, ensure_ascii=False).encode()) > CONTEXT_BYTES:
        raise ContractError('worker context exceeds 16384 bytes; use bounded artifact references')
    packet_hash = digest(packet)
    records[unit['id']] = {'unit_id': unit['id'], 'skill_id': skill,
        'input_revision': unit['input_revision'], 'packet_hash': packet_hash,
        'status': 'running', 'mode': mode, 'started_at': now, 'deadline': now + timeout,
        'adapter_evidence_ids': evidence}
    return {'packet': packet, 'packet_hash': packet_hash}


def record(state: dict, result: dict, now: float | None = None) -> None:
    """Record one terminal result; timed-out work can never become successful."""
    now = time.time() if now is None else now
    skill = current_skill(state)
    records = state['execution'].get('work_records', {})
    if not isinstance(result.get('unit_id'), str):
        raise ContractError('unit_id must be a string')
    item = records.get(result['unit_id'])
    if item is None or item['status'] != 'running' or item['skill_id'] != skill:
        raise ContractError('no current running unit, or duplicate result')
    if len(json.dumps(result, ensure_ascii=False).encode()) > RESULT_BYTES:
        raise ContractError('worker result exceeds 8192 bytes; store detail in an artifact')
    for key in ('input_revision', 'packet_hash'):
        if result.get(key) != item[key]:
            raise ContractError('stale work result: ' + key)
    if result.get('worker_stopped') is not True:
        raise ContractError('adapter must confirm worker termination before releasing ownership')
    status = result.get('status')
    if status not in ('completed', 'failed', 'cancelled', 'timed_out'):
        raise ContractError('invalid terminal work status')
    if now < item['started_at']:
        raise ContractError('clock moved backwards; cannot accept work timing')
    if now >= item['deadline']:
        status = 'timed_out'
    if status == 'completed':
        for key in ('artifact_ids', 'evidence_ids'):
            values = result.get(key)
            if not isinstance(values, list) or not values or any(not isinstance(v, str) or not v.strip() for v in values):
                raise ContractError('completed work requires ' + key)
        if result.get('acceptance_verified') is not True:
            raise ContractError('coordinator must verify unit acceptance before joining')
    usage = result.get('usage')
    if not isinstance(usage, dict) or usage.get('status') not in ('reported', 'unavailable'):
        raise ContractError('work usage must be reported or unavailable')
    if usage['status'] == 'reported':
        for key in ('input_tokens', 'output_tokens'):
            if type(usage.get(key)) is not int or usage[key] < 0:
                raise ContractError('reported token counts must be nonnegative integers')
        if not isinstance(usage.get('source'), str) or not usage['source'].strip():
            raise ContractError('reported usage requires provider-counter source')
    elif any(k in usage for k in ('input_tokens', 'output_tokens')):
        raise ContractError('unavailable usage cannot report invented token counts')
    item.update(status=status, finished_at=now, result={**result, 'status': status})


def require_join(state: dict, skill: str) -> None:
    units = state['route'].get('work_plan', {}).get('units', [])
    records = state['execution'].get('work_records', {})
    required = units if skill == 'core.verify-and-handoff' else [u for u in units if u.get('skill_id') == skill]
    if any(records.get(u['id'], {}).get('status') != 'completed' for u in required):
        raise ContractError('required work units have not successfully joined')


def validate_bindings(plan: dict, queue: list[str], cursor: int = 0,
                      records: dict | None = None, allow_unbound: bool = False) -> None:
    """Unbound intake units are provisional until composition, never dispatchable."""
    records = records or {}
    for unit in plan.get('units', []):
        owner = unit.get('skill_id')
        if owner is None and allow_unbound:
            continue
        if records.get(unit['id'], {}).get('status') == 'completed':
            continue
        if owner not in queue[cursor:]:
            raise ContractError('work unit must bind to a reachable pending skill: ' + unit['id'])
