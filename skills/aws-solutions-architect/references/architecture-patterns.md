# AWS Architecture Patterns

## Table of Contents
1. [Multi-tier web application](#multi-tier-web-application)
2. [Event-driven / async processing](#event-driven--async-processing)
3. [Serverless API](#serverless-api)
4. [Containerized microservices (ECS)](#containerized-microservices-ecs)
5. [Data pipeline / streaming](#data-pipeline--streaming)
6. [Multi-account strategy](#multi-account-strategy)
7. [Availability and resilience patterns](#availability-and-resilience-patterns)
8. [Caching strategies](#caching-strategies)
9. [IAM design patterns](#iam-design-patterns)
10. [Networking patterns](#networking-patterns)

---

## Multi-tier web application

**Standard pattern (RVO Health context: ECS + RDS/DynamoDB)**

```
Internet → CloudFront → ALB (public subnet) → ECS Fargate tasks (private subnet) → RDS/DynamoDB (private/isolated subnet)
```

Key decisions:
- **CloudFront in front of ALB**: Always do this for public-facing apps. WAF attachment, SSL termination, edge caching, DDoS mitigation at no extra latency cost.
- **ALB over NLB**: Unless you need static IPs, TCP passthrough, or extreme low-latency Layer 4 routing.
- **Target group health checks**: Don't use the default `/` unless it returns 200. Create a dedicated `/health` or `/healthz` endpoint that checks DB connectivity (or not — depends on your failure modes).
- **Sticky sessions**: Avoid. Design stateless services; push state to Redis/DynamoDB.

---

## Event-driven / async processing

**Pattern: SQS + Lambda or SQS + ECS task**

```
Producer → SQS Standard Queue → Lambda / ECS task → downstream
                ↓ (on failure)
            Dead Letter Queue (SQS) → CloudWatch Alarm
```

Rules:
- **Always attach a DLQ.** Set `maxReceiveCount` to 3-5 before moving to DLQ.
- **Visibility timeout** should be 6x your function/task max execution time. Lambda default of 30s is usually wrong.
- **Lambda concurrency**: Set a reserved concurrency to protect downstream services from thundering herd. Start at 10 and raise as you understand your throughput.
- **ECS task-based consumers**: Better than Lambda when messages take > 15 minutes or need > 10GB memory.
- **FIFO vs Standard**: Standard is almost always right. FIFO is only needed when strict ordering is a business requirement — it has 3,000 msg/s throughput cap (vs. effectively unlimited for Standard).

**Pattern: EventBridge for internal events**
```
Service emits event → EventBridge bus → Rules (pattern match) → multiple targets
```
- Use custom event buses per domain, not the default bus.
- EventBridge schema registry + code bindings reduce event contract drift.
- For cross-account fan-out, EventBridge resource policies beat SNS for complex routing.

---

## Serverless API

**Pattern: API Gateway (HTTP API) + Lambda + DynamoDB**

```
Client → API Gateway HTTP API → Lambda (ARM/Graviton) → DynamoDB
```

- **HTTP API over REST API**: Unless you need REST API-specific features (custom authorizers with response caching, request/response transformation, API keys). HTTP API is ~70% cheaper.
- **Lambda response streaming**: For large payloads, use streaming to reduce perceived latency and avoid 6MB response limit.
- **Cold starts**: Use provisioned concurrency only for latency-sensitive paths, not globally. Or use SnapStart for Java.
- **Authorization**: Prefer JWT authorizers (HTTP API) or Lambda authorizers over API key auth. For internal service-to-service, use IAM auth with SigV4.

**Pitfalls:**
- API Gateway has a 29-second integration timeout. If your Lambda can take longer, you need a different pattern (async invocation + polling, or WebSocket API).
- DynamoDB conditional writes are your "transactions" for simple cases. Use transactions (`TransactWriteItems`) sparingly — they cost 2x read/write capacity.

---

## Containerized microservices (ECS)

**Standard ECS Fargate service setup:**

```hcl
# Key resource relationships:
ECS Cluster → ECS Service → Task Definition → Container(s)
                ↓               ↓
            ALB Target      IAM Task Role
            Group           (not execution role)
```

**Task role vs. execution role:**
- **Execution role**: What ECS needs to *start* the task (pull from ECR, write to CloudWatch Logs, fetch SSM/Secrets Manager values). Managed by your platform team.
- **Task role**: What your *application code* can do (call DynamoDB, publish to SQS, put to S3). You define this per service.

**Service discovery:**
- AWS Cloud Map for service-to-service within a cluster (DNS-based).
- ALB for external traffic or cross-service when you want L7 routing/health checks.
- App Mesh (Envoy) for advanced traffic management — high operational cost, only worth it at large scale or when you need circuit breaking/retries at the mesh level.

**Scaling:**
- ECS service auto-scaling with Application Auto Scaling.
- Scale on CPU and memory, but also consider custom CloudWatch metrics (queue depth, request latency).
- Target tracking scaling > step scaling for most use cases — simpler, self-tuning.
- Set `deregistration_delay` on the target group to something reasonable (30-60s) — the default of 300s slows deployments.

**Deployment strategies:**
- Rolling (default): zero downtime if `minimum_healthy_percent` = 100, but requires capacity headroom.
- Blue/Green via CodeDeploy: test before shifting traffic, instant rollback. Worth the setup for critical services.

---

## Data pipeline / streaming

**Batch (Make pipeline context):**
```
Source → S3 (raw) → Lambda/ECS transform → S3 (processed) → Athena/Redshift
```

**Streaming (Kafka/Kinesis):**
```
Producers → MSK (Kafka) / Kinesis Data Streams → Lambda/Flink/KCL consumer → storage
```

**MSK vs Kinesis:**
- **MSK**: Full Kafka API compatibility. Better when you're already on Kafka or need Kafka-ecosystem tooling (ksqlDB, Connect, Schema Registry). More operational overhead.
- **Kinesis**: Simpler, fully managed, tight AWS integration. Shard model is less flexible but easier to operate. Enhanced fan-out for multiple consumers.

**S3 as a data lake foundation:**
- Partitioning strategy matters enormously for Athena query cost/speed. Partition by date (year/month/day) at minimum, then by any high-cardinality filter field.
- S3 Intelligent-Tiering: Worth it for data > 128KB that has unknown access patterns. Automatic, no retrieval fees for frequent/infrequent tiers.
- Object lifecycle rules: Transition to Glacier after N days, expire after M days. Never let logs/raw data grow indefinitely.

---

## Multi-account strategy

**Account vending model (AWS Organizations):**
```
Management account (billing only)
├── Security OU
│   ├── Log Archive account
│   └── Security Tooling account
├── Infrastructure OU
│   └── Shared Services (networking, DNS, ECR)
├── Production OU
│   └── App accounts (one per major product area)
└── Non-Production OU
    └── Staging, Dev accounts
```

**Key principles:**
- Production account gets no human console access in steady state. Changes via CI/CD only.
- Shared VPC via AWS RAM (Resource Access Manager) or Transit Gateway — don't recreate VPCs per account.
- Centralized logging to Log Archive account — nothing in that account except S3 buckets that accept CloudWatch logs from all other accounts.
- SCPs (Service Control Policies) at OU level — deny root account usage, require MFA, restrict regions.

---

## Availability and resilience patterns

### Multi-AZ (standard requirement)
- All production workloads span at least 3 AZs.
- ECS tasks: `minimum_healthy_percent = 100`, `desired_count >= 3` (one per AZ).
- RDS: Multi-AZ enabled. Failover takes 60-120s — design clients with retry logic.
- ElastiCache: Multi-AZ with auto-failover. Cluster mode for Redis when you need horizontal scale.

### Circuit breaker
ECS has a native circuit breaker: if a service's deployment fails (tasks keep failing health checks), ECS rolls back automatically. Enable this — it's off by default.

### Graceful degradation
Design with feature flags or fallback paths so partial outages don't cascade. Example: if the recommendation service is down, show popular items instead of erroring.

### Throttling and backpressure
- SQS as a buffer in front of any downstream that can't absorb bursty traffic.
- Lambda reserved concurrency as a hard ceiling to protect downstream.
- API Gateway usage plans + throttling for public APIs.

---

## Caching strategies

### CloudFront (edge cache)
- Cache static assets aggressively (max-age=31536000 with content-hash in filename).
- Cache API responses for GET requests where appropriate — be precise about `Cache-Control` headers.
- Cache invalidation via invalidation paths (costs $0.005/path after first 1000/month) or use versioned paths.

### ElastiCache Redis (application cache)
- Cache-aside pattern: app checks cache → miss → fetch from DB → write to cache.
- Write-through for data that's frequently read and must be fresh.
- TTL everything. Stale cache entries are a source of subtle bugs.
- Use Redis keyspace notifications + Lambda for cache warming patterns.

### DynamoDB DAX
- Adds microsecond read latency for DynamoDB. Only worth it if DynamoDB latency is a measured bottleneck. Not free — DAX clusters cost money even idle.

### S3 + CloudFront
- For large objects (images, JS bundles, ML models), S3 origin + CloudFront is almost always cheaper and faster than serving from ECS/Lambda.

---

## IAM design patterns

### Least privilege by default
- Never `*` on actions unless you've exhausted more specific options.
- Use IAM Access Analyzer to validate policies and identify unused permissions.
- Prefer `aws:SourceAccount` and `aws:SourceArn` conditions on cross-service policies to prevent confused deputy.

### Role patterns
- **Service roles**: One role per ECS task / Lambda function. No sharing roles across services — blast radius.
- **Cross-account roles**: Use `sts:AssumeRole` with external ID for third-party cross-account access. Log all AssumeRole calls via CloudTrail.
- **Break-glass role**: Emergency high-privilege role with CloudTrail alarm on any usage. Require MFA.

### Common IAM mistakes
- Attaching policies to users directly (use groups or roles).
- Using long-lived access keys (rotate; prefer IRSA/task roles for code running on AWS).
- Overly broad `s3:*` on a bucket when you only need `s3:GetObject`.
- Not setting permission boundaries on roles that developers can create.

---

## Networking patterns

### VPC CIDR planning
- Allocate large CIDRs (/16) even if you don't need them — CIDR expansion is painful.
- Leave room in your IP space for VPC peering — overlapping CIDRs block peering.
- /24 per AZ per tier is a reasonable default (256 IPs, ~250 usable after AWS reserve).

### Private connectivity
- **VPC Endpoints (Interface)**: Keep traffic to AWS services off the public internet and off the NAT Gateway (saves NAT Gateway data processing fees).
  - High-value targets: S3, DynamoDB, ECR (API + DKR), SSM, Secrets Manager, SQS, SNS, CloudWatch Logs
- **PrivateLink**: Expose your service to other accounts/VPCs without VPC peering. Only traffic you explicitly allow.
- **VPC Peering vs Transit Gateway**: Peering for 2-3 VPCs; TGW for anything more. TGW costs ~$0.05/attachment/hr + data transfer.

### DNS
- Route 53 private hosted zones attached to VPCs for internal service discovery.
- Enable `enableDnsSupport` and `enableDnsHostnames` on every VPC (required for private hosted zones and VPC endpoints).
- Split-horizon DNS: same domain resolves differently inside and outside the VPC.
