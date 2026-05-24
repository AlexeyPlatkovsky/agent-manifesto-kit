---
name: review-code-performance
description: Reviews a code diff for performance issues — algorithmic complexity, N+1 queries, allocation hotspots, blocking I/O, and caching mistakes. Use when the user asks for a performance review, latency review, or scalability check of a change.
---

# Reviewing Code for Performance

## When to use

The user wants a performance-focused review of a diff. For correctness, use `review-code-correctness`. For security, use `review-code-security`. Not for ad-hoc profiling or benchmarking.

## Inputs required

- The diff or PR
- Workload context: request rate, data volumes, latency target, environment (single host / cluster / serverless)
- Whether the change is on a hot path

If workload is unstated, ask before drawing conclusions. "Slow" without context is meaningless.

## Procedure

1. Identify the hot paths the diff touches.
2. Estimate algorithmic complexity for new loops and recursion in terms of input size.
3. Walk the checklist below. Cite file:line for every finding.
4. Quantify impact when possible (rough Big-O or rows × queries), not just "could be slow".

## Performance checklist

**Algorithm and data structures**
- Nested loops over the same collection (O(n²) where O(n) is feasible)
- Linear search inside a loop (consider hash set)
- Sorting / copying in hot paths
- Recomputation of the same value per iteration

**Database**
- N+1 query patterns (loop that issues a query per item)
- Missing index for the filter / sort / join introduced
- `SELECT *` over wide tables on hot paths
- Transactions held across network / external calls
- Unbounded `LIMIT`-less queries on growing tables
- Pagination via `OFFSET` on large offsets (use keyset pagination)

**I/O and concurrency**
- Synchronous I/O on a request thread / event loop
- Sequential awaits where parallel `gather` / `allSettled` is correct
- Thread / connection pool exhaustion (long-held connections, no timeout)
- Blocking call inside an async function
- Hot loop without backpressure

**Memory and allocation**
- Loading entire collections into memory when streaming is feasible
- String concatenation in tight loops (use builder / join)
- Defensive copies that are not necessary
- Caches without size bound or TTL → leak

**Caching**
- Cache key omits a tenant / locale / version dimension
- TTL not set or far too long for the data's volatility
- Stampede: many callers fill the same key after expiry (no single-flight / lock)
- Cache invalidation tied to a write path that may not run

**Network and serialization**
- Chatty calls that could be batched
- JSON parse/stringify on every request for static data
- Large payloads not compressed where transport supports it
- Retries without exponential backoff and jitter

## Severity

- **Critical**: regression on a known hot path, scaling breaks at expected load
- **High**: N+1, unbounded query, blocking the event loop
- **Medium**: avoidable allocation, suboptimal cache use
- **Low**: micro-optimization with little measurable effect
- **Info**: observation only

## Output contract

```
| Severity | File:line | Issue | Estimated impact | Suggested fix |
```

End with a verdict and an explicit recommendation on whether a benchmark or load test is warranted before merge.

## Stopping conditions

Stop if workload context is unknown or if the diff requires profiling data the user has not provided.
