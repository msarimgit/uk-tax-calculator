import os
from dataclasses import asdict
from flask import Flask, render_template, request, jsonify

from tax_rates import calculate_tax, compare_regions, REGIONS

app = Flask(__name__)


def result_to_dict(result):
    d = asdict(result)
    return d


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/calculate", methods=["GET"])
def api_calculate():
    try:
        income = float(request.args.get("income", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "income must be a number"}), 400

    if income < 0:
        return jsonify({"error": "income cannot be negative"}), 400
    if income > 10_000_000:
        return jsonify({"error": "income is unrealistically large"}), 400

    comp = compare_regions(income)
    return jsonify({
        "ruk": result_to_dict(comp["ruk"]),
        "scotland": result_to_dict(comp["scotland"]),
        "difference": comp["difference"],
    })


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
