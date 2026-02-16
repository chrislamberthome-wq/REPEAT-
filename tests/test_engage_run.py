"""Tests for the engage_run tool."""

import pytest
import tempfile
import shutil
from pathlib import Path
import json
import sys
import os
import uuid

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools'))

from engage_run import main
import argparse


class TestEngageRun:
    """Tests for engage_run.py output directory structure."""
    
    def test_output_directory_structure(self):
        """Test that output follows the engage-v1/<run_id>/... structure."""
        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Mock sys.argv to simulate command-line arguments
            original_argv = sys.argv
            try:
                sys.argv = [
                    'engage_run.py',
                    '--out-dir', tmp_dir,
                    '--name', 'test_run'
                ]
                
                # Run the main function
                result = main()
                assert result == 0
                
                # Check that engage-v1 directory was created
                engage_v1_dir = Path(tmp_dir) / 'engage-v1'
                assert engage_v1_dir.exists(), "engage-v1 directory should exist"
                assert engage_v1_dir.is_dir(), "engage-v1 should be a directory"
                
                # Check that a run_id directory was created under engage-v1
                run_dirs = list(engage_v1_dir.iterdir())
                assert len(run_dirs) == 1, "Should have exactly one run directory"
                
                run_dir = run_dirs[0]
                assert run_dir.is_dir(), "run_id should be a directory"
                
                # Check that metadata.json exists in the run directory
                metadata_file = run_dir / 'metadata.json'
                assert metadata_file.exists(), "metadata.json should exist"
                
                # Verify metadata content
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                assert 'run_id' in metadata
                assert 'name' in metadata
                assert metadata['name'] == 'test_run'
                assert 'timestamp' in metadata
                assert 'output_dir' in metadata
                
                # Check that results subdirectory exists
                results_dir = run_dir / 'results'
                assert results_dir.exists(), "results directory should exist"
                assert results_dir.is_dir(), "results should be a directory"
                
            finally:
                sys.argv = original_argv
    
    def test_output_directory_not_direct_run_id(self):
        """Test that output is NOT written directly to out_dir/run_id."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_argv = sys.argv
            try:
                sys.argv = [
                    'engage_run.py',
                    '--out-dir', tmp_dir,
                ]
                
                result = main()
                assert result == 0
                
                tmp_path = Path(tmp_dir)
                
                # Ensure engage-v1 is present
                assert (tmp_path / 'engage-v1').exists()
                
                # Get all directories in tmp_dir
                top_level_dirs = [d for d in tmp_path.iterdir() if d.is_dir()]
                
                # The only top-level directory should be 'engage-v1'
                assert len(top_level_dirs) == 1
                assert top_level_dirs[0].name == 'engage-v1'
                
                # Run ID should be nested under engage-v1, not at top level
                engage_v1_subdirs = list((tmp_path / 'engage-v1').iterdir())
                assert len(engage_v1_subdirs) == 1
                
                # The subdirectory name should be a valid UUID
                run_id_dir = engage_v1_subdirs[0]
                try:
                    uuid.UUID(run_id_dir.name)
                except ValueError:
                    pytest.fail(f"Directory name '{run_id_dir.name}' is not a valid UUID")
                
            finally:
                sys.argv = original_argv
    
    def test_dry_run_does_not_create_files(self):
        """Test that --dry-run flag doesn't create files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_argv = sys.argv
            try:
                sys.argv = [
                    'engage_run.py',
                    '--out-dir', tmp_dir,
                    '--dry-run'
                ]
                
                result = main()
                assert result == 0
                
                # Check that no directories were created
                tmp_path = Path(tmp_dir)
                created_items = list(tmp_path.iterdir())
                assert len(created_items) == 0, "Dry run should not create any files or directories"
                
            finally:
                sys.argv = original_argv
    
    def test_multiple_runs_create_separate_directories(self):
        """Test that multiple runs create separate run directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_argv = sys.argv
            try:
                # Run twice
                for i in range(2):
                    sys.argv = [
                        'engage_run.py',
                        '--out-dir', tmp_dir,
                        '--name', f'run_{i}'
                    ]
                    
                    result = main()
                    assert result == 0
                
                # Check that engage-v1 directory exists
                engage_v1_dir = Path(tmp_dir) / 'engage-v1'
                assert engage_v1_dir.exists()
                
                # Check that two separate run directories were created
                run_dirs = list(engage_v1_dir.iterdir())
                assert len(run_dirs) == 2, "Should have two separate run directories"
                
                # Verify they have different run_ids
                run_ids = set()
                for run_dir in run_dirs:
                    metadata_file = run_dir / 'metadata.json'
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    run_ids.add(metadata['run_id'])
                
                assert len(run_ids) == 2, "Run IDs should be unique"
                
            finally:
                sys.argv = original_argv
    
    def test_path_components(self):
        """Test the specific path components required by the issue."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_argv = sys.argv
            try:
                sys.argv = [
                    'engage_run.py',
                    '--out-dir', tmp_dir,
                ]
                
                result = main()
                assert result == 0
                
                tmp_path = Path(tmp_dir)
                engage_v1_path = tmp_path / 'engage-v1'
                
                # Verify the path structure
                assert engage_v1_path.exists()
                
                # Get the run directory
                run_dirs = list(engage_v1_path.iterdir())
                assert len(run_dirs) == 1
                run_dir = run_dirs[0]
                
                # Verify the complete path follows: out_dir/engage-v1/<run_id>/...
                assert run_dir.parent.name == 'engage-v1'
                assert run_dir.parent.parent == tmp_path
                
            finally:
                sys.argv = original_argv
