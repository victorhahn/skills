# Serverless & Event-Driven Architecture

## Table of Contents
1. [Lambda fundamentals and gotchas](#lambda-fundamentals-and-gotchas)
2. [Event-driven patterns](#event-driven-patterns)
3. [Step Functions](#step-functions)
4. [EventBridge patterns](#eventbridge-patterns)
5. [Anti-patterns](#anti-patterns)

---

## Lambda fundamentals and gotchas

### Execution model
- Each Lambda invocation gets an isolated execution environment. The handler runs fresh each time, but the environment (process, /tmp, global variables) may be reused across invocations within the same container ("warm start"). Don't assume clean state between invocations — initialize expensive resources outside the handler, but defensively.
- `/tmp` is 512MB by default (configurable up to 10GB). It persists within a warm container but is not shared between concurrent invocations. Use it for temp work, not coordination.
- Environment variables are set at deploy time. For secrets, use Secrets Manager or SSM via the execution role — not environment variables.

### Cold starts
Cold starts add latency when a new execution environment is initialized (new deployment, scale-out, idle expiry). Lambda keeps environments warm for roughly 5–15 minutes of inactivity.

Mitigation options:
- **SnapStart** (Java only): pre-initializes the JVM snapshot. Best option for Java Lambdas with slow init.
- **Provisioned concurrency**: keeps N environments pre-warmed. Costs extra even when not invoked — only use for latency-critical paths where cold starts are a measured user-facing problem.
- **ARM/Graviton**: smaller runtime initialization overhead in addition to cost benefits.
- Avoid heavy SDK initialization in the handler body — do it at module level so it's cached across warm invocations.

### Concurrency model
- **Reserved concurrency**: hard ceiling on concurrent executions for a function. Use to protect downstream systems from thundering herd. Also useful to guarantee capacity (reserved concurrency is subtracted from the regional pool and held for your function).
- **Burst limits**: Lambda can scale fast, but not infinitely instantaneous. Region-level burst limit is 3,000 initial concurrent executions + 500/min after that (varies by region). At high scale, this can be a real constraint.
- **Throttling**: when concurrency limit is hit, Lambda returns a 429. The event source mapping (SQS, Kinesis) retries; API Gateway returns a 429 to the client.

### Limits worth knowing
Check https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html for current limits. Notable ones:
- Maximum execution duration: 15 minutes
- Maximum deployment package size: 250MB unzipped (use Lambda Layers or S3 for large dependencies)
- Maximum response payload: 6MB (synchronous), 256KB (async destinations). For large responses, write to S3 and return the key.
- Maximum environment variable size: 4KB total
- Maximum `/tmp` storage: 10GB (default 512MB — configure explicitly if needed)

---

## Event-driven patterns

### SQS → Lambda (most common pattern)
Lambda polls SQS via an event source mapping. Key configuration:

```hcl
resource "aws_lambda_event_source_mapping" "sqs" {
  event_source_arn                   = aws_sqs_queue.main.arn
  function_name                      = aws_lambda_function.processor.arn
  batch_size                         = 10      # Messages per invocation
  maximum_batching_window_in_seconds = 5       # Wait up to 5s to fill the batch
  function_response_types            = ["ReportBatchItemFailures"]  # Partial batch success
}
```

**`ReportBatchItemFailures`**: If your Lambda processes 10 messages and 2 fail, without this, all 10 go back to the queue. With it, you return which message IDs failed and only those are retried. Always enable this for SQS.

**Visibility timeout**: Must be >= 6× your Lambda function timeout. If Lambda takes 30s, set visibility timeout to 180s+. If not, the message becomes visible again while still being processed — duplicate processing.

### Kinesis → Lambda
Different from SQS: Lambda reads from a shard, and *in-order processing within a shard* is guaranteed. A single failed record blocks the shard until it succeeds or expires.

```hcl
resource "aws_lambda_event_source_mapping" "kinesis" {
  event_source_arn              = aws_kinesis_stream.main.arn
  function_name                 = aws_lambda_function.processor.arn
  starting_position             = "LATEST"
  bisect_batch_on_function_error = true   # Split batch in half on failure to isolate bad records
  destination_config {
    on_failure {
      destination_arn = aws_sqs_queue.dlq.arn  # Failed records go here
    }
  }
  maximum_retry_attempts        = 3
}
```

**`bisect_batch_on_function_error`**: On failure, splits the batch in half and retries each half. Isolates poison pill records without manual intervention. Always enable.

### SNS → SQS fan-out
The correct pattern for sending one event to multiple consumers:

```
SNS Topic → SQS Queue A (Consumer A)
          → SQS Queue B (Consumer B)
          → SQS Queue C (Consumer C)
```

❌ Don't subscribe Lambda directly to SNS if you need retry semantics — SNS has limited retry and no DLQ built-in for Lambda subscriptions.  
✅ Subscribe SQS queues to SNS, then Lambda to each SQS. Each consumer gets its own retry/DLQ behavior independently.

---

## Step Functions

Use Step Functions when:
- You have multi-step workflows where you need to track state between steps
- Steps are long-running (> 15 minutes total, which Lambda can't do in one invocation)
- You need human approval steps, wait-for-callback patterns, or parallel branches
- You want built-in retry/catch logic with exponential backoff without writing it yourself

**Standard vs. Express:**
- **Standard**: Exactly-once execution, durable state, up to 1 year duration. For business-critical workflows. Priced per state transition.
- **Express**: At-least-once, up to 5 minutes, cheaper. For high-volume event processing where idempotency is handled in your code.

**Key patterns:**
- **Wait for callback** (`waitForTaskToken`): Lambda sends a token to an external system; the workflow pauses until that token is returned. Useful for async integrations (Slack approvals, human review, third-party webhooks).
- **Map state**: Fan-out processing — run the same state machine logic over each item in an array, in parallel or serially.
- **Express + SQS**: For high-throughput event processing where you want orchestration without SQS's 12-hour message retention limit.

---

## EventBridge patterns

EventBridge is the right choice over SNS when:
- You need content-based routing (filter on event body fields, not just topic)
- You have multiple AWS accounts sending/receiving events (event bus resource policies)
- You want schema registry and generated code bindings to enforce event contracts
- You're integrating with SaaS sources (Salesforce, Datadog, etc.)

**Custom event bus per domain:**
```hcl
resource "aws_cloudwatch_event_bus" "orders" {
  name = "orders-${var.environment}"
}

resource "aws_cloudwatch_event_rule" "order_placed" {
  event_bus_name = aws_cloudwatch_event_bus.orders.name
  name           = "order-placed"
  
  event_pattern = jsonencode({
    source      = ["com.myapp.orders"]
    detail-type = ["OrderPlaced"]
    detail = {
      status = ["CONFIRMED"]  # Content-based filter
    }
  })
}
```

**Schema registry**: Enable it on custom buses. EventBridge can infer schemas from events and generate typed code bindings. This is a lightweight contract mechanism between producers and consumers.

**Pipes**: EventBridge Pipes connect event sources (SQS, Kinesis, DynamoDB Streams) to targets with optional filtering and enrichment — without writing a Lambda just to route events.

---

## Anti-patterns

### ❌ Lambda as a general-purpose compute layer
Lambda's concurrency model, 15-minute limit, and stateless nature make it poorly suited for: long-running batch jobs, workloads requiring persistent connections (database connection pooling), or anything that needs > 10GB memory. Use ECS Fargate tasks for those.

### ❌ Synchronous Lambda chains
```
API Gateway → Lambda A → (synchronously invokes) Lambda B → Lambda C
```
This compounds latency, consumes concurrency from both functions simultaneously, and errors in Lambda B/C surface as errors in Lambda A with no independent retry. Replace with async invocation + SQS between steps, or use Step Functions if you need orchestration.

### ❌ Sharing Lambda execution roles across functions
One IAM role for all your Lambdas means every function has permissions it doesn't need. When something goes wrong (or gets compromised), the blast radius is your entire Lambda fleet. One role per function.

### ❌ Polling SQS in a loop inside Lambda
Lambda has native SQS integration via event source mappings — don't write a loop that polls SQS manually inside a Lambda invoked on a schedule. The managed integration handles polling, batching, visibility timeout, and partial batch failures automatically.

### ❌ EventBridge default event bus for application events
The default bus receives all AWS service events (EC2 state changes, CloudTrail events, etc.) and is noisy. Put your application events on a custom bus to keep routing rules clean and avoid accidentally matching AWS service events.

### ❌ Step Functions for simple async decoupling
If you just need "run this job when a message arrives," SQS + Lambda is simpler and cheaper. Step Functions adds value when you need orchestration — branching, parallel state, wait states, long-duration workflows. Don't use it just because it exists.
