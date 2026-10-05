"""
Simulates 1,000 baseline successful requests (establishing the budget
window), followed by the same sequence of deploys: one safe, two risky.

Runs this through BOTH the naive gate and the error-budget gate, so we
can compare what actually ships.
"""

import requests

BASE_URL = "http://localhost:8000"

BASELINE_REQUESTS = 1000
DEPLOY_SEQUENCE = ["safe", "risky", "risky"]


def run_mode(mode: str):
    print(f"\n--- {mode.upper()} gate ---")

    print(f"Sending {BASELINE_REQUESTS} baseline successful requests...")
    for _ in range(BASELINE_REQUESTS):
        requests.post(f"{BASE_URL}/traffic/{mode}")

    for i, risk_level in enumerate(DEPLOY_SEQUENCE, start=1):
        r = requests.post(f"{BASE_URL}/deploy/{mode}", json={"risk_level": risk_level})
        result = r.json()
        print(f"  Deploy {i} ({risk_level}): {result['status']}"
              + (f" -- {result['reason']}" if "reason" in result else ""))


if __name__ == "__main__":
    print("Resetting state...")
    requests.post(f"{BASE_URL}/reset")
    run_mode("naive")
    naive_status = requests.get(f"{BASE_URL}/status").json()["naive"]

    print("\nResetting state...")
    requests.post(f"{BASE_URL}/reset")
    run_mode("gated")
    gated_status = requests.get(f"{BASE_URL}/status").json()["gated"]

    print("\n--- Summary ---")
    print(f"NAIVE gate:  {naive_status['total_failures']} failures, "
          f"{naive_status['failure_rate_pct']}% failure rate (SLO target: 1%)")
    print(f"GATED gate:  {gated_status['total_failures']} failures, "
          f"{gated_status['failure_rate_pct']}% failure rate, "
          f"{gated_status['deploys_blocked']} risky deploy(s) blocked")
