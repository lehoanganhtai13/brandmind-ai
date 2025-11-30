#!/usr/bin/env python3
"""
Compare current secrets scan with baseline and report new secrets.
Used by: make secrets-scan
"""
import json
import sys

def main():
    try:
        with open('.secrets.baseline', 'r') as f:
            baseline = json.load(f)
        
        with open('/tmp/secrets-current-scan.json', 'r') as f:
            current = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)
    
    # Create sets of (filename, hashed_secret) tuples for comparison
    baseline_secrets = {
        (file, secret['hashed_secret']): secret
        for file, secrets in baseline.get('results', {}).items()
        for secret in secrets
    }
    
    current_secrets = {
        (file, secret['hashed_secret']): secret
        for file, secrets in current.get('results', {}).items()
        for secret in secrets
    }
    
    # Find new secrets (in current but not in baseline)
    new_secrets = {}
    for (file, hash_val), secret in current_secrets.items():
        if (file, hash_val) not in baseline_secrets:
            if file not in new_secrets:
                new_secrets[file] = []
            new_secrets[file].append(secret)
    
    if new_secrets:
        print('')
        print('🚨 ========================================')
        print('🚨  NEW SECRETS DETECTED IN CODE!')
        print('🚨 ========================================')
        print('')
        
        for file, secrets in sorted(new_secrets.items()):
            lines = ', '.join(str(s['line_number']) for s in secrets)
            print(f'📁 {file}:')
            print(f'   → {len(secrets)} secret(s) found on line(s): {lines}')
            for secret in secrets:
                secret_type = secret.get('type', 'Unknown')
                print(f'      Type: {secret_type}')
            print('')
        
        print('⚠️  Action required:')
        print('   1. Review the files listed above')
        print('   2. Remove the secrets or move them to .env files')
        print('   3. If these are false positives, run: make secrets-audit')
        print('')
        sys.exit(1)
    else:
        print('✅ No new secrets detected in code')
        print('   (.env files are excluded from this check)')
        sys.exit(0)

if __name__ == '__main__':
    main()
