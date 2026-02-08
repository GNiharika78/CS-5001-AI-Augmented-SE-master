# Payments Runbook

## Symptom: High p95 latency
Diagnosis:
1. Check dashboard: payments_service_latency_p95
2. Check downstream dependency: redis latency
3. Check error rate: http_5xx_rate

Mitigation:
- Scale replicas by 2
- Enable cache warmup job

Rollback procedure:
- Revert last deploy using: deployctl rollback payments --to <previous>
