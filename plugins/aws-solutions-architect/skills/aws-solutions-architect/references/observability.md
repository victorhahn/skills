# AWS Observability

## Table of Contents
1. [Instrumentation strategy](#instrumentation-strategy)
2. [CloudWatch](#cloudwatch)
3. [Distributed tracing](#distributed-tracing)
4. [Log strategy](#log-strategy)
5. [Alerting](#alerting)
6. [Anti-patterns](#anti-patterns)

---

## Instrumentation strategy

The team uses **OpenTelemetry (OTEL) via AWS Distro for OpenTelemetry (ADOT)** as the instrumentation layer, with Datadog as the backend. This is the right call for new services — it avoids vendor lock-in on instrumentation and lets you switch backends without re-instrumenting.

**ADOT vs. native X-Ray SDK:**
- ADOT: OTEL-standard instrumentation. Emits to X-Ray, Datadog, Jaeger, or any OTEL-compatible backend. Prefer for new services.
- X-Ray SDK: AWS-native, tighter ECS/Lambda integration, but locks you to X-Ray as the backend. Only use if you have a strong reason to prefer X-Ray console over Datadog.

**The three pillars:**
- **Metrics**: operational health (request rate, error rate, latency p50/p95/p99, saturation)
- **Logs**: context for individual events, errors, and debugging
- **Traces**: distributed request flow across services — where latency lives, which service is the bottleneck

All three are needed; logs alone are insufficient for a distributed system.

---

## CloudWatch

### Container Insights
Enable Container Insights on ECS clusters to get task-level CPU, memory, network, and disk metrics without custom instrumentation:

```hcl
resource "aws_ecs_cluster" "main" {
  name = local.name_prefix

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}
```

Gives you per-task metrics via `ECS/ContainerInsights` namespace — essential for rightsizing and spotting memory leaks.

### CloudWatch Logs Insights
Ad-hoc querying over CloudWatch log groups. Useful query patterns:

```
# Count errors by type
fields @timestamp, @message
| filter @message like /ERROR/
| stats count() by bin(5m)

# Find slow requests
fields @timestamp, requestId, duration
| filter duration > 1000
| sort duration desc
| limit 20

# Trace a specific request ID across log groups
fields @timestamp, @message
| filter @message like "abc-123-request-id"
| sort @timestamp
```

Cross-log-group queries (querying multiple log groups at once) are available but cost more. Use for correlating ECS task logs with ALB access logs during incident investigation.

### CloudWatch Metrics: what to emit
For every service, emit at minimum:
- **Request count** (or invocation count for Lambda)
- **Error count / error rate** — broken out by error type if possible
- **Latency** (p50, p95, p99) — p99 surfaces tail latency issues that p50 hides
- **Queue depth** (for SQS consumers) — leading indicator of consumer lag
- **Business metrics** — events processed, orders created, etc. These are the metrics that matter when something breaks and you need to answer "what's the customer impact?"

Custom metrics via `aws-embedded-metrics` library (EMF format) are the most efficient way to emit custom metrics from Lambda/ECS — they embed metric data in CloudWatch Logs and get extracted automatically, avoiding PutMetricData API calls.

### Metric Math and anomaly detection
CloudWatch Metric Math lets you compute derived metrics (error rate = errors / requests) without emitting them separately. Anomaly detection alarms use ML to set dynamic thresholds based on historical patterns — more effective than static thresholds for metrics with daily/weekly seasonality (e.g., traffic that's always higher during business hours).

---

## Distributed tracing

### X-Ray / ADOT trace propagation
For traces to be useful, every service in the call chain must propagate the trace context (`X-Amzn-Trace-Id` header or W3C `traceparent`). If one service doesn't forward it, the trace breaks into disconnected fragments.

For ECS services using ADOT:
1. The ADOT collector runs as a sidecar container in the task definition
2. Your application sends OTEL spans to `localhost:4317` (gRPC) or `localhost:4318` (HTTP)
3. The collector exports to X-Ray, Datadog, or both

```json
// Container definition sidecar
{
  "name": "aws-otel-collector",
  "image": "public.ecr.aws/aws-observability/aws-otel-collector:latest",
  "essential": false,
  "command": ["--config=/etc/ecs/ecs-default-config.yaml"],
  "logConfiguration": {
    "logDriver": "awslogs",
    "options": {
      "awslogs-group": "/ecs/aws-otel-collector",
      "awslogs-region": "us-east-1",
      "awslogs-stream-prefix": "ecs"
    }
  }
}
```

### Sampling
X-Ray samples 5% of requests by default. For high-traffic services this is usually fine — you'll see enough traces. For low-traffic services or debugging specific issues, increase sampling via X-Ray sampling rules (not by changing code). Never sample 100% in production — the overhead and cost become significant.

### Trace IDs in logs
Correlate traces with logs by emitting the trace ID in your log output. When you find a slow trace in X-Ray, you can immediately jump to the logs for that specific request:

```typescript
// Include trace ID in all log lines
const traceId = process.env._X_AMZN_TRACE_ID;
logger.info('Processing request', { traceId, requestId, userId });
```

---

## Log strategy

### Structured logging
Emit JSON logs. Unstructured log lines are frustrating to query and parse in CloudWatch Logs Insights and Datadog. Every log event should be a JSON object with consistent fields:

```json
{
  "timestamp": "2025-01-01T00:00:00.000Z",
  "level": "INFO",
  "service": "my-service",
  "environment": "prod",
  "traceId": "Root=1-...",
  "requestId": "abc-123",
  "message": "Order processed",
  "orderId": "ord-456",
  "durationMs": 142
}
```

### Log levels — discipline matters
- `DEBUG`: verbose detail for local development. Never emit in production by default (cost + noise).
- `INFO`: normal operational events (request received, job completed, external call made)
- `WARN`: unexpected but handled conditions (retry triggered, fallback used, unusual input)
- `ERROR`: something failed and requires attention
- `FATAL`: service is unable to continue

Make log level configurable via environment variable (`LOG_LEVEL`) without redeployment. When debugging a production issue, bump to DEBUG on one instance, investigate, then revert.

### Log retention
Set explicitly on every log group — default is never expire. 30 days covers most debugging needs; 90 days for compliance-adjacent logs; 1 year for audit logs.

```hcl
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${local.name_prefix}"
  retention_in_days = 30
}
```

Log groups created automatically by Lambda, API Gateway, etc. won't have retention set unless you create the `aws_cloudwatch_log_group` resource explicitly in Terraform with `retention_in_days`.

### What to log (and what not to)
**Always log:**
- Request/response at service boundaries (with latency)
- External API calls and their outcomes
- Errors with full stack trace and request context
- State transitions for long-running jobs

**Never log:**
- PII (names, emails, SSNs, payment info) — even accidentally logging PII can be a compliance incident
- Credentials, tokens, passwords
- Full request/response bodies for endpoints that might carry sensitive data

---

## Alerting

### Alert on symptoms, not causes
Alert on customer-impacting conditions: high error rate, elevated p99 latency, queue depth growing unbounded. Don't alert on every infrastructure metric — CPU at 70% doesn't matter if response times are fine.

**The four golden signals** (from Google SRE):
1. **Latency** — how long requests take (distinguish successful vs. error latency)
2. **Traffic** — how much demand the system is under
3. **Errors** — rate of failed requests
4. **Saturation** — how "full" the service is (CPU, memory, queue depth, connection pool)

### Alarm configuration in Terraform
```hcl
resource "aws_cloudwatch_metric_alarm" "error_rate" {
  alarm_name          = "${local.name_prefix}-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  threshold           = 5  # > 5% error rate

  metric_query {
    id          = "error_rate"
    expression  = "errors / requests * 100"
    label       = "Error Rate %"
    return_data = true
  }

  metric_query {
    id = "errors"
    metric {
      metric_name = "HTTPCode_Target_5XX_Count"
      namespace   = "AWS/ApplicationELB"
      period      = 60
      stat        = "Sum"
      dimensions  = { LoadBalancer = aws_lb.main.arn_suffix }
    }
  }

  metric_query {
    id = "requests"
    metric {
      metric_name = "RequestCount"
      namespace   = "AWS/ApplicationELB"
      period      = 60
      stat        = "Sum"
      dimensions  = { LoadBalancer = aws_lb.main.arn_suffix }
    }
  }

  alarm_actions = [var.sns_alert_topic_arn]
  ok_actions    = [var.sns_alert_topic_arn]
}
```

### DLQ alarms are mandatory
Any DLQ with messages > 0 means something failed and was not retried. This should always page:

```hcl
resource "aws_cloudwatch_metric_alarm" "dlq_depth" {
  alarm_name          = "${local.name_prefix}-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Maximum"
  threshold           = 0
  dimensions          = { QueueName = aws_sqs_queue.dlq.name }
  alarm_actions       = [var.sns_alert_topic_arn]
}
```

### CloudWatch Anomaly Detection
Use anomaly detection alarms for metrics with seasonal patterns. More sensitive than static thresholds — catches real problems without false-positives during expected traffic spikes:

```hcl
resource "aws_cloudwatch_metric_alarm" "latency_anomaly" {
  alarm_name          = "${local.name_prefix}-latency-anomaly"
  comparison_operator = "GreaterThanUpperThreshold"
  evaluation_periods  = 3
  threshold_metric_id = "e1"

  metric_query {
    id          = "e1"
    expression  = "ANOMALY_DETECTION_BAND(m1, 2)"
    return_data = true
  }

  metric_query {
    id = "m1"
    metric {
      metric_name = "TargetResponseTime"
      namespace   = "AWS/ApplicationELB"
      period      = 60
      stat        = "p99"
      dimensions  = { LoadBalancer = aws_lb.main.arn_suffix }
    }
  }

  alarm_actions = [var.sns_alert_topic_arn]
}
```

---

## Anti-patterns

### ❌ Logging without structure
Unstructured logs like `"Processing order 12345 for user johndoe"` are nearly impossible to query systematically. Emit JSON from the start — retrofitting structured logging across a mature service is painful.

### ❌ Alerting on every metric
More alarms ≠ better observability. Alert fatigue causes engineers to ignore alarms, including real ones. Start with the four golden signals per service. Add specific alarms as you learn your system's failure modes.

### ❌ No retention set on log groups
The default is "never expire." High-volume services can accumulate surprising CloudWatch Logs costs silently over months. Always set `retention_in_days` in Terraform.

### ❌ Using CloudWatch as your only observability tool
CloudWatch Logs Insights is slow and expensive for large queries. For real-time debugging and correlated traces+logs+metrics, Datadog (which the team already uses) provides a better workflow. CloudWatch alarms are still useful as the source of paging alerts since they integrate natively with AWS resources, but investigation happens in Datadog.

### ❌ Trace context not propagated
If you add tracing to Service A but Service A calls Service B which doesn't propagate the trace header, every trace terminates at the A→B boundary. Traces are only useful if the full call graph is instrumented. Instrument all services before relying on traces for debugging cross-service latency.

### ❌ Sampling too aggressively (or not at all)
100% sampling in production = real performance overhead and cost. 0.1% sampling = traces are nearly useless for debugging specific requests. 5% (X-Ray default) is a reasonable starting point; tune up for critical paths, down for noisy high-volume paths.
