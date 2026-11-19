"""Gate closure, skip, resume, bounded feedback and routing-entry regressions (2026-11-19 review)."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from harness_router import route, _load_manifest, RouterError
from harness_runner import start, submit
from harness_state import StateStore
from harness_validator import ContractError

REGISTRY = ROOT / 'registry/active-skills.json'
TAXONOMY = ROOT / 'registry/taxonomy.json'
MANIFEST = ROOT / 'registry/routing-gates.json'
PATTERNS = 'core.architecture-and-design-patterns'
QUALITY = 'core.implementation-quality'
VERIFY = 'core.verify-and-handoff'


def base_intake():
    value = json.loads((ROOT / 'templates/workflow-intake.json.example').read_text())
    value.update(work_units=[], delegation={}, technologies=[], languages=['python'], fields=['implementation'],
                 project_state='brownfield', action='change', risk='low', depth='standard', work_type='standard',
                 change_characteristics=['authored_code'], enforcement_mode='hook')
    return value


def option(candidate_id, status='candidate'):
    return {'candidate_id': candidate_id, 'name': candidate_id, 'status': status, 'decision_scope': 'storage boundary',
            'fit': 'fits', 'recommendation_reason': 'evidence', 'benefits': ['isolation'], 'liabilities': ['mapping'],
            'quality_attribute_effects': [], 'affected_artifact_ids': [], 'migration_and_rollback': [],
            'verification_ids': []}


def pattern_review(decision_status):
    selected = decision_status == 'user_selected'
    return {'schema_version': 1, 'pattern_id': 'PATTERN-001', 'scopes': ['architecture'], 'drivers': ['QAS-1'],
            'open_issue_ids': [] if selected else ['ISSUE-1'],
            'candidates': [option('OPT-A', 'selected' if selected else 'candidate'), option('OPT-B')],
            'decision': {'status': decision_status, 'decision_scope': 'storage boundary',
                         'recommended_candidate_id': 'OPT-A', 'recommendation_reason': 'lower coupling',
                         'conditions_that_change_recommendation': ['team split'],
                         'selected_candidate_id': 'OPT-A' if selected else None,
                         'decision_evidence_ids': ['EVD-user-choice'] if selected else []}}


QUALITY_RECORD = {'schema_version': 1, 'status': 'completed', 'authored_boundaries': ['src'],
    'activated_profiles': [{'id': 'core', 'depth': 'light', 'authored_boundaries': ['src'],
        'evidence_ids': ['EVD-q'], 'expected_outcomes': ['behavior preserved'], 'verification_ids': ['VER-q']}],
    'suppressed_profiles': [], 'findings': [], 'changes_or_recommendations': [], 'residual_risks': [], 'open_points': []}


class RunnerGateClosureTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.target = Path(temp.name)
        self.intake = base_intake()
        self.intake['change_characteristics'] = ['authored_code', 'architecture_structure']
        self.proof = self.target / 'proof.txt'
        self.proof.write_text('Contract fixture evidence, not product validation.')

    def begin(self, **changes):
        intake = {**self.intake, **changes}
        path = self.target / 'intake.json'; path.write_text(json.dumps(intake))
        return start(self.target, 'TASK-INTEGRITY', path, 'claude', 'label', ROOT, REGISTRY, TAXONOMY, MANIFEST)

    def result(self, response, status='completed', **extra):
        skill = response['next']['skill_id']
        value = {'schema_version': 1, 'skill_id': skill, 'status': status,
                 'artifact_ids': ['ART-1'], 'evidence_ids': ['EVD-1'],
                 'transition': {'next_stage': response['next']['stage']}, 'error': None,
                 'execution_resolution': {'adapter': 'claude', 'model': 'fixture', 'reasoning': 'unknown',
                                          'native_reasoning': 'unknown', 'status': 'platform_default',
                                          'evidence_ids': []}}
        if skill == PATTERNS and status == 'completed':
            value['pattern_review'] = pattern_review('user_selected')
        if skill == QUALITY and status == 'completed':
            value['implementation_quality'] = QUALITY_RECORD
        if skill == VERIFY and status == 'completed':
            digest = hashlib.sha256(self.proof.read_bytes()).hexdigest()
            value['verification'] = [{'criterion': c, 'status': 'passed',
                                      'evidence': [{'path': 'proof.txt', 'sha256': digest}]}
                                     for c in self.intake['intent']['success_criteria']]
        value.update(extra)
        return value

    def send(self, response, result):
        path = self.target / 'result.json'; path.write_text(json.dumps(result))
        return submit(self.target, response['task_id'], response['revision'], path, ROOT, REGISTRY)

    def advance_to(self, response, skill):
        while response['next']['skill_id'] != skill:
            response = self.send(response, self.result(response))
        return response

    def assert_rejected(self, response, result):
        with self.assertRaises(ContractError):
            self.send(response, result)
        self.assertEqual(StateStore(self.target, harness_root=ROOT).read(response['task_id'])['revision'],
                         response['revision'])

    def test_gate_cannot_close_without_outputs_or_with_a_contradicting_transition(self):
        response = self.begin()
        self.assert_rejected(response, self.result(response, artifact_ids=[]))
        self.assert_rejected(response, self.result(response, evidence_ids=[]))
        for stage in ('clarification', 'backward_feedback', 'blocked', 'failed'):
            self.assert_rejected(response, self.result(response, transition={'next_stage': stage}))
        degraded = self.result(response)
        degraded['execution_resolution'].update(reasoning='low', status='degraded')
        self.assert_rejected(response, degraded)

    def test_activated_baseline_and_impact_cannot_be_skipped_for_a_mutation(self):
        response = self.begin()
        self.assert_rejected(response, self.result(response, 'not_applicable', reason='no docs'))
        response = self.advance_to(response, 'core.workflow-composition')
        self.assert_rejected(response, self.result(response, 'not_applicable'))  # no reason
        self.assert_rejected(response, self.result(response, 'not_applicable', reason='single slice', evidence_ids=[]))
        self.assertEqual(self.send(response, self.result(response, 'not_applicable', reason='single slice'))['status'],
                         'active')

    def test_typed_records_bind_pattern_and_quality_completion(self):
        response = self.advance_to(self.begin(), PATTERNS)
        missing = self.result(response); del missing['pattern_review']
        self.assert_rejected(response, missing)
        self.assert_rejected(response, self.result(response, pattern_review=pattern_review('user_decision_required')))
        response = self.advance_to(self.send(response, self.result(response)), QUALITY)
        missing = self.result(response); del missing['implementation_quality']
        self.assert_rejected(response, missing)
        self.assert_rejected(response, self.result(
            response, implementation_quality={**QUALITY_RECORD, 'status': 'not_applicable'}))

    def test_deep_route_requires_independent_verification_evidence(self):
        response = self.advance_to(self.begin(depth='deep'), VERIFY)
        self.assertTrue(response['next']['execution_profile']['independent_context'])
        self.assert_rejected(response, self.result(response))
        done = self.send(response, self.result(response, independent_verification_evidence_ids=['EVD-fresh-context']))
        self.assertEqual(done['status'], 'complete')


if __name__ == '__main__':
    unittest.main()
