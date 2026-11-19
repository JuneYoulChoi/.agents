"""Bounded native-worker receipts. Does not spawn, cancel, or contact providers."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from harness_validator import (ContractError, active_skill_ids, read_object,
                               validate_evidence_files, validate_acceptance_evidence, validate_skill_result,
                               validate_resolution_binding)
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
            'parent_usage': 'unavailable', 'total_task_tokens': None,
            'savings': 'not_measured'}


ROLE_GUIDANCE = {
    'analyst': ('You are the analyst for this unit. Collect scoped evidence from the named paths: callers, behavior, '
                'data and failure cases. Distinguish observations from hypotheses, keep competing explanations until '
                'evidence separates them, and report what you could not check. Do not design or edit.'),
    'designer': ('You are the designer for this unit. Explain scoped contracts, ownership and coupling, and compare only '
                 'alternatives that decide the same boundary, with trade-offs and the applicable SOLID/GRASP checks. '
                 'Recommend with evidence; preserve user-owned decisions. Do not edit code.'),
    'implementer': ('You are the implementer for this unit. Implement accepted behavior only within owned paths, in the '
                    'smallest coherent slice, following the supplied skill and project conventions. Verify the change '
                    'against every acceptance criterion and report commands, results and anything left undone.'),
    'reviewer': ('You are the reviewer for this unit. Check correctness and necessary complexity against current '
                 'evidence: contract and boundary failures, error and lifecycle handling, and unjustified abstraction. '
                 'Separate defects from optional improvements and cite the file and behavior for each finding. '
                 'Do not edit.'),
    'verifier': ('You are the verifier for this unit. Check acceptance independently on the pinned revision, without '
                 'relying on the producer\'s own tests or claims. Run or inspect the stated proof for each criterion and '
                 'report failed or missing checks plainly. Do not fix what you find.'),
    'documenter': ('You are the documenter for this unit. Write clear source-grounded documentation for the stated '
                   'audience and purpose; every claim traces to a cited source. Preserve uncertainty and traceability, '
                   'and do not invent behavior that the sources do not show.'),
}

# Portable gate roles (routing-gates.json execution_policy.gate_roles) mapped to the unit
# roles a worker may hold while that gate's skill is current. Guard and classifier are never workers.
GATE_ROLE_UNITS = {
    'architect': ('analyst', 'designer', 'reviewer', 'documenter'),
    'analyst': ('analyst', 'reviewer'),
    'planner': ('analyst', 'designer', 'reviewer'),
    'specialist': ('analyst', 'designer', 'implementer', 'reviewer'),
    'implementer': ('analyst', 'implementer', 'reviewer', 'documenter'),
    'verifier': ('verifier', 'reviewer', 'documenter'),
}

LENS_GUIDANCE = {
    'meticulous': 'Find missing requirements, counterexamples and boundary failures within the unit scope. Separate observed facts from assumptions; cite evidence and necessary unresolved decisions. Do not expand scope.',
    'minimal_sufficient': 'Find the least redundant path satisfying every acceptance criterion. Reuse current evidence, identify unnecessary work and state stopping conditions. Never omit required checks, ownership or error handling.',
}


def skill_context(state: dict, unit: dict, harness_root: Path, registry_path: Path) -> dict:
    """Resolve only the current approved skill; references remain explicit bounded reads."""
    skill = current_skill(state)
    if skill not in active_skill_ids(registry_path):
        raise ContractError('worker skill is not approved')
    metadata = next(s for s in read_object(registry_path)['skills'] if s['id'] == skill)
    entry = metadata['entry']
    root = harness_root.resolve(strict=True)
    path = (root / entry).resolve(strict=True)
    if root not in path.parents or 'incoming' in path.relative_to(root).parts:
        raise ContractError('worker skill escapes approved source')
    body = path.read_bytes()
    references = []
    required = metadata.get('required_worker_references', [])
    selected = unit.get('skill_references', [])
    if skill == 'core.language-engineering':
        language_refs = {f'skills/language-engineering/references/{lang}.md'
                         for lang in state['intake'].get('languages', [])}
        if not selected or not set(selected) <= language_refs:
            raise ContractError('language worker requires only evidenced language references')
    for relative in dict.fromkeys([*required, *selected]):
        ref = (root / relative).resolve(strict=True)
        if path.parent / 'references' not in ref.parents or ref != root / relative:
            raise ContractError('worker reference must be canonical and belong to the current skill')
        references.append({'path': str(ref), 'sha256': hashlib.sha256(ref.read_bytes()).hexdigest()})
    gate_id = state['execution']['skill_gates'][skill]
    gate = next(g for g in state['route']['gate_results'] if g['gate_id'] == gate_id)
    profile = next(p for p in state['route']['execution_profile']['gate_profiles'] if p['gate_id'] == gate_id)
    if unit['role'] not in GATE_ROLE_UNITS.get(profile['role'], ()):
        raise ContractError(f"unit role {unit['role']} is not available at the {profile['role']} gate")
    return {'entry': entry, 'path': str(path), 'sha256': hashlib.sha256(body).hexdigest(),
            'instructions': body.decode('utf-8'), 'references': references,
            'application_depth': gate.get('application_depths', {}).get(skill, state['classification']['depth']),
            'execution_profile': profile,
            'gate_role': profile['role'],
            'role_guidance': ROLE_GUIDANCE[unit['role']],
            'lens_guidance': LENS_GUIDANCE.get(unit.get('reasoning_lens')),
            'application_rule': 'Apply these instructions only to the unit scope. Read and verify selected references before work; stop if required context is missing. Do not run another skill or expand authority. Record actual model/reasoning resolution and instruction evidence in the result artifact.'}


def prepare(state: dict, request: dict, target: Path, now: float | None = None,
            harness_root: Path | None = None, registry_path: Path | None = None) -> dict:
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
    capacity = 1
    if mode == 'native':
        # Fresh capacity excludes the primary and unrelated agents, but includes
        # this task's already running workers. The adapter observes host state.
        observed = request.get('native_worker_capacity')
        if type(observed) is not int or observed < 0:
            raise ContractError('fresh native_worker_capacity required')
        capacity = min(plan['max_workers'], observed)
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
    context_files = validate_evidence_files(unit.get('context_artifacts'), target)
    root = harness_root or Path(__file__).resolve().parents[1]
    binding = skill_context(state, unit, root, registry_path or root / 'registry/active-skills.json')
    packet = {'context_artifacts': context_files, 'target_root': str(target), 'skill_context': binding, 'schema_version': 1, 'task_id': state['task_id'], 'skill_id': skill,
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
        'adapter_evidence_ids': evidence, 'admitted_capacity': capacity,
        'native_worker_capacity': request.get('native_worker_capacity') if mode == 'native' else None,
        'instruction_hash': binding['sha256'],
        'reference_hashes': [r['sha256'] for r in binding['references']],
        'context_artifacts': context_files, 'expected_reasoning': binding['execution_profile']['reasoning']}
    return {'packet': packet, 'packet_hash': packet_hash}


def record(state: dict, result: dict, now: float | None = None, target: Path | None = None) -> None:
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
        if target is None:
            raise ContractError('completion requires the target root for evidence validation')
        unit = next(u for u in state['route']['work_plan']['units'] if u['id'] == item['unit_id'])
        validate_evidence_files(item['context_artifacts'], target)
        validate_acceptance_evidence(result.get('verification'), unit['acceptance'], target)
        instruction = result.get('instruction_evidence', {})
        if not isinstance(instruction, dict):
            raise ContractError('instruction_evidence must be an object')
        if (instruction.get('instruction_hash') != item['instruction_hash']
                or instruction.get('reference_hashes') != item['reference_hashes']):
            raise ContractError('worker must report current instruction and reference evidence')
        # Reuse the existing resolution contract instead of another worker schema.
        validate_skill_result({'schema_version': 1, 'skill_id': skill, 'status': 'completed',
            'artifact_ids': result['artifact_ids'], 'evidence_ids': result['evidence_ids'],
            'transition': {'next_stage': 'verification'},
            'execution_resolution': result.get('execution_resolution')}, {skill})
        validate_resolution_binding(result['execution_resolution'], state['selected_adapter'], item['expected_reasoning'])
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
    units = {u['id']: u for u in plan.get('units', [])}
    for unit in units.values():
        owner = unit.get('skill_id')
        if owner is None and allow_unbound:
            continue
        if records.get(unit['id'], {}).get('status') == 'completed':
            continue
        if owner not in queue[cursor:]:
            raise ContractError('work unit must bind to a reachable pending skill: ' + unit['id'])

        for dependency in unit.get('depends_on', []):
            if records.get(dependency, {}).get('status') == 'completed':
                continue
            predecessor = units[dependency].get('skill_id')
            if predecessor is None and allow_unbound:
                continue
            if predecessor not in queue or queue.index(predecessor) > queue.index(owner):
                raise ContractError('dependency owner must precede or equal unit owner: ' + unit['id'])
