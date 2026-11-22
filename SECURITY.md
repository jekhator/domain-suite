# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability in monitoring-suite, please report it privately using GitHub's security vulnerability reporting feature.

### How to Report

1. Navigate to the repository's **Security** tab
2. Click **Report a vulnerability**
3. Provide details of the vulnerability and steps to reproduce (if applicable)

I appreciate responsible disclosure and will acknowledge receipt of your report promptly.

## Security Considerations

- All domain service inputs are validated and sanitized for injection attacks
- Authorization checks are enforced at decorator and context levels
- Tenancy boundaries are strictly validated
- No sensitive secrets are logged by default
- Error handling preserves security posture while providing useful diagnostics

For detailed security implementation, see the domain documentation in `docs/`.
