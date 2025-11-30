# Security Guidelines

## Secrets Detection

This project uses `detect-secrets` to prevent accidentally committing API keys, passwords, and other sensitive information to the repository.

### Available Commands

#### 1. Create/Update Baseline
```bash
make secrets-baseline
```
Creates or updates the `.secrets.baseline` file which contains a snapshot of all currently detected secrets in the repository. This file is used as a reference point for future scans.

**When to use:**
- First time setting up secrets detection
- After reviewing and approving legitimate secrets (like test fixtures)
- When you want to update the baseline with new approved secrets

**Note:** .env files are automatically excluded from the baseline - they're allowed to contain secrets.

#### 2. Scan for New Secrets
```bash
make secrets-scan
```
Scans the entire repository for secrets and compares against the baseline. If new secrets are detected, the command will:
- **Exit with error code 1** (fails the build - prevents commits with secrets)
- Display a summary of detected secrets with file names and line numbers
- Show the type of secret detected (API Key, Token, etc.)
- Suggest running `make secrets-audit` to review

**When to use:**
- Before committing code
- In CI/CD pipelines
- Regular security audits

**Note:** This command is automatically run as part of `make typecheck`.

#### 3. Audit Detected Secrets (Interactive)
```bash
make secrets-audit
```
Opens an **interactive interface** to review ALL detected secrets in the baseline. For each secret, you can:

**Options:**
- `(y)es` - Mark as **allowed** - This is a legitimate secret (e.g., config file secret, test fixture). Will be added to baseline and won't trigger errors.
- `(n)o` - Mark as **NOT allowed** - This is a real secret that should NOT be committed. You need to remove it.
- `(s)kip` - Skip this secret for now, review later
- `(b)ack` - Go back to previous secret
- `(q)uit` - Exit the audit

**When to use:**
- After `make secrets-scan` detects new secrets
- To review and classify detected secrets
- To mark legitimate non-secret strings as false positives (e.g., example API keys in documentation)

**Example workflow:**
```bash
# 1. You accidentally added a real API key
make secrets-scan
# → Error: Secret detected in config.py

# 2. Review the secret
make secrets-audit
# → Shows: "STRIPE_KEY = sk_live_abc123..."
# → Choose (n)o - this is a real secret

# 3. Remove the secret, move to .env
mv config.py config.py.bak
# ... move secret to .env file ...

# 4. Scan again
make secrets-scan
# → ✅ No secrets detected
```

### Security Scanning with Bandit

#### Scan src/ folder
```bash
make security-check
```
Runs Bandit security scanner on the `src/` folder only, checking for common security issues in Python code like:
- SQL injection vulnerabilities
- Use of unsafe functions (`eval`, `exec`)
- Weak cryptography
- Path traversal issues

**Note:** This is also automatically run as part of `make typecheck`.

### Workflow Example

```bash
# 1. Initial setup - create baseline (one-time)
make secrets-baseline

# 2. Development workflow - run before every commit
make typecheck
# This automatically runs:
#   - Code formatting
#   - Linting
#   - Security check (bandit)
#   - Secrets scan ← Will fail if API keys detected!

# 3. If secrets are detected - review them
make secrets-audit
# Mark false positives or remove real secrets
```

### What Gets Detected?

The `detect-secrets` tool can identify:
- **API Keys**: AWS, Google Cloud, OpenAI, Azure, etc.
- **Tokens**: GitHub, GitLab, JWT, Discord, Telegram, etc.
- **Passwords**: Hardcoded passwords in code
- **Private Keys**: SSH keys, SSL certificates
- **High Entropy Strings**: Base64, Hex strings that look like secrets
- **Cloud Credentials**: Various cloud provider credentials

### Best Practices

1. **Never commit real secrets** - Use environment variables instead
2. **Run `make secrets-scan` before every commit**
3. **Review the baseline regularly** - Remove outdated entries
4. **Use `.env` files** - Keep them in `.gitignore`
5. **Use secret management tools** - For production secrets (e.g., AWS Secrets Manager, HashiCorp Vault)

### CI/CD Integration

Add to your CI/CD pipeline:

```yaml
# Example for GitHub Actions
- name: Check for secrets
  run: make secrets-scan
```

This will fail the build if new secrets are detected, preventing them from being merged.

### Excluding False Positives

If you have a legitimate string that's being flagged as a secret, you can:

1. **Inline comment** - Add `# pragma: allowlist secret` at the end of the line
2. **Audit and mark** - Use `make secrets-audit` to mark it as a false positive
3. **Update baseline** - Run `make secrets-baseline` after marking false positives

Example:
```python
# This is a test API key, not a real secret
TEST_KEY = "sk-test-1234567890abcdef"  # pragma: allowlist secret
```

### Files Excluded from Scanning

The following directories are automatically excluded:
- `.venv/`, `venv/` - Virtual environments
- `.git/` - Git directory
- `__pycache__/` - Python cache
- `.pytest_cache/`, `.mypy_cache/` - Test and type checking cache
- `node_modules/` - Node.js dependencies

### Need Help?

- Run `make help` to see all available commands
- Check the [detect-secrets documentation](https://github.com/Yelp/detect-secrets)
- Review the Makefile for command details
