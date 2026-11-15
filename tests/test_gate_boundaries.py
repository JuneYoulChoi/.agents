"""Reproduced guide/runtime gaps: concrete evidence, trust, ordering and restart."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from harness_bootstrap import source_tree_hash, verify_source
from harness_delegation import validate_bindings
from harness_router import route, _load_manifest, RouterError
from harness_runner import start, submit
from harness_state import StateStore
from harness_validator import (ContractError, canonical_json_bytes, validate_acceptance_evidence,
                               validate_intake)


class GateBoundaryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.target = Path(temp.name)
        self.registry = ROOT / 'registry/active-skills.json'
        self.taxonomy = ROOT / 'registry/taxonomy.json'
        self.manifest_path = ROOT / 'registry/routing-gates.json'
        self.manifest = _load_manifest(self.manifest_path)
        self.intake = json.loads((ROOT / 'templates/workflow-intake.json.example').read_text())
        self.intake.update(work_units=[], delegation={}, technologies=[], languages=['python'],
                           action='change', change_characteristics=['authored_code'])
        self.proof = self.target / 'proof.txt'
        self.proof.write_text('Contract test fixture: actual proof existence and pinned bytes, not product validation.')

    def evidence(self):
        return [{'path': 'proof.txt', 'sha256': hashlib.sha256(self.proof.read_bytes()).hexdigest()}]

    def begin(self, name='TASK-GATES', intake=None):
        p = self.target / 'intake.json'; p.write_text(json.dumps(intake or self.intake))
        return start(self.target, name, p, 'codex', 'untrusted-caller-label', ROOT,
                     self.registry, self.taxonomy, self.manifest_path)

    def result(self, response, status='completed'):
        return {'schema_version': 1, 'skill_id': response['next']['skill_id'], 'status': status,
            'artifact_ids': ['ART-fixture'], 'evidence_ids': ['EVD-fixture'],
            'transition': {'next_stage': 'verification'},
            'verification': [{'criterion': c, 'status': 'passed', 'evidence': self.evidence()}
                             for c in self.intake['intent']['success_criteria']],
            'execution_resolution': {'adapter': 'codex', 'model': 'fixture',
                'reasoning': 'unknown', 'native_reasoning': 'unknown',
                'status': 'platform_default', 'evidence_ids': []}}

    def send(self, response, result):
        p = self.target / 'result.json'; p.write_text(json.dumps(result))
        return submit(self.target, response['task_id'], response['revision'], p, ROOT, self.registry)

    def test_completion_rejects_empty_missing_or_stale_proof_then_accepts_current_evidence(self):
        response = self.begin()
        while response['next']['skill_id'] != 'core.verify-and-handoff':
            response = self.send(response, self.result(response))
        good = self.result(response)
        variants = []
        for key in ('artifact_ids', 'evidence_ids', 'verification'):
            bad = copy.deepcopy(good); bad[key] = []; variants.append(bad)
        bad = copy.deepcopy(good); bad['verification'][0]['evidence'][0]['sha256'] = '0'*64; variants.append(bad)
        bad = copy.deepcopy(good); bad['verification'][0]['evidence'][0]['path'] = 'missing.txt'; variants.append(bad)
        for bad in variants:
            with self.assertRaises(ContractError): self.send(response, bad)
            self.assertEqual(StateStore(self.target, harness_root=ROOT).read(response['task_id'])['revision'], response['revision'])
        self.assertEqual(self.send(response, good)['status'], 'complete')

    def test_every_acceptance_criterion_must_have_passed_evidence(self):
        valid = [{'criterion': c, 'status': 'passed', 'evidence': self.evidence()} for c in ['a','b']]
        validate_acceptance_evidence(valid, ['a','b'], self.target)
        for invalid in (valid[:1], [valid[0],valid[0]], [{**valid[0], 'status': 'not_run'},valid[1]]):
            with self.assertRaises(ContractError): validate_acceptance_evidence(invalid, ['a','b'], self.target)
        stale = copy.deepcopy(valid); self.proof.write_text('changed')
        with self.assertRaises(ContractError): validate_acceptance_evidence(stale, ['a','b'], self.target)

    def test_evidence_cannot_escape_target_or_use_symlink_alias(self):
        (self.target / 'alias.txt').symlink_to(self.proof)
        for path in ('../proof.txt', str(self.proof), 'alias.txt'):
            with self.assertRaises(ContractError):
                validate_acceptance_evidence([{'criterion':'a','status':'passed','evidence':[
                    {'path': path, 'sha256': self.evidence()[0]['sha256']}]}], ['a'], self.target)

    def test_reversed_skill_dependency_is_rejected_before_execution(self):
        units = [{'id':'a','skill_id':'core.nodejs-engineering','depends_on':['b']},
                 {'id':'b','skill_id':'core.react-engineering','depends_on':[]}]
        with self.assertRaisesRegex(ContractError, 'dependency owner'):
            validate_bindings({'units':units}, ['core.nodejs-engineering','core.react-engineering'])
        validate_bindings({'units':units}, ['core.react-engineering','core.nodejs-engineering'])

    def test_only_annotations_cannot_suppress_authored_quality(self):
        for only in ('documentation_only', 'generated_code_only'):
            c = copy.deepcopy(self.intake); c['change_characteristics'] = ['authored_code', only]
            with self.assertRaises(ContractError): validate_intake(c, self.taxonomy)
            with self.assertRaises(RouterError): route(c, self.manifest)
        c = copy.deepcopy(self.intake); c['fields'].append('documentation')
        self.assertIn('core.implementation-quality', route(c, self.manifest)['activated_skills'])

    def test_unknown_cannot_mutate_or_advance_discovery_and_can_restart_after_reclassification(self):
        c = copy.deepcopy(self.intake); c.update(project_state='unknown', architecture_status='missing')
        self.assertEqual(route(c, self.manifest)['status'], 'blocked')
        c['action'] = 'investigate'
        response = self.begin(intake=c)
        with self.assertRaisesRegex(ContractError, 'reclassification'):
            self.send(response, self.result(response))
        response = self.send(response, self.result(response, 'waiting_user'))
        before = StateStore(self.target, harness_root=ROOT).read(response['task_id'])
        c = copy.deepcopy(self.intake); c['supersedes_task_id'] = response['task_id']
        restarted = self.begin('TASK-RECLASSIFIED', c)
        state = StateStore(self.target, harness_root=ROOT).read(restarted['task_id'])
        self.assertEqual(state['supersedes']['task_id'], response['task_id'])
        self.assertIn('core.brownfield-impact-analysis', state['execution']['queue'])
        self.assertEqual(before, StateStore(self.target, harness_root=ROOT).read(response['task_id']))
        self.assertEqual(state['execution']['results'], [])

    def test_restart_cannot_silently_replace_an_active_task(self):
        response = self.begin(); c = copy.deepcopy(self.intake); c['supersedes_task_id'] = response['task_id']
        with self.assertRaisesRegex(ContractError, 'interrupted'):
            self.begin('TASK-RESTART', c)

    def test_invalid_registry_and_changed_source_are_rejected(self):
        root = self.target / 'harness'; (root / 'registry').mkdir(parents=True)
        source = root / 'skill.md'; source.write_text('reviewed source')
        registry = {'integrity_policy': {'manifest_revision': 'test-pin'}, 'skills': []}
        registry['integrity_policy']['manifest_sha256'] = hashlib.sha256(canonical_json_bytes(registry)).hexdigest()
        reg = root / 'registry/active-skills.json'; reg.write_text(json.dumps(registry))
        (root / 'registry/adapter-manifest.json').write_text(json.dumps({'source_revision':'test-pin','source_tree_sha256':source_tree_hash(root)}))
        verify_source(root, reg)
        source.write_text('unreviewed change')
        with self.assertRaisesRegex(ContractError, 'source integrity'): verify_source(root, reg)
        bad = json.loads(self.registry.read_text()); bad['integrity_policy']['manifest_sha256'] = '0'*64
        reg.write_text(json.dumps(bad))
        with self.assertRaisesRegex(ContractError, 'registry integrity'): verify_source(ROOT, reg)

    def test_caller_revision_is_not_an_integrity_claim(self):
        response = self.begin(); state = StateStore(self.target, harness_root=ROOT).read(response['task_id'])
        self.assertNotEqual(state['harness_source_revision'], 'untrusted-caller-label')
        self.assertEqual(state['harness_source_revision'], json.loads((ROOT/'registry/adapter-manifest.json').read_text())['source_revision'])
