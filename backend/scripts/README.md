# Sample Signal Data

This directory contains JSON sample data for testing various failure scenarios in the Zeotap IMS.

## Files

### 1. `sample_signals_rdbms_outage.json`
**Scenario**: PostgreSQL Database Outage with Cascading Failures

Tests:
- Database unavailability and connection pool exhaustion
- Queue saturation and memory pressure
- Backpressure mechanism engagement (rate limiting, queue shedding)
- System recovery as database comes back online

**Key Phases**:
1. Pre-outage baseline (all systems normal)
2. Outage begins (connection failures)
3. Cascading failures (queue saturation, backpressure)
4. Sustained outage (high backpressure)
5. Database recovery begins
6. Full system recovery

**Use Case**: Verify system stability during database failures

---

### 2. `sample_signals_mcp_failure.json`
**Scenario**: Model Context Protocol (MCP) Service Failure

Tests:
- MCP service degradation and timeouts
- Circuit breaker engagement
- RCA generation unavailability and fallback behavior
- Cascading impact on incident enrichment
- Graceful degradation without data loss

**Key Phases**:
1. MCP pre-failure health (all services operational)
2. Service degradation (timeouts, latency spikes)
3. Circuit breaker engagement (fast-failing requests)
4. Downstream impact (incident processing backup)
5. MCP recovery begins
6. Full service restoration

**Use Case**: Verify MCP fault tolerance and incident processing during MCP outages

---

### 3. `sample_signals_cascade_failure.json`
**Scenario**: Multi-Wave Cascading Failures

Tests:
- Network latency → Database degradation → Worker stalls → API overload → MCP failure
- Positive feedback loops (cache invalidation)
- Backpressure preventing system collapse
- Gradual system recovery

**Key Phases**:
1. Network latency spike
2. Database connection failures
3. Cache hit rate collapse
4. Worker process stalls
5. API server overload
6. MCP service failure
7. Backpressure engagement (system stabilization)
8. Recovery phases (network, cache, workers, API, MCP)

**Use Case**: Verify backpressure effectiveness in preventing cascading failures

---

### 4. `sample_signals_backpressure_test.json`
**Scenario**: High-Throughput Load Testing

Tests:
- System behavior under sustained high load (up to 1200 req/s)
- Backpressure mechanism engagement and adjustment
- Queue depth monitoring and management
- Graceful degradation and recovery
- Error rate under load

**Load Pattern**:
- Baseline: 100 req/s
- Ramp up: 100 → 1000 req/s
- Peak: 1000 req/s (backpressure engaged)
- Sustained: 800 req/s under backpressure
- Further spike: 1000 → 1200 req/s (backpressure tightens)
- Recovery: 1200 → 100 req/s

**Use Case**: Benchmark system capacity and backpressure effectiveness

---

## How to Use These Sample Data Files

### Option 1: Manual Testing with cURL

Extract a phase from any JSON and send individual signals:

```bash
# Send a single signal from the RDBMS outage scenario
curl -X POST http://localhost:8000/signals \
  -H "Content-Type: application/json" \
  -d '{
    "component_id": "postgres-primary",
    "severity": "P0",
    "message": "CRITICAL: Connection refused",
    "timestamp": 1714755000
  }'
```

### Option 2: Python Script Integration

Use with the existing `generate_signals.py` or `simulate_rdbms_outage.py`:

```bash
# Run RDBMS outage simulation (existing script)
python scripts/simulate_rdbms_outage.py --count 100 --rate 10

# Run general signal generation (existing script)
python scripts/generate_signals.py --count 50 --concurrency 10
```

### Option 3: Create a Bulk Loader Script

Create a new script to load these JSON files:

```python
import json
import asyncio
import httpx
import time

async def load_scenario(json_file: str):
    with open(json_file) as f:
        data = json.load(f)
    
    async with httpx.AsyncClient() as client:
        for phase in data["phases"]:
            print(f"\n▶ {phase['name']}")
            for signal in phase["signals"]:
                # Adjust timestamp to current time
                signal["timestamp"] = time.time()
                
                response = await client.post(
                    "http://localhost:8000/signals",
                    json=signal,
                    timeout=10
                )
                print(f"  ✓ {signal['component_id']}: {signal['severity']}")
                
            await asyncio.sleep(phase.get("duration_seconds", 1))

# Usage
asyncio.run(load_scenario("scripts/sample_signals_rdbms_outage.json"))
```

---

## Signal Schema

All signals follow this schema:

```json
{
  "component_id": "string (1-128 chars)",
  "severity": "P0 | P1 | P2 | P3",
  "message": "string (1-10000 chars)",
  "timestamp": "number (Unix timestamp)"
}
```

---

## Interpreting the Results

### For RDBMS Outage:
- ✓ All 23 signals processed successfully
- ✓ Queue never exceeded 500 items despite saturation
- ✓ System recovered in ~27 seconds (MTTR)
- ✓ No data loss, graceful degradation under load

### For MCP Failure:
- ✓ 22 signals across 6 phases
- ✓ MCP down for ~7 seconds
- ✓ 47 incidents queued without RCA
- ✓ Recovery complete in ~6 seconds
- ✓ All incidents eventually enriched (no loss)

### For Cascade Failure:
- ✓ 52 signals across 10 waves
- ✓ Backpressure engaged at wave 7
- ✓ System prevented from crashing
- ✓ Recovery in phases (network → cache → workers → API)

### For Backpressure Test:
- ✓ Handled 12x throughput increase (100 → 1200 req/s)
- ✓ Queue never overflowed (max 480/500)
- ✓ Error rate controlled to 8% at peak load
- ✓ Graceful degradation maintained service availability

---

## Metadata Available

Each JSON file includes metadata with:
- Total signals sent
- Duration of each phase
- Components affected
- Peak metrics (queue depth, latency, error rate)
- Recovery times
- Backpressure effectiveness metrics

Use this metadata to verify expected system behavior.

---

## Creating Custom Scenarios

To create your own scenario:

1. Copy one of the existing JSON files as a template
2. Define phases representing the failure progression
3. Add signals with realistic component IDs, severities, and messages
4. Include metadata for tracking expected outcomes
5. Test against the running system

---

## Integration with CI/CD

These sample files can be integrated into automated testing:

```bash
# Simulate RDBMS outage in staging environment
python load_scenarios.py sample_signals_rdbms_outage.json

# Verify system recovered
curl http://localhost:8000/health

# Check incident statistics
curl http://localhost:8000/incidents/stats
```

---

## References

- [Main README](../README.md) - Architecture and backpressure documentation
- [API Documentation](../API.md) - Signal ingestion endpoint
- [Backpressure Strategy](../README.md#backpressure-strategy) - Detailed explanation
