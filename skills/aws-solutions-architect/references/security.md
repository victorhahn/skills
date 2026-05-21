# AWS Security Best Practices

## Table of Contents
1. [IAM design](#iam-design)
2. [VPC security](#vpc-security)
3. [Secrets and credentials](#secrets-and-credentials)
4. [Encryption](#encryption)
5. [Compliance and audit](#compliance-and-audit)
6. [Anti-patterns](#anti-patterns)

---

## IAM design

### Least privilege — operationalized
"Least privilege" is easy to say and hard to do consistently. Practical approach:

1. Start from what your service actually calls. For ECS/Lambda, enable CloudTrail in a dev account, run your service through its real flows, then use IAM Access Analyzer to generate a policy from the CloudTrail events. This gives you a data-driven minimal policy rather than a guess.
2. Scope resources as tightly as possible — not just actions. `dynamodb:GetItem` on `*` is still overly broad. Scope to the specific table ARN.
3. Add `Condition` clauses for cross-service trust. `aws:SourceAccount` and `aws:SourceArn` on service trust policies prevent confused deputy attacks.

### Roles, not users
No human should have long-lived IAM user access keys for production. Use:
- **AWS SSO / IAM Identity Center**: federated access with short-lived credentials, MFA enforced, audit trail
- **Task/execution roles**: for workloads running on AWS (ECS, Lambda, EC2 instance profiles)
- **Cross-account role assumption** + `sts:AssumeRole`: for CI/CD pipelines and cross-account automation

If you find long-lived IAM user access keys in use, that's tech debt worth prioritizing.

### Permission boundaries
When allowing developers to create IAM roles (e.g., in a dev account), attach a permission boundary that caps what those roles can do. Prevents privilege escalation via self-created roles:

```hcl
resource "aws_iam_role" "developer_created" {
  name                 = "my-service-role"
  assume_role_policy   = data.aws_iam_policy_document.trust.json
  permissions_boundary = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/DeveloperBoundary"
}
```

### Service Control Policies (SCPs)
SCPs at the AWS Organizations level are your last line of defense — they override even `AdministratorAccess`. Useful guardrails:
- Deny all actions outside approved regions (limits blast radius of compromised credentials)
- Deny root account usage
- Require MFA for console access
- Prevent disabling CloudTrail or GuardDuty
- Deny creating IAM users with long-lived credentials in prod accounts

SCPs are `DENY` by default — an SCP doesn't grant permissions, it restricts what's possible within the account.

### IAM Access Analyzer
Run IAM Access Analyzer in every account to identify:
- Resources with public access (S3 buckets, SQS queues, KMS keys, Lambda functions)
- Cross-account access that wasn't explicitly intended
- Unused access in existing roles (the "unused access" analyzer feature)

The "unused access" findings are gold for least-privilege cleanup — it tells you which permissions haven't been used in 90 days.

---

## VPC security

### Security group rules: source-to-source, not CIDR
Inside a VPC, reference security groups rather than CIDR blocks. The rule "allow port 5432 from the app's security group ID" is clearer, automatically updates when app instances change, and is easier to audit than "allow port 5432 from 10.0.0.0/8":

```hcl
# ❌ CIDR-based (ambiguous, hard to audit)
resource "aws_security_group_rule" "db_ingress" {
  type        = "ingress"
  from_port   = 5432
  to_port     = 5432
  protocol    = "tcp"
  cidr_blocks = ["10.0.0.0/8"]
  security_group_id = aws_security_group.db.id
}

# ✅ Security-group-to-security-group (explicit, auditable)
resource "aws_security_group_rule" "db_ingress" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.app.id
  security_group_id        = aws_security_group.db.id
}
```

### Network ACLs vs security groups
Security groups are stateful (return traffic is automatically allowed) and operate at the instance/ENI level. NACLs are stateless and operate at the subnet level — both directions must be explicitly allowed.

In practice: security groups are your primary network control layer. NACLs are a second layer for subnet-level blocking (e.g., blocking a known malicious CIDR range, or a hard deny that doesn't depend on security group correctness).

### Private subnets
- Databases, queues, and internal services: always in private subnets.
- ECS tasks: private subnets. The ALB sits in the public subnet and routes in.
- Lambda in a VPC: private subnet. Lambda being in a VPC mainly matters for accessing VPC resources (RDS, ElastiCache) — it doesn't add significant security otherwise.

### IMDSv2 enforcement
EC2 instance metadata service (IMDS) v1 can be accessed without authentication, making it exploitable via SSRF. Enforce IMDSv2 (requires a session token):

```hcl
resource "aws_launch_template" "main" {
  metadata_options {
    http_tokens                 = "required"  # IMDSv2 only
    http_put_response_hop_limit = 1           # Prevent container metadata leakage
  }
}
```

For ECS on Fargate, IMDSv2 is the default. For EC2-based ECS, enforce it in the launch template.

---

## Secrets and credentials

### Hierarchy of secrets management
From best to worst:
1. **IAM roles + AWS services** — no secret needed at all (ECS task role calling DynamoDB)
2. **Secrets Manager** — managed rotation, cross-account sharing, fine-grained access control
3. **SSM Parameter Store (SecureString)** — cheaper, no rotation, good for config that needs to be secret
4. **Environment variables** — acceptable for non-sensitive config, never for secrets
5. **Hardcoded in code** — never

### Secrets Manager rotation
For RDS passwords, use the built-in rotation Lambda that AWS provides:
```hcl
resource "aws_secretsmanager_secret_rotation" "db" {
  secret_id           = aws_secretsmanager_secret.db_password.id
  rotation_lambda_arn = aws_lambda_function.rotate_db.arn  # AWS provides this

  rotation_rules {
    automatically_after_days = 30
  }
}
```

The rotation Lambda must be in the same VPC as the database (or use VPC endpoint to Secrets Manager) to actually connect and rotate.

### Detecting leaked credentials
Enable **AWS GuardDuty** — it has specific findings for credentials used outside AWS (credential exfiltration to another IP), unusual API call patterns, and known threat actor behaviors. It also integrates with Security Hub for centralized findings.

Additionally: configure a CloudTrail alarm for any `sts:AssumeRole` or `console:Login` from an unexpected IP, and for root account usage.

---

## Encryption

### At rest
- **S3**: SSE-S3 (AES-256, AWS-managed) is sufficient for most data. SSE-KMS for data that needs a separate audit trail of who decrypted what, or for compliance requirements. Customer-managed KMS keys (CMKs) are worth it when you need to be able to revoke access by disabling the key.
- **RDS**: Encryption is enabled at creation time and can't be changed after — don't forget to enable it. Encrypted snapshots can be copied and restored, but an unencrypted RDS can't be "encrypted in place."
- **EBS**: Encrypt all volumes. Set the account-level default to encrypt all new EBS volumes: `aws ec2 enable-ebs-encryption-by-default`.
- **DynamoDB**: Always encrypted at rest using AWS-managed keys; CMK if compliance requires customer key control.
- **SQS, SNS, CloudWatch Logs**: Support SSE. Enable for sensitive data.

### In transit
- **TLS everywhere**: ALB to service (use HTTPS on the target group if the service speaks TLS, or HTTP if it's within the VPC and the ALB terminates TLS — the latter is acceptable for VPC-internal traffic with appropriate network controls).
- **RDS**: Enforce TLS via the parameter group (`require_secure_transport = 1` for MySQL/Aurora MySQL; `rds.force_ssl = 1` for Postgres/Aurora Postgres).
- **S3**: Bucket policy to deny non-TLS access:
  ```json
  {
    "Effect": "Deny",
    "Principal": "*",
    "Action": "s3:*",
    "Resource": ["arn:aws:s3:::bucket/*"],
    "Condition": {"Bool": {"aws:SecureTransport": "false"}}
  }
  ```

---

## Compliance and audit

### CloudTrail
Enable CloudTrail in every account and region. Key configuration:
- **Multi-region trail**: one trail covering all regions (catches activity in regions you're not actively using)
- **S3 data events**: off by default, expensive, but required for compliance if you're auditing S3 object access
- **Log file validation**: enables you to detect if log files were tampered with
- **CloudWatch Logs integration**: stream CloudTrail to CloudWatch for real-time alerting on specific API calls

Critical alarms to set on CloudTrail events:
- Root account login
- IAM policy changes
- Security group changes
- VPC/network changes
- CloudTrail itself being stopped or modified

### Config
AWS Config records configuration state of resources over time and evaluates against rules. Useful for:
- Detecting configuration drift (security group opened to 0.0.0.0/0)
- Compliance reporting (are all S3 buckets encrypted?)
- Change history ("what did this security group look like 3 months ago?")

Enable Config in every account. AWS Managed Rules that are worth enabling by default: `s3-bucket-public-read-prohibited`, `rds-instance-public-access-check`, `restricted-ssh`, `encrypted-volumes`.

### Security Hub
Aggregates findings from GuardDuty, Inspector, Config, Macie, and IAM Access Analyzer into one place. Scores your posture against AWS Foundational Security Best Practices and CIS Benchmarks. Worth enabling as a baseline — the noise from low-severity findings is manageable once you suppress known non-issues.

---

## Anti-patterns

### ❌ Wildcard actions on production resources
```json
{ "Effect": "Allow", "Action": "s3:*", "Resource": "*" }
```
This grants read, write, delete, and ACL modification on every S3 bucket in the account. Scope to specific actions and specific resource ARNs.

### ❌ Sharing KMS keys across unrelated workloads
If you use a single KMS key for encrypting your RDS instance, S3 buckets, Secrets Manager secrets, and SQS queues, then anyone with `kms:Decrypt` has access to everything. Separate CMKs per service or per sensitivity level.

### ❌ Security groups as a substitute for IAM
Security groups control network access; they don't grant or restrict API-level permissions. An ECS task in a private subnet with an overly broad task role can still exfiltrate data via the AWS API — the VPC doesn't stop it. Both layers matter.

### ❌ Long-lived credentials in CI/CD
GitHub Actions, Jenkins, etc. — don't store long-lived AWS access keys as secrets. Use OIDC federation: CI providers can assume an IAM role via a short-lived token tied to the specific repo and branch. No keys to rotate, no keys to leak.

### ❌ Not enabling MFA delete on S3 buckets with critical data
Without MFA delete, any credential with `s3:DeleteObject` can permanently delete objects even if versioning is enabled. For compliance-critical or audit log buckets, enable MFA delete.

### ❌ Over-relying on VPC for security
Being "inside the VPC" is not a sufficient security model. Lateral movement within a VPC is real. Layer your controls: security groups, IAM roles, encryption at rest, secrets management, and audit logging all matter independently of whether traffic is within the VPC.
