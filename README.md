# Google SRE — Error Budget Demo

Companion code for **Day 83/91 | The Incident: Google**

This is a local, illustrative simulation of error-budget-gated deploys,
the core idea behind Google's SRE practice: turn "can we ship this?" from
an opinion into a number.

## The idea

Both modes run the same sequence: 1,000 baseline successful requests,
then three deploys (safe, risky, risky). The only difference is whether
the deploy gate checks remaining error budget before letting a risky
change through.

| Naive gate                                    | Error-budget gate                                 |
|---------------------------------------------------|---------------------------------------------------------|
| Every deploy ships, regardless of recent reliability | Risky deploys only ship if enough budget remains           |
| No way to stop a reliability nosedive automatically   | Budget exhaustion blocks further risk automatically          |
| Ends at 1.57% failure rate — over the 1% SLO            | Ends at 0.79% failure rate — stays under the SLO             |

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install flask requests
```

## Run it

**Terminal 1 — start the app:**
```bash
python3 app.py
```

**Terminal 2 — run the simulated deploy sequence:**
```bash
python3 load_test.py
```

You'll see the same three deploys run through both gates, and the very
different outcome once the error budget is actually enforced.

## Try it live

```bash
curl -X POST http://localhost:8000/deploy/gated \
  -H "Content-Type: application/json" \
  -d '{"risk_level": "risky"}'

curl http://localhost:8000/status
```
