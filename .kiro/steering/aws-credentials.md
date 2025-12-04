---
inclusion: always
---

# AWS Credentials Reminder

When working with AWS CLI commands or CDK deployments:

1. **Check credentials first**: Before running AWS commands, verify the current AWS identity with `aws sts get-caller-identity`

2. **Prompt for credentials**: If credentials are expired or for wrong account, ask the user to provide new credentials:
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - AWS_SESSION_TOKEN (for temporary credentials)
   - AWS_DEFAULT_REGION

3. **Set credentials in session**: Use `export` commands to set credentials before AWS operations

4. **Target account**: The workshop account is `692859950494` in `us-west-2` region

5. **Credential expiration**: Session tokens expire - if AWS commands fail with authentication errors, prompt for fresh credentials
