# API Examples

Backend base URL:

```text
http://localhost:8000
```

## Health

```bash
curl http://localhost:8000/health
```

## List HCPs

```bash
curl http://localhost:8000/api/hcps
```

## Structured Log Interaction

```bash
curl -X POST http://localhost:8000/api/interactions ^
  -H "Content-Type: application/json" ^
  -d "{\"hcp_id\":1,\"interaction_type\":\"Detailing Call\",\"channel\":\"In-person\",\"product_discussed\":\"CardioGuard\",\"objective\":\"Discuss patient profile fit\",\"notes\":\"Dr. Mehra was interested in safety evidence and asked for a follow-up next week.\",\"commitment\":\"Review evidence\",\"next_step\":\"Send approved clinical deck\",\"follow_up_date\":\"\"}"
```

## Conversational Log Interaction

```bash
curl -X POST http://localhost:8000/api/agent/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"hcp_id\":1,\"message\":\"Log that Dr. Mehra discussed CardioGuard, was positive about the evidence, and requested a follow-up next week.\"}"
```

## Demo A Specific Tool

```bash
curl -X POST http://localhost:8000/api/agent/demo ^
  -H "Content-Type: application/json" ^
  -d "{\"tool_name\":\"suggest_next_best_action\",\"payload\":{\"hcp_id\":1}}"
```

## Agent Trace

```bash
curl http://localhost:8000/api/agent/runs
```
