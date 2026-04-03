# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Knowledge OS seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Please do not report security vulnerabilities through public GitHub issues.

Instead, please report them via email to: **security@knowledge-os.local** (replace with your actual security email)

Please include the following information in your report:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### Response Timeline

We will acknowledge receipt of your vulnerability report within 48 hours and will send you a more detailed response within 72 hours indicating the next steps in handling your report.

After the initial reply to your report, we will endeavor to keep you informed of the progress towards a fix and full announcement, and may ask for additional information or guidance.

### Disclosure Policy

When we receive a security bug report, we will:

1. Confirm the problem and determine the affected versions
2. Audit code to find any similar problems
3. Prepare fixes for all supported versions
4. Release new versions and announce the issue

### Security Best Practices

When deploying Knowledge OS:

1. **Use HTTPS** - Always use HTTPS in production
2. **Keep dependencies updated** - Regularly update all dependencies
3. **Use strong passwords** - If authentication is enabled, use strong passwords
4. **Limit network exposure** - Don't expose Qdrant directly to the internet
5. **Regular backups** - Enable automatic backups
6. **Monitor logs** - Regularly check application logs for suspicious activity

### Security Features

Knowledge OS includes several security features:

- Input validation on all API endpoints
- CORS configuration
- Security headers in nginx
- Docker security best practices
- Dependency scanning in CI/CD
