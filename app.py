"""
Google SRE error budget demo (illustrative, local-only simulation).

Simulates an SLO of 99% success over a 1,000-request window, giving a
total error budget of 10 allowed failures. Risky deploys are modeled as
generating a fixed number of failures if they're allowed to go out.

Two deploy gates over equivalent traffic and deploy sequences:

  /deploy/naive  -> ALWAYS allows a deploy, regardless of current
                     reliability. Risky deploys ship no matter how much
                     budget has already been burned.

  /deploy/gated  -> checks the remaining error budget first. A risky
                     deploy is only allowed if enough budget remains to
                     cover its worst-case failure cost. Safe deploys are
                     always allowed, since they carry no failure cost.

POST /traffic/<mode> records baseline successful requests to establish
the budget window.
GET /status returns current totals and remaining budget for both modes.
POST /reset restores both to a clean baseline.
"""

from flask import Flask, request, jsonify

app = Flask(__name__)

SLO_PERCENT = 99                      # target success rate
BUDGET_WINDOW_REQUESTS = 1000         # rolling window size
ERROR_BUDGET = BUDGET_WINDOW_REQUESTS * (100 - SLO_PERCENT) // 100  # 10 allowed failures
RISKY_DEPLOY_FAILURE_COST = 8          # failures a risky deploy generates, if allowed through

naive_total_requests = 0
naive_total_failures = 0

gated_total_requests = 0
gated_total_failures = 0
gated_deploys_blocked = 0


@app.route("/traffic/<mode>", methods=["POST"])
def traffic(mode):
    global naive_total_requests, gated_total_requests

    if mode == "naive":
        naive_total_requests += 1
    else:
        gated_total_requests += 1

    return jsonify({"mode": mode, "status": "recorded"})


@app.route("/deploy/naive", methods=["POST"])
def deploy_naive():
    global naive_total_requests, naive_total_failures

    data = request.get_json()
    risk_level = data["risk_level"]  # "safe" or "risky"

    if risk_level == "risky":
        naive_total_failures += RISKY_DEPLOY_FAILURE_COST
        naive_total_requests += RISKY_DEPLOY_FAILURE_COST

    return jsonify({
        "mode": "naive",
        "risk_level": risk_level,
        "status": "deployed",
    })


@app.route("/deploy/gated", methods=["POST"])
def deploy_gated():
    global gated_total_requests, gated_total_failures, gated_deploys_blocked

    data = request.get_json()
    risk_level = data["risk_level"]

    remaining_budget = ERROR_BUDGET - gated_total_failures

    if risk_level == "risky":
        if remaining_budget < RISKY_DEPLOY_FAILURE_COST:
            gated_deploys_blocked += 1
            return jsonify({
                "mode": "gated",
                "risk_level": risk_level,
                "status": "blocked",
                "reason": f"only {remaining_budget} error budget remaining, "
                          f"need {RISKY_DEPLOY_FAILURE_COST}",
            }), 403

        gated_total_failures += RISKY_DEPLOY_FAILURE_COST
        gated_total_requests += RISKY_DEPLOY_FAILURE_COST

    return jsonify({
        "mode": "gated",
        "risk_level": risk_level,
        "status": "deployed",
    })


@app.route("/status", methods=["GET"])
def status():
    naive_failure_rate = (naive_total_failures / naive_total_requests * 100) if naive_total_requests else 0
    gated_failure_rate = (gated_total_failures / gated_total_requests * 100) if gated_total_requests else 0

    return jsonify({
        "naive": {
            "total_requests": naive_total_requests,
            "total_failures": naive_total_failures,
            "failure_rate_pct": round(naive_failure_rate, 2),
        },
        "gated": {
            "total_requests": gated_total_requests,
            "total_failures": gated_total_failures,
            "failure_rate_pct": round(gated_failure_rate, 2),
            "deploys_blocked": gated_deploys_blocked,
            "remaining_budget": ERROR_BUDGET - gated_total_failures,
        },
    })


@app.route("/reset", methods=["POST"])
def reset():
    global naive_total_requests, naive_total_failures
    global gated_total_requests, gated_total_failures, gated_deploys_blocked
    naive_total_requests = 0
    naive_total_failures = 0
    gated_total_requests = 0
    gated_total_failures = 0
    gated_deploys_blocked = 0
    return jsonify({"status": "reset"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
