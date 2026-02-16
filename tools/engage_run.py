#!/usr/bin/env python3
"""Engage runner tool for REPEAT- project."""

import argparse
import sys
from pathlib import Path
import uuid
import json
from datetime import datetime, timezone


def main():
    """Main entry point for the engage runner."""
    parser = argparse.ArgumentParser(
        prog='engage_run',
        description='Run engage processes with versioned output structure'
    )
    
    parser.add_argument(
        '--out-dir',
        dest='out_dir',
        required=True,
        type=str,
        help='Base output directory for engage results'
    )
    
    parser.add_argument(
        '--name',
        type=str,
        default='default',
        help='Name for this run'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform a dry run without writing files'
    )
    
    args = parser.parse_args()
    
    # Generate unique run ID
    run_id = str(uuid.uuid4())
    
    # Build output directory path following the structure:
    # out_dir/engage-v1/<run_id>/...
    base_output = Path(args.out_dir)
    versioned_output = base_output / 'engage-v1' / run_id
    
    # Create output directories
    if not args.dry_run:
        versioned_output.mkdir(parents=True, exist_ok=True)
        
        # Write run metadata
        metadata = {
            'run_id': run_id,
            'name': args.name,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'output_dir': str(versioned_output)
        }
        
        metadata_file = versioned_output / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Create results subdirectory
        results_dir = versioned_output / 'results'
        results_dir.mkdir(exist_ok=True)
        
        print(f"Run ID: {run_id}")
        print(f"Output directory: {versioned_output}")
        print(f"Metadata written to: {metadata_file}")
    else:
        print(f"[DRY RUN] Would create output at: {versioned_output}")
        print(f"[DRY RUN] Run ID would be: {run_id}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
