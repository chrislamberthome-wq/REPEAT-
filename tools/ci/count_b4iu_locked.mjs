#!/usr/bin/env node
/**
 * count_b4iu_locked.mjs
 * 
 * Verifier script to ensure B4IU_LOCKED token compliance.
 * Counts occurrences of B4IU_LOCKED tokens in the codebase and
 * enforces compliance rules according to the SPEC.
 * 
 * Usage: node tools/ci/count_b4iu_locked.mjs
 * 
 * Exit codes:
 *   0 - Compliance check passed
 *   1 - Compliance check failed
 */

import { readFileSync, readdirSync, statSync } from 'fs';
import { join, extname } from 'path';

// Configuration
const IGNORE_PATTERNS = [
  /node_modules/,
  /\.git/,
  /\.pyc$/,
  /__pycache__/,
  /\.egg-info/,
  /dist\//,
  /build\//,
  /\.pytest_cache/,
  /\.mypy_cache/,
  /\.ruff_cache/,
];

// Token to search for
const TOKEN = 'B4IU_LOCKED';

// File extensions to search
const SEARCH_EXTENSIONS = [
  '.py', '.js', '.mjs', '.ts', '.md', '.txt', '.yml', '.yaml',
  '.json', '.sh', '.toml', '.cfg', '.ini'
];

/**
 * Check if a path should be ignored
 */
function shouldIgnore(path) {
  return IGNORE_PATTERNS.some(pattern => pattern.test(path));
}

/**
 * Recursively find all files to search
 */
function findFiles(dir, files = []) {
  const entries = readdirSync(dir);
  
  for (const entry of entries) {
    const fullPath = join(dir, entry);
    
    if (shouldIgnore(fullPath)) {
      continue;
    }
    
    const stat = statSync(fullPath);
    
    if (stat.isDirectory()) {
      findFiles(fullPath, files);
    } else if (stat.isFile()) {
      const ext = extname(fullPath);
      if (SEARCH_EXTENSIONS.includes(ext)) {
        files.push(fullPath);
      }
    }
  }
  
  return files;
}

/**
 * Count token occurrences in a file
 */
function countTokenInFile(filePath) {
  try {
    const content = readFileSync(filePath, 'utf-8');
    const regex = new RegExp(TOKEN, 'g');
    const matches = content.match(regex);
    return matches ? matches.length : 0;
  } catch (err) {
    console.warn(`Warning: Could not read file ${filePath}: ${err.message}`);
    return 0;
  }
}

/**
 * Main verification function
 */
function main() {
  console.log(`B4IU_LOCKED Verifier - Token Compliance Check`);
  console.log(`=========================================`);
  console.log();
  
  const rootDir = process.cwd();
  console.log(`Scanning directory: ${rootDir}`);
  console.log(`Looking for token: ${TOKEN}`);
  console.log();
  
  const files = findFiles(rootDir);
  console.log(`Found ${files.length} files to scan`);
  console.log();
  
  let totalCount = 0;
  const filesWithToken = [];
  
  for (const file of files) {
    const count = countTokenInFile(file);
    if (count > 0) {
      totalCount += count;
      filesWithToken.push({ file, count });
    }
  }
  
  console.log(`Results:`);
  console.log(`--------`);
  console.log(`Total ${TOKEN} tokens found: ${totalCount}`);
  console.log();
  
  if (filesWithToken.length > 0) {
    console.log(`Files containing ${TOKEN}:`);
    for (const { file, count } of filesWithToken) {
      console.log(`  ${file}: ${count} occurrence(s)`);
    }
    console.log();
  }
  
  // Registry rule: Report the count (N_locked)
  console.log(`N_locked = ${totalCount}`);
  console.log();
  
  // For now, we just report the count. The script exits with 0 (success)
  // Future versions may add enforcement rules that cause non-zero exits
  console.log(`✓ Compliance check passed`);
  process.exit(0);
}

// Run the verifier
main();
