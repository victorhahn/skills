# Terraform AWS Best Practices

## Table of Contents
1. [Provider configuration](#provider-configuration)
2. [Module patterns](#module-patterns)
3. [State management](#state-management)
4. [Resource naming and tagging](#resource-naming-and-tagging)
5. [Common resource patterns](#common-resource-patterns)
6. [IAM with Terraform](#iam-with-terraform)
7. [Secrets and sensitive values](#secrets-and-sensitive-values)
8. [Common pitfalls and gotchas](#common-pitfalls-and-gotchas)
9. [Testing and validation](#testing-and-validation)

---

## Provider configuration

### Multi-region and multi-account
```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"  # Always pin major version; verify current at registry.terraform.io/providers/hashicorp/aws
    }
  }
  required_version = ">= 1.9"
}

provider "aws" {
  region = var.aws_region

  # Standard tags applied to every resource that supports them
  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Service     = var.service_name
      Team        = var.team
    }
  }
}

# Secondary region (for DR, global services, etc.)
provider "aws" {
  alias  = "us_west_2"
  region = "us-west-2"

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Cross-account role assumption
provider "aws" {
  alias  = "shared_services"
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::${var.shared_services_account_id}:role/TerraformRole"
  }
}
```

**Always use `default_tags`.** It applies tags to every supported resource without repeating them. Much better than `tags = merge(local.common_tags, {...})` on every resource.

**Pin provider versions with `~>` (pessimistic operator).** `~> 6.0` allows 6.x but not 7.0. Unpinned providers will drift and break.

**Before writing HCL for any resource, verify the current argument schema.** The provider evolves — argument names change, some are removed. The canonical source:
`https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/{resource_name}`

**Notable provider migration history** (relevant if working on existing codebases):
- **v4**: `aws_s3_bucket` in-line config split into separate sub-resources (versioning, encryption, lifecycle, etc.) — if you see inline config, it's a v3 codebase
- **v5**: Provider-level argument renames (`assume_role.duration_seconds` → `duration`, `s3_force_path_style` → `s3_use_path_style`)
- **v6**: `aws_lb_target_group` `preserve_client_ip` must be boolean (`true`/`false`), not string (`"0"`/`"1"`); multi-region support added (resources can take a `region` argument); several end-of-life services removed (OpsWorks, SimpleDB, etc.)

---

## Module patterns

### When to use modules vs. root configuration
- Use modules for things you instantiate more than once (e.g., an ECS service pattern, a VPC, an RDS cluster).
- Don't extract a module for something you have once. One-off resources live in root configuration.
- Prefer flat module trees over deep nesting — `module.vpc.module.subnets.module.nacl` is hard to reason about.

### Module structure
```
modules/
└── ecs-service/
    ├── main.tf          # Resources
    ├── variables.tf     # Inputs (with validation)
    ├── outputs.tf       # Outputs
    └── versions.tf      # Required providers
```

Don't put `provider` blocks in modules — let the root configuration pass them via `providers = {}`.

### Variable validation
```hcl
variable "environment" {
  type        = string
  description = "Deployment environment"
  
  validation {
    condition     = contains(["prod", "staging", "dev"], var.environment)
    error_message = "Environment must be prod, staging, or dev."
  }
}

variable "desired_count" {
  type    = number
  default = 2
  
  validation {
    condition     = var.desired_count >= 1
    error_message = "At least 1 task required."
  }
}
```

### Module versioning (private registry / GitHub)
```hcl
module "vpc" {
  source  = "git::https://github.com/your-org/terraform-modules.git//vpc?ref=v2.3.0"
  # or from TFE private registry:
  # source  = "app.terraform.io/your-org/vpc/aws"
  # version = "~> 2.3"
}
```
Always pin with `ref=` or `version =`. Never use `ref=main`.

---

## State management

### Remote state with S3 + DynamoDB
```hcl
terraform {
  backend "s3" {
    bucket         = "your-org-terraform-state"
    key            = "services/my-service/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
    
    # If using cross-account state bucket:
    role_arn = "arn:aws:iam::${INFRA_ACCOUNT_ID}:role/TerraformStateRole"
  }
}
```

Key requirements for the state bucket:
- **Versioning**: enabled (recovery from accidental state corruption)
- **Encryption**: SSE-S3 or SSE-KMS
- **Block public access**: all four options enabled
- **Bucket policy**: Deny non-TLS access (`aws:SecureTransport = false`)

### State key conventions
Use a path that reflects the hierarchy: `{account}/{region}/{environment}/{service}/terraform.tfstate`

### `terraform_remote_state` (use sparingly)
```hcl
data "terraform_remote_state" "vpc" {
  backend = "s3"
  config = {
    bucket = "your-org-terraform-state"
    key    = "networking/vpc/terraform.tfstate"
    region = "us-east-1"
  }
}

# Then use: data.terraform_remote_state.vpc.outputs.private_subnet_ids
```
The problem: this creates tight coupling between stacks. A change to the VPC outputs can break the app stack's plan. Prefer looking up resources via data sources (e.g., `aws_vpc`, `aws_subnets`) when the dependency is loose.

### Data sources for cross-stack references
```hcl
# Better than remote_state for loosely-coupled dependencies
data "aws_vpc" "main" {
  tags = {
    Environment = var.environment
    Name        = "main-${var.environment}"
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }
  
  tags = {
    Tier = "private"
  }
}
```

---

## Resource naming and tagging

### Naming conventions
```hcl
locals {
  # Consistent name prefix
  name_prefix = "${var.service_name}-${var.environment}"
}

resource "aws_ecs_service" "main" {
  name = local.name_prefix  # my-service-prod
}

resource "aws_cloudwatch_log_group" "main" {
  name = "/ecs/${local.name_prefix}"  # /ecs/my-service-prod
}
```

Use `lower(replace(...))` if names need to be sanitized for resources with strict naming rules (no underscores, etc.).

### Tagging
`default_tags` in the provider handles most tags. For resource-specific tags:
```hcl
resource "aws_s3_bucket" "data" {
  bucket = "${local.name_prefix}-data"
  
  tags = {
    DataClassification = "internal"
    CostCenter         = "platform-12345"
  }
  # default_tags are merged automatically
}
```

---

## Common resource patterns

### ECS Fargate service (complete example)
```hcl
resource "aws_ecs_task_definition" "main" {
  family                   = local.name_prefix
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = var.service_name
    image     = "${aws_ecr_repository.main.repository_url}:${var.image_tag}"
    essential = true
    
    portMappings = [{
      containerPort = var.container_port
      protocol      = "tcp"
    }]
    
    environment = [for k, v in var.env_vars : { name = k, value = v }]
    
    secrets = [for k, v in var.secret_arns : {
      name      = k
      valueFrom = v
    }]
    
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.main.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
    
    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:${var.container_port}/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])
}

resource "aws_ecs_service" "main" {
  name            = local.name_prefix
  cluster         = var.ecs_cluster_id
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.main.arn
    container_name   = var.service_name
    container_port   = var.container_port
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  deployment_controller {
    type = "ECS"
  }

  lifecycle {
    ignore_changes = [desired_count]  # Managed by auto-scaling
  }
}
```

**Note `deployment_circuit_breaker`**: always enable this. It auto-rolls back failed deployments.

**Note `ignore_changes = [desired_count]`**: Required when using Application Auto Scaling, otherwise Terraform will fight the scaler.

### ALB + Target Group
```hcl
resource "aws_lb" "main" {
  name               = local.name_prefix
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.environment == "prod"
  
  access_logs {
    bucket  = var.access_logs_bucket
    prefix  = local.name_prefix
    enabled = true
  }
}

resource "aws_lb_target_group" "main" {
  name        = local.name_prefix
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"  # Required for Fargate awsvpc mode

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }

  deregistration_delay = 30  # Default is 300 — too slow for deployments
}
```

### SQS Queue (with DLQ)
```hcl
resource "aws_sqs_queue" "dlq" {
  name                      = "${local.name_prefix}-dlq"
  message_retention_seconds = 1209600  # 14 days
}

resource "aws_sqs_queue" "main" {
  name                       = local.name_prefix
  visibility_timeout_seconds = 300  # 6x your max processing time
  message_retention_seconds  = 86400  # 1 day; tune to your needs
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_cloudwatch_metric_alarm" "dlq_depth" {
  alarm_name          = "${local.name_prefix}-dlq-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Maximum"
  threshold           = 0
  alarm_description   = "Messages in DLQ — requires investigation"
  
  dimensions = {
    QueueName = aws_sqs_queue.dlq.name
  }
  
  alarm_actions = [var.sns_alert_topic_arn]
}
```

Always add a CloudWatch alarm on DLQ depth > 0. DLQ messages mean failures.

---

## IAM with Terraform

### Least-privilege task role
```hcl
resource "aws_iam_role" "ecs_task" {
  name = "${local.name_prefix}-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = {
        StringEquals = {
          "aws:SourceAccount" = data.aws_caller_identity.current.account_id
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "ecs_task" {
  name = "app-permissions"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query"
        ]
        Resource = [
          aws_dynamodb_table.main.arn,
          "${aws_dynamodb_table.main.arn}/index/*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["sqs:SendMessage", "sqs:GetQueueUrl"]
        Resource = aws_sqs_queue.main.arn
      }
    ]
  })
}
```

Use inline policies (`aws_iam_role_policy`) for service-specific permissions — they're attached directly to the role and deleted with it. Use managed policies (`aws_iam_role_policy_attachment`) for AWS-managed policies like `AmazonECSTaskExecutionRolePolicy`.

### The `aws:SourceAccount` condition
Add this to all service trust policies. It prevents the confused deputy attack where another account's ECS task impersonates yours. Terraform example above includes it.

---

## Secrets and sensitive values

### Pattern: Secrets Manager + ECS task definition
```hcl
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${local.name_prefix}/db-password"
  recovery_window_in_days = 7
}

# Grant the task execution role access to fetch this secret
resource "aws_iam_role_policy" "ecs_execution_secrets" {
  name = "secrets-access"
  role = aws_iam_role.ecs_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = [aws_secretsmanager_secret.db_password.arn]
    }]
  })
}
```

Then in the container definition, reference via `secrets`:
```json
"secrets": [
  {
    "name": "DB_PASSWORD",
    "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:my-service/db-password"
  }
]
```

### Never use `sensitive = false` to work around Terraform masking
If Terraform masks a value and you need to debug, use `terraform output -json` or check the state file (with appropriate access controls). Don't expose secrets in outputs.

### SSM Parameter Store vs Secrets Manager
- **Secrets Manager**: Rotation support, cross-account sharing, higher cost ($0.40/secret/month). Use for passwords, API keys, certificates.
- **SSM Parameter Store (SecureString)**: Cheaper (free tier for standard, $0.05/advanced), no rotation. Use for config values that need to be secret but don't rotate.

---

## Common pitfalls and gotchas

### 1. `count` vs `for_each` — use `for_each` for anything addressable
```hcl
# BAD: if you remove index 0 from the list, everything re-indexes
resource "aws_iam_role_policy_attachment" "policies" {
  count      = length(var.policy_arns)
  role       = aws_iam_role.main.name
  policy_arn = var.policy_arns[count.index]
}

# GOOD: stable keys, removals only affect the removed resource
resource "aws_iam_role_policy_attachment" "policies" {
  for_each   = toset(var.policy_arns)
  role       = aws_iam_role.main.name
  policy_arn = each.value
}
```

### 2. The `depends_on` trap
`depends_on` is a code smell — it usually means the dependency isn't being expressed through resource references. If you're adding `depends_on`, ask whether you can instead use the resource attribute directly (e.g., `aws_iam_role.main.name` instead of a string and `depends_on`).

Legitimate uses: module-level `depends_on` when a module creates IAM permissions that another module needs to work.

### 3. Security groups: ingress/egress rules as separate resources
```hcl
# BAD: inline rules conflict with aws_security_group_rule resources
resource "aws_security_group" "app" {
  name   = "app"
  vpc_id = var.vpc_id

  ingress {  # Don't do this if you also have aws_security_group_rule resources
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

Either use inline rules exclusively OR `aws_security_group_rule` exclusively for a given SG. Mixing causes perpetual drift.

### 4. IAM policy JSON encoding
Use `jsonencode()` over heredoc or `data.aws_iam_policy_document`:
- `jsonencode()`: Clean HCL, easy to review, catches syntax errors at plan time
- `aws_iam_policy_document` data source: More verbose but gives you attribute references — useful for complex policies with dynamic conditions
- Heredoc strings: No validation, prone to JSON errors, hard to read

### 5. `lifecycle { prevent_destroy = true }` for production data
```hcl
resource "aws_dynamodb_table" "main" {
  # ...
  
  lifecycle {
    prevent_destroy = true  # Requires explicit removal before destroy
  }
}
```
Add this to any resource where accidental deletion would be catastrophic: RDS instances, DynamoDB tables, S3 buckets with data, Secrets Manager secrets.

### 6. ECS task definition container image tags
Don't use `latest` as the image tag in Terraform — it makes deployments non-deterministic and prevents rollback:
```hcl
# BAD
image = "${aws_ecr_repository.main.repository_url}:latest"

# GOOD
image = "${aws_ecr_repository.main.repository_url}:${var.image_tag}"
```
Pass `image_tag` as a variable from CI/CD. This makes deployments traceable and rollbacks simple.

### 7. S3 bucket configuration: separate resources per concern
AWS provider v4+ requires separate resources for bucket configuration:
```hcl
resource "aws_s3_bucket" "main" {
  bucket = local.name_prefix
}

resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "main" {
  bucket                  = aws_s3_bucket.main.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

### 8. CloudWatch Log Group creation before ECS service
ECS will try to create the log group if it doesn't exist, but Terraform should create it explicitly so you can control retention:
```hcl
resource "aws_cloudwatch_log_group" "main" {
  name              = "/ecs/${local.name_prefix}"
  retention_in_days = 30
}
```
Without this, the log group is created with "never expire" retention and you'll pay indefinitely.

---

## Testing and validation

### terraform validate + tflint
```bash
# In CI/CD
terraform init -backend=false
terraform validate
tflint --enable-plugin=aws
```

### checkov for security scanning
```bash
checkov -d . --framework terraform
```
Common rules to pay attention to: encryption at rest, public access on S3/RDS/SG, CloudWatch logging enabled, deletion protection on databases.

### Terratest (Go-based integration tests)
For modules, write actual integration tests that provision real resources in a test account and assert on their properties. More expensive to run but catches things `validate` can't.

### Pre-plan checks in TFE/TFC
Use Sentinel policies or OPA policies to enforce organizational standards before plans can be applied:
- Require specific tags
- Deny public S3 buckets
- Enforce encryption
- Block non-compliant instance types
