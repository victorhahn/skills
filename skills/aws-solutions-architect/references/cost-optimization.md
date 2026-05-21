# AWS Cost Optimization

## Table of Contents
1. [Where AWS spend actually comes from](#where-aws-spend-actually-comes-from)
2. [Quick wins](#quick-wins)
3. [Compute optimization](#compute-optimization)
4. [Storage optimization](#storage-optimization)
5. [Data transfer costs](#data-transfer-costs)
6. [Commitment discounts](#commitment-discounts)
7. [Database optimization](#database-optimization)
8. [Cost visibility and governance](#cost-visibility-and-governance)

---

## Where AWS spend actually comes from

Most teams are surprised to find their bill dominated by a few categories. In rough order of frequency for backend services teams:

1. **EC2 / Fargate compute** — oversized instances, over-provisioned task CPU/memory
2. **Data transfer** — cross-AZ, NAT Gateway egress, inter-region
3. **RDS** — over-provisioned instance sizes, backups, data transfer
4. **NAT Gateway** — data processing + hourly charges, especially for high-egress services
5. **CloudWatch Logs** — log ingestion for high-volume services, long retention
6. **ElastiCache** — idle clusters, over-provisioned node types
7. **S3** — less often the primary driver, but storage class choices matter at scale

**Before optimizing:** pull the AWS Cost Explorer "Group by service + linked account" view for the last 3 months. Identify the top 3 cost drivers. Optimize those first — everything else is noise.

---

## Quick wins

These can usually be done in < 1 sprint with low risk:

### 1. Right-size ECS tasks
ECS task CPU/memory is often over-provisioned because it was set once and never revisited. Pull CloudWatch Container Insights metrics:
- Look at CPU utilization per service over the last 30 days (p95)
- If p95 CPU < 30% of provisioned, halve the allocation and monitor
- Memory is trickier — set to ~1.5x the p99 observed usage (not peak) to allow headroom

### 2. Switch Lambda to ARM (Graviton)
One-line change. Graviton is cheaper with equal or better performance for most workloads (check current discount at https://aws.amazon.com/lambda/pricing/):
```hcl
architectures = ["arm64"]
```
Test first in non-prod. Not compatible with x86-only native dependencies (rare but possible).

### 3. Enable S3 Intelligent-Tiering
For any S3 bucket with objects > 128KB and uncertain access patterns:
```hcl
resource "aws_s3_bucket_intelligent_tiering_configuration" "example" {
  bucket = aws_s3_bucket.example.id
  name   = "default"
  
  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = 180
  }
  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = 90
  }
}
```
No retrieval fees for frequent/infrequent tiers. Deep Archive has retrieval fees — only enable for data you're archiving.

### 4. Set S3 lifecycle rules on log buckets
```hcl
resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "transition-and-expire"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER_IR"
    }

    expiration {
      days = 365
    }
  }
}
```

### 5. Reduce CloudWatch Logs retention
Default retention is "never expire." Set per log group to what your compliance/debugging needs actually require:
```hcl
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/my-service"
  retention_in_days = 30  # or 7, 14, 60 — depends on compliance requirements
}
```
CloudWatch Logs ingestion is priced per GB — check https://aws.amazon.com/cloudwatch/pricing/. Long retention on high-volume services adds up fast regardless of current rates.

### 6. Delete unused resources
- Unattached EBS volumes
- Unused EIPs (Elastic IPs) — charged when *not* attached
- Idle NAT Gateways
- Stopped EC2 instances (still paying for EBS)
- Old/unused ECR images (use lifecycle policies)

---

## Compute optimization

### EC2 Savings Plans vs Reserved Instances
- **Compute Savings Plans**: Most flexible — apply to EC2, Lambda, and Fargate. Discount based on $/hr spend commitment, not specific instance type. Start here.
- **EC2 Instance Savings Plans**: Higher discount than Compute SP but locked to instance family + region.
- **Reserved Instances**: Old model. Prefer Savings Plans unless you have specific steady-state workloads where the extra savings of convertible RIs matter.

**Commitment strategy:**
- 1-year, no upfront = meaningful discount with no cash outlay. Start here.
- 3-year, all upfront = highest discount. Only commit when you have confidence in steady-state usage.
- Never commit more than you're confident will be used. Unused commitments are a sunk cost.
- For current discount rates, check https://aws.amazon.com/savingsplans/compute-pricing/ — rates shift as on-demand prices change.

**Coverage target:** Aim for 70-80% Savings Plan coverage on stable compute. Keep 20-30% on-demand for variability and unpredictable growth.

### Fargate Spot
For fault-tolerant, interruptible workloads (batch jobs, background processing), Fargate Spot can save 70%:
```hcl
capacity_provider_strategy {
  capacity_provider = "FARGATE_SPOT"
  weight            = 4
  base              = 0
}
capacity_provider_strategy {
  capacity_provider = "FARGATE"
  weight            = 1
  base              = 1
}
```
This runs 80% Spot, 20% on-demand. The `base = 1` on FARGATE ensures at least one on-demand task is always running. Don't use Spot for latency-sensitive user-facing services.

### Lambda cost
Lambda is already cheap for most workloads. The main optimization levers:
- ARM architecture — Graviton is cheaper per GB-second; check current rates at https://aws.amazon.com/lambda/pricing/
- Right-size memory — Lambda allocates CPU proportionally to memory. Under-provisioned = slow and therefore more expensive per request.
- SnapStart for Java (reduces cold starts, can reduce concurrent execution count)
- Watch out for: Functions kept warm unnecessarily via EventBridge pings — this was a cold start hack that's mostly unnecessary now.

---

## Storage optimization

### S3 storage class tiers

For current pricing, fetch https://aws.amazon.com/s3/pricing/. The tiers from most to least expensive storage cost (with trade-offs):

| Tier | Use case | Retrieval fee? |
|------|----------|----------------|
| Standard | Frequently accessed | None |
| Standard-IA | Infrequent, accessed < ~1x/mo | Yes — per GB |
| Glacier Instant Retrieval | Archive, millisecond access | Yes — per GB |
| Glacier Flexible Retrieval | Archive, minutes-hours | Yes — per GB |
| Deep Archive | Long-term archive, hours | Yes — per GB |

**Don't use Standard-IA for small objects.** There's a 128KB minimum billable size — small objects in Standard-IA cost *more* than in Standard.

**Deep Archive retrieval is slow and costs extra** — only use it for compliance/backup data you will rarely or never access.

### EBS optimization
- **gp3 over gp2**: gp3 is 20% cheaper and you can tune IOPS/throughput independently. Convert existing gp2 volumes:
  ```bash
  aws ec2 modify-volume --volume-id vol-xxx --volume-type gp3
  ```
- **Snapshots**: Old, forgotten snapshots accumulate quietly. Audit and delete.
- **EC2 instance store**: Free, but ephemeral. Use for temp files, caches, scratch space — not for anything that needs to survive instance termination.

---

## Data transfer costs

Data transfer is frequently the surprise in AWS bills. For current rates, fetch https://aws.amazon.com/ec2/pricing/on-demand/#Data_Transfer and https://aws.amazon.com/vpc/pricing/.

**What's free vs. what costs (stable structure, rates vary):**
- Inbound to AWS: always free
- Cross-AZ within a region: costs per GB each direction — adds up at scale
- Cross-region: costs per GB — significant for multi-region architectures
- Outbound to internet: costs per GB (tiered rates), check current pricing
- VPC Endpoint (S3/DDB): no data processing fee, unlike NAT Gateway
- NAT Gateway: hourly charge per AZ + data processing fee per GB — often a top cost driver for egress-heavy services

**High-impact changes:**
1. **VPC endpoints for S3 and DynamoDB** — eliminates NAT Gateway data processing costs for S3/DDB traffic entirely
2. **Co-locate services in the same AZ** — cross-AZ traffic charges on hot paths add up; consider AZ affinity for latency-sensitive internal calls
3. **CloudFront for external traffic** — CloudFront's regional data transfer rates are lower than direct EC2 internet egress

**NAT Gateway cost pattern:**
High-egress services (e.g., services constantly pulling from S3 or calling AWS APIs) can generate large NAT Gateway bills because every byte passes through it. VPC endpoints for the target services eliminate that cost for that traffic. Do the math with current rates from https://aws.amazon.com/vpc/pricing/ for your actual egress volume.

---

## Commitment discounts

### Compute Savings Plans (recommended starting point)
1. Go to Cost Explorer → Savings Plans → Recommendations
2. AWS recommends coverage amount based on your 7/30/60-day average usage
3. Start with 1-year, no-upfront — break-even in first month vs. on-demand
4. Monitor coverage weekly; add more in tranches

### RDS Reserved Instances
RDS doesn't participate in Compute Savings Plans. You need RDS-specific RIs.
- Multi-AZ RIs are priced separately from Single-AZ
- Reserved capacity is applied per instance class per region — check your fleet first

### ElastiCache Reserved Nodes
Similar to RDS — separate reservation model. Worth buying if you have stable ElastiCache usage.

---

## Database optimization

### DynamoDB cost drivers
- **Read/Write Capacity Units**: On-demand scales freely but costs ~7x more per request at high steady-state load vs. provisioned. Switch to provisioned + auto-scaling when you have predictable load.
- **DAX**: Only add if you've measured DynamoDB latency as a bottleneck and confirmed DAX will help. DAX clusters aren't cheap.
- **Global Tables**: Replicated to N regions — pay for storage and write replication in each region. Only use when you actually need multi-region.
- **On-demand backup** vs. **PITR**: PITR is $0.20/GB/month for backup storage. Evaluate retention window carefully.

### RDS/Aurora cost optimization
- **Aurora Serverless v2**: Good for variable workloads. Min ACU of 0.5 still costs; Aurora doesn't truly scale to zero (Aurora Serverless v1 does but has cold-start issues). Min ACU = $0.06/hr even idle.
- **Instance sizing**: Use Performance Insights to identify if you're CPU- or memory-bound before sizing. For read-heavy workloads, read replicas often make more sense than upsizing the primary.
- **Storage auto-scaling**: Enable it, but also set a max — uncapped auto-scaling storage can surprise you.
- **Multi-AZ**: Required for production. Don't use single-AZ to save money in prod.

### ElastiCache
- Audit: Is this cache actually improving performance? Use CloudWatch `CacheHits` vs `CacheMisses`. A miss rate > 20% means your TTLs or key design may need tuning.
- Node type sizing: use current-gen Graviton nodes — check https://aws.amazon.com/elasticache/pricing/ for the latest available families, which are cheaper and better than prior generations.

---

## Cost visibility and governance

### Tagging strategy
Without consistent tags, Cost Explorer is nearly useless below the account level. Required tags:
- `Environment` (prod, staging, dev)
- `Service` (the application/microservice name)
- `Team` or `Owner`
- `CostCenter` (for chargeback if needed)

Enforce via AWS Config rules and SCP-enforced tag policies. Add to your Terraform standards.

### Cost Explorer queries to run monthly
1. **Top services by cost** — identify the big buckets
2. **Cost by tag:Service** — which applications are most expensive?
3. **Untagged resources** — any cost that isn't attributed is a blind spot
4. **Data transfer breakdown** — "Usage type group: Data Transfer" reveals cross-AZ and NAT costs

### AWS Cost Anomaly Detection
Enable this — it's free and will alert you when spending in any service suddenly spikes. Set it up for each major service tag. Many teams have been surprised by a runaway Lambda or DynamoDB scan that ran for days before anyone noticed.

### Budgets and alerts
```hcl
resource "aws_budgets_budget" "monthly" {
  name         = "monthly-total-budget"
  budget_type  = "COST"
  limit_amount = "5000"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["team@example.com"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = ["team@example.com"]
  }
}
```
