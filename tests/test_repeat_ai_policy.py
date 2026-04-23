"""Tests for the REPEAT-AI policy engine."""

import unittest
import json
import tempfile
import os
from repeat_ai.policy import PolicyEngine, Classification
from repeat_ai.cli import cmd_diff, extract_paths_from_diff
import argparse


class TestClassification(unittest.TestCase):
    """Tests for Classification enum."""
    
    def test_classification_precedence(self):
        """Test that classifications have correct precedence values."""
        self.assertEqual(Classification.DENY.value, 3)
        self.assertEqual(Classification.WARN.value, 2)
        self.assertEqual(Classification.ALLOW.value, 1)
        self.assertEqual(Classification.UNMATCHED.value, 0)
        
        # Verify precedence order
        self.assertGreater(Classification.DENY.value, Classification.WARN.value)
        self.assertGreater(Classification.WARN.value, Classification.ALLOW.value)
        self.assertGreater(Classification.ALLOW.value, Classification.UNMATCHED.value)


class TestPolicyEngine(unittest.TestCase):
    """Tests for PolicyEngine class."""
    
    def setUp(self):
        """Set up test policy engine."""
        self.policy_data = {
            'deny': ['*.critical', 'security/*', 'invariants/*'],
            'warn': ['*.config', 'schema/*', 'api/*'],
            'allow': ['*.test', '*.temp', 'debug/*']
        }
        self.engine = PolicyEngine(self.policy_data)
    
    def test_init(self):
        """Test PolicyEngine initialization."""
        self.assertEqual(self.engine.deny_patterns, self.policy_data['deny'])
        self.assertEqual(self.engine.warn_patterns, self.policy_data['warn'])
        self.assertEqual(self.engine.allow_patterns, self.policy_data['allow'])
    
    def test_classify_path_deny(self):
        """Test classification of DENY paths."""
        self.assertEqual(self.engine.classify_path('file.critical'), Classification.DENY)
        self.assertEqual(self.engine.classify_path('security/auth.py'), Classification.DENY)
        self.assertEqual(self.engine.classify_path('invariants/check.py'), Classification.DENY)
    
    def test_classify_path_warn(self):
        """Test classification of WARN paths."""
        self.assertEqual(self.engine.classify_path('app.config'), Classification.WARN)
        self.assertEqual(self.engine.classify_path('schema/user.json'), Classification.WARN)
        self.assertEqual(self.engine.classify_path('api/endpoint.py'), Classification.WARN)
    
    def test_classify_path_allow(self):
        """Test classification of ALLOW paths."""
        self.assertEqual(self.engine.classify_path('unit.test'), Classification.ALLOW)
        self.assertEqual(self.engine.classify_path('scratch.temp'), Classification.ALLOW)
        self.assertEqual(self.engine.classify_path('debug/output.log'), Classification.ALLOW)
    
    def test_classify_path_unmatched(self):
        """Test classification of UNMATCHED paths."""
        self.assertEqual(self.engine.classify_path('random.txt'), Classification.UNMATCHED)
        self.assertEqual(self.engine.classify_path('src/main.py'), Classification.UNMATCHED)
        self.assertEqual(self.engine.classify_path('data/input.csv'), Classification.UNMATCHED)
    
    def test_precedence_deny_over_warn(self):
        """Test that DENY takes precedence over WARN."""
        # Add overlapping patterns
        engine = PolicyEngine({
            'deny': ['*.critical'],
            'warn': ['*.critical'],  # Same pattern
            'allow': []
        })
        self.assertEqual(engine.classify_path('file.critical'), Classification.DENY)
    
    def test_precedence_deny_over_allow(self):
        """Test that DENY takes precedence over ALLOW."""
        engine = PolicyEngine({
            'deny': ['*.critical'],
            'warn': [],
            'allow': ['*.critical']  # Same pattern
        })
        self.assertEqual(engine.classify_path('file.critical'), Classification.DENY)
    
    def test_precedence_warn_over_allow(self):
        """Test that WARN takes precedence over ALLOW."""
        engine = PolicyEngine({
            'deny': [],
            'warn': ['*.config'],
            'allow': ['*.config']  # Same pattern
        })
        self.assertEqual(engine.classify_path('app.config'), Classification.WARN)
    
    def test_evaluate_empty_paths(self):
        """Test evaluation with no paths."""
        result = self.engine.evaluate([])
        self.assertEqual(result['summary']['deny'], 0)
        self.assertEqual(result['summary']['warn'], 0)
        self.assertEqual(result['summary']['allow'], 0)
        self.assertEqual(result['summary']['unmatched'], 0)
        self.assertFalse(result['has_deny_violations'])
    
    def test_evaluate_mixed_paths(self):
        """Test evaluation with mixed classification paths."""
        paths = [
            'file.critical',      # DENY
            'app.config',         # WARN
            'unit.test',          # ALLOW
            'random.txt'          # UNMATCHED
        ]
        result = self.engine.evaluate(paths)
        
        self.assertEqual(result['summary']['deny'], 1)
        self.assertEqual(result['summary']['warn'], 1)
        self.assertEqual(result['summary']['allow'], 1)
        self.assertEqual(result['summary']['unmatched'], 1)
        self.assertTrue(result['has_deny_violations'])
        
        # Check classifications
        self.assertEqual(result['classifications']['file.critical'], Classification.DENY)
        self.assertEqual(result['classifications']['app.config'], Classification.WARN)
        self.assertEqual(result['classifications']['unit.test'], Classification.ALLOW)
        self.assertEqual(result['classifications']['random.txt'], Classification.UNMATCHED)
    
    def test_evaluate_no_deny_violations(self):
        """Test evaluation without DENY violations."""
        paths = ['app.config', 'unit.test', 'random.txt']
        result = self.engine.evaluate(paths)
        
        self.assertEqual(result['summary']['deny'], 0)
        self.assertFalse(result['has_deny_violations'])
    
    def test_format_report_grouped(self):
        """Test grouped report formatting."""
        paths = ['file.critical', 'app.config', 'unit.test', 'random.txt']
        evaluation = self.engine.evaluate(paths)
        report = self.engine.format_report(evaluation, grouped=True)
        
        # Check summary section
        self.assertIn('Policy Evaluation Summary', report)
        self.assertIn('DENY:      1', report)
        self.assertIn('WARN:      1', report)
        self.assertIn('ALLOW:     1', report)
        self.assertIn('UNMATCHED: 1', report)
        
        # Check grouped section
        self.assertIn('Paths by Classification', report)
        self.assertIn('DENY:', report)
        self.assertIn('file.critical', report)
    
    def test_format_report_per_path(self):
        """Test per-path report formatting."""
        paths = ['file.critical', 'app.config']
        evaluation = self.engine.evaluate(paths)
        report = self.engine.format_report(evaluation, grouped=False)
        
        # Check summary section
        self.assertIn('Policy Evaluation Summary', report)
        
        # Check per-path section
        self.assertIn('Per-Path Classification', report)
        self.assertIn('DENY', report)
        self.assertIn('WARN', report)
    
    def test_from_file(self):
        """Test loading policy from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.policy_data, f)
            temp_file = f.name
        
        try:
            engine = PolicyEngine.from_file(temp_file)
            self.assertEqual(engine.deny_patterns, self.policy_data['deny'])
            self.assertEqual(engine.warn_patterns, self.policy_data['warn'])
            self.assertEqual(engine.allow_patterns, self.policy_data['allow'])
        finally:
            os.unlink(temp_file)


class TestExtractPathsFromDiff(unittest.TestCase):
    """Tests for extract_paths_from_diff function."""
    
    def test_no_differences(self):
        """Test extraction with identical data."""
        baseline = {'key1': 'value1', 'key2': 'value2'}
        current = {'key1': 'value1', 'key2': 'value2'}
        paths = extract_paths_from_diff(baseline, current)
        self.assertEqual(paths, [])
    
    def test_value_changes(self):
        """Test extraction with changed values."""
        baseline = {'key1': 'value1', 'key2': 'value2'}
        current = {'key1': 'changed', 'key2': 'value2'}
        paths = extract_paths_from_diff(baseline, current)
        self.assertIn('key1', paths)
        self.assertNotIn('key2', paths)
    
    def test_added_keys(self):
        """Test extraction with added keys."""
        baseline = {'key1': 'value1'}
        current = {'key1': 'value1', 'key2': 'value2'}
        paths = extract_paths_from_diff(baseline, current)
        self.assertIn('key2', paths)
    
    def test_removed_keys(self):
        """Test extraction with removed keys."""
        baseline = {'key1': 'value1', 'key2': 'value2'}
        current = {'key1': 'value1'}
        paths = extract_paths_from_diff(baseline, current)
        self.assertIn('key2', paths)


class TestCmdDiff(unittest.TestCase):
    """Tests for cmd_diff command."""
    
    def setUp(self):
        """Set up test files."""
        # Create baseline file
        self.baseline_data = {'key1': 'value1', 'key2': 'value2'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.baseline_data, f)
            self.baseline_file = f.name
        
        # Create current file (with changes)
        self.current_data = {'key1': 'changed', 'key2': 'value2', 'key3': 'value3'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.current_data, f)
            self.current_file = f.name
        
        # Create policy file
        self.policy_data = {
            'deny': ['key1'],
            'warn': ['key3'],
            'allow': []
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.policy_data, f)
            self.policy_file = f.name
    
    def tearDown(self):
        """Clean up test files."""
        os.unlink(self.baseline_file)
        os.unlink(self.current_file)
        os.unlink(self.policy_file)
    
    def test_no_differences(self):
        """Test diff with no changes."""
        # Create identical files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'key': 'value'}, f)
            same_file = f.name
        
        try:
            args = argparse.Namespace(
                baseline=same_file,
                current=same_file,
                policy=None,
                policy_report='grouped',
                fail_on_change=False
            )
            result = cmd_diff(args)
            self.assertEqual(result, 0)
        finally:
            os.unlink(same_file)
    
    def test_differences_without_policy(self):
        """Test diff with changes but no policy."""
        args = argparse.Namespace(
            baseline=self.baseline_file,
            current=self.current_file,
            policy=None,
            policy_report='grouped',
            fail_on_change=False
        )
        result = cmd_diff(args)
        self.assertEqual(result, 0)
    
    def test_fail_on_change(self):
        """Test --fail-on-change flag."""
        args = argparse.Namespace(
            baseline=self.baseline_file,
            current=self.current_file,
            policy=None,
            policy_report='grouped',
            fail_on_change=True
        )
        result = cmd_diff(args)
        self.assertEqual(result, 2)
    
    def test_policy_with_deny_violations(self):
        """Test policy evaluation with DENY violations."""
        args = argparse.Namespace(
            baseline=self.baseline_file,
            current=self.current_file,
            policy=self.policy_file,
            policy_report='grouped',
            fail_on_change=False
        )
        result = cmd_diff(args)
        self.assertEqual(result, 3)  # DENY violations
    
    def test_policy_without_deny_violations(self):
        """Test policy evaluation without DENY violations."""
        # Create policy without deny patterns matching our changes
        policy_data = {
            'deny': ['nomatch'],
            'warn': ['key1', 'key3'],
            'allow': []
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(policy_data, f)
            temp_policy = f.name
        
        try:
            args = argparse.Namespace(
                baseline=self.baseline_file,
                current=self.current_file,
                policy=temp_policy,
                policy_report='grouped',
                fail_on_change=False
            )
            result = cmd_diff(args)
            self.assertEqual(result, 0)
        finally:
            os.unlink(temp_policy)
    
    def test_policy_report_per_path(self):
        """Test --policy-report per-path option."""
        args = argparse.Namespace(
            baseline=self.baseline_file,
            current=self.current_file,
            policy=self.policy_file,
            policy_report='per-path',
            fail_on_change=False
        )
        result = cmd_diff(args)
        self.assertEqual(result, 3)  # Still has DENY violations


if __name__ == '__main__':
    unittest.main()
