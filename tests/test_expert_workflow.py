"""Expert packet inputs and conservative budget projections; not model quality tests."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from harness_router import route, _load_manifest, RouterError
from harness_validator import validate_intake, ContractError


class ExpertWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.context = json.loads((ROOT / 'templates/workflow-intake.json.example').read_text())
        self.manifest = _load_manifest(ROOT / 'registry/routing-gates.json')

    def test_invalid_lens_rejected_by_router_and_intake_validator(self):
        for value in ('all_knowing', '', None, [], True):
            context = copy.deepcopy(self.context)
            context['work_units'][0]['reasoning_lens'] = value
            with self.subTest(value=value):
                with self.assertRaises(RouterError):
                    route(context, self.manifest)
                with self.assertRaises(ContractError):
                    validate_intake(context, ROOT / 'registry/taxonomy.json')

    def test_lenses_preserve_existing_parallel_plan(self):
        before = route(self.context, self.manifest)
        for unit, lens in zip(self.context['work_units'], ('meticulous', 'minimal_sufficient')):
            unit['reasoning_lens'] = lens
        after = route(self.context, self.manifest)
        self.assertEqual(after['activated_skills'], before['activated_skills'])
        self.assertEqual(after['execution_profile'], before['execution_profile'])
        self.assertEqual(after['work_plan']['batches'], before['work_plan']['batches'])
        self.assertEqual(after['work_plan']['mode'], 'parallel')
        self.assertFalse(after['work_plan']['dispatch_authorized'])

    def test_budget_projects_serial_admission_without_discarding_units(self):
        before = route(self.context, self.manifest)['work_plan']
        self.context['delegation']['worker_token_budget'] = 1000
        after = route(self.context, self.manifest)['work_plan']
        self.assertEqual(before['mode'], 'parallel')
        self.assertEqual(after['mode'], 'single')
        self.assertEqual(after['max_workers'], 1)
        self.assertEqual(after['units'], before['units'])
        self.assertEqual(after['batches'], [['a'], ['b'], ['join']])
        self.assertIn('worker_token_budget_requires_reported_usage_before_next_dispatch', after['reasons'])
