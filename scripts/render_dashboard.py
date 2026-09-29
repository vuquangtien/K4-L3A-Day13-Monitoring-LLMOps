"""Render the six-panel Day 13 dashboard from structured JSONL logs.

This deliberately uses only the standard library so the dashboard can be
generated on every machine that installs the lab requirements:

    .venv/bin/python scripts/render_dashboard.py
"""

from __future__ import annotations

import html
import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
OUTPUT_PATH = REPO_ROOT / "submission" / "evidence" / "11-dashboard-overview.html"


def percentile(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((p / 100) * len(ordered) + 0.5) - 1))
    return ordered[index]


def read_records() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    records = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def panel(title: str, unit: str, threshold: str, body: str) -> str:
    return f"""
    <section class=\"panel\">
      <div class=\"panel-heading\"><h2>{html.escape(title)}</h2><span>{html.escape(unit)}</span></div>
      <div class=\"values\">{body}</div>
      <p class=\"threshold\">Threshold / SLO: {html.escape(threshold)}</p>
    </section>"""


def value(label: str, number: str) -> str:
    return f"<div><strong>{html.escape(number)}</strong><small>{html.escape(label)}</small></div>"


def render(records: list[dict]) -> str:
    received = [record for record in records if record.get("event") == "request_received"]
    responses = [record for record in records if record.get("event") == "response_sent"]
    failures = [record for record in records if record.get("event") == "request_failed"]
    latencies = [float(record["latency_ms"]) for record in responses if "latency_ms" in record]
    ttfts = [float(record["ttft_ms"]) for record in responses if "ttft_ms" in record]
    costs = [float(record.get("cost_usd", 0)) for record in responses]
    input_tokens = sum(int(record.get("tokens_in", 0)) for record in responses)
    output_tokens = sum(int(record.get("tokens_out", 0)) for record in responses)
    quality = [float(record["quality_score"]) for record in responses if "quality_score" in record]
    retrieval = [record for record in responses + failures if record.get("tool_name") == "retrieval"]
    retrieval_success = (
        100 * sum(record.get("tool_success") is True for record in retrieval) / len(retrieval)
        if retrieval
        else 0.0
    )
    error_rate = 100 * len(failures) / len(received) if received else 0.0
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    panels = "".join(
        [
            panel(
                "Latency percentiles and TTFT",
                "milliseconds",
                "P95 latency ≤ 3000 ms",
                value("P50 latency", f"{percentile(latencies, 50):.0f} ms")
                + value("P95 latency", f"{percentile(latencies, 95):.0f} ms")
                + value("P99 latency", f"{percentile(latencies, 99):.0f} ms")
                + value("P95 TTFT", f"{percentile(ttfts, 95):.0f} ms"),
            ),
            panel(
                "Request traffic",
                "requests per minute",
                "≥ 1 request/min baseline",
                value("Requests in window", str(len(received))) + value("Window", "60 minutes"),
            ),
            panel(
                "Error rate and retrieval success",
                "percent",
                "Error rate ≤ 2%; retrieval success ≥ 90%",
                value("Error rate", f"{error_rate:.1f}%")
                + value("Retrieval success", f"{retrieval_success:.1f}%")
                + value("Failures", str(len(failures))),
            ),
            panel(
                "Cost over time",
                "USD",
                "Total ≤ $2.50 / 60-minute window",
                value("Total cost", f"${sum(costs):.6f}") + value("Responses", str(len(responses))),
            ),
            panel(
                "Input and output tokens",
                "tokens",
                "Total ≤ 50,000 tokens / window",
                value("Input tokens", f"{input_tokens:,}") + value("Output tokens", f"{output_tokens:,}"),
            ),
            panel(
                "Quality proxy",
                "score 0–1",
                "Mean quality ≥ 0.75",
                value("Mean quality", f"{mean(quality):.2f}" if quality else "0.00")
                + value("Scored responses", str(len(quality))),
            ),
        ]
    )
    return f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><title>Day 13 LLMOps dashboard</title>
<style>
body {{ font-family: Inter, Arial, sans-serif; margin: 32px; color: #172033; background: #f6f8fc; }}
header {{ display:flex; justify-content:space-between; align-items:baseline; margin-bottom:20px; }}
h1 {{ margin:0; font-size:26px; }} .meta {{ color:#53627c; }}
.grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; }}
.panel {{ background:white; border:1px solid #dce3f0; border-radius:12px; padding:18px; min-height:150px; }}
.panel-heading {{ display:flex; justify-content:space-between; gap:12px; }} h2 {{ font-size:16px; margin:0; }}
.panel-heading span, small {{ color:#53627c; font-size:12px; }} .values {{ display:flex; flex-wrap:wrap; gap:20px; margin:28px 0; }}
strong {{ display:block; color:#0d3c8c; font-size:24px; }} small {{ display:block; margin-top:4px; }}
.threshold {{ border-top:1px solid #e8edf6; color:#53627c; font-size:12px; margin:0; padding-top:12px; }}
</style></head><body><header><div><h1>K4-L3A Monitoring & LLMOps</h1><p class=\"meta\">Structured-log dashboard · last 60 minutes · refresh snapshot</p></div><p class=\"meta\">Generated {timestamp}</p></header>
<main class=\"grid\">{panels}</main></body></html>"""


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render(read_records()), encoding="utf-8")
    print(f"Dashboard written to {OUTPUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
