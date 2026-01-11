# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: Supported |
| < 1.0   | :x: Not supported  |

## Reporting a Vulnerability

We take the security of cc2oc-bridge seriously. If you discover a security vulnerability, please follow these steps:

### DO NOT:

- Do NOT open a public issue on GitHub
- Do NOT post about the vulnerability on social media
- Do NOT share details in public forums or chat rooms

### DO:

1. **Email us directly**: Send a detailed report to **security@cc2oc-bridge.dev**
2. **Use our PGP key** (see below) to encrypt sensitive information
3. **Wait for our response**: We aim to respond within 48 hours
4. **Allow time for investigation**: We'll work with you to understand and fix the issue

### What to Include in Your Report

Please provide as much information as possible:

- **Description**: Clear description of the vulnerability
- **Steps to Reproduce**: Step-by-step instructions to reproduce
- **Impact**: What could an attacker do with this?
- **Affected Versions**: Which versions are vulnerable?
- **Potential Fixes**: Any suggestions for fixing the issue
- **Your Contact Info**: How we can reach you (optional but helpful)

### Our PGP Key

For encrypting sensitive vulnerability reports:

```
-----BEGIN PGP PUBLIC KEY BLOCK-----

mQINBGWXYZ... [Your PGP key here]

-----END PGP PUBLIC KEY BLOCK-----
```

**Fingerprint**: `ABCD 1234 5678 90EF GHIJ KLMN OPQR 5678 90AB CDEF`

### What Happens Next

1. **Acknowledgment**: We'll confirm receipt within 48 hours
2. **Investigation**: We'll investigate and validate the vulnerability
3. **Fix Development**: We'll develop a fix (with your help if possible)
4. **Testing**: We'll thoroughly test the fix
5. **Release**: We'll release the fix with proper credit
6. **Disclosure**: We'll coordinate public disclosure with you

## Security Best Practices for Users

### Installation

- Always download from official sources
- Verify checksums when available
- Keep the bridge updated to the latest version
- Review plugin code before installation

### Plugin Security

- Only install plugins from trusted sources
- Review plugin permissions and tool access
- Use tool restrictions to limit plugin capabilities
- Monitor plugin behavior for suspicious activity

### Configuration

- Use tool restrictions to limit what plugins can do
- Configure hooks to audit sensitive operations
- Regularly review installed plugins
- Keep OpenCode and the bridge updated

## Known Security Considerations

### Current Limitations

1. **Prompt Injection**: The bridge relies on LLM instruction following. Maliciously crafted prompts could potentially bypass restrictions.
2. **Tool Access**: Plugins have access to tools (Read, Write, Bash, etc.) based on their configuration.
3. **Path Traversal**: Plugins could potentially access files outside their intended scope.
4. **Hook Bypass**: Determined plugins might find ways to bypass hook restrictions.

### Mitigations

- Tool restrictions are enforced at the bridge level
- Hooks provide audit and blocking capabilities
- Path rewriting prevents absolute path access
- Model capabilities affect security enforcement quality

## Security Features

### Tool Restrictions

Plugins can specify allowed and disallowed tools:

```yaml
allowed-tools:
  - Bash(git:*)
  - Read
  - Write(*.md)
```

### Hooks for Security

Use hooks to audit or block operations:

```json
{
  "PreToolUse": [{
    "matcher": "Bash",
    "command": "./security-check.sh",
    "timeout": 30
  }]
}
```

### Path Sandboxing

The bridge rewrites paths to prevent access outside plugin directories.

## Vulnerability Disclosure Policy

### Responsible Disclosure

We follow responsible disclosure principles:

1. **Private Reporting**: Vulnerabilities reported privately
2. **Reasonable Time**: We aim to fix issues within 90 days
3. **Coordinated Disclosure**: We coordinate public disclosure with reporters
4. **Credit**: We give credit to security researchers
5. **No Legal Threats**: We won't pursue legal action for good-faith research

### Safe Harbor

We support safe harbor for security research:

- We won't pursue legal action for good-faith security research
- We ask that you follow responsible disclosure
- We appreciate researchers who help improve our security

## Security Updates

### Security Advisories

We'll publish security advisories for significant vulnerabilities:

- GitHub Security Advisories
- Email notifications to subscribers
- Release notes with security fixes

### Subscribing to Security Updates

- Watch the repository on GitHub
- Enable security alerts in your GitHub settings
- Check release notes for security-related fixes

## Contact

### Security Team

- **Email**: security@cc2oc-bridge.dev
- **Response Time**: Within 48 hours
- **Encryption**: PGP available (see above)

### Emergency Contact

For critical security issues requiring immediate attention:

- **Emergency Email**: security-emergency@cc2oc-bridge.dev
- **Response Time**: Within 4 hours during business days

## Acknowledgments

We appreciate the security community's efforts to make cc2oc-bridge safer for everyone. Thank you for helping us maintain a secure environment for all users.

### Hall of Fame

Security researchers who have responsibly disclosed vulnerabilities:

- [Researcher Name] - [Brief description of contribution]
- [Your name could be here!]

---

**Thank you for helping keep cc2oc-bridge and its users safe!** 🔒

*This security policy is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*