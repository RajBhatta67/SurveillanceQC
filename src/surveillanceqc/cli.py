"""CLI: stdout is the report; input is never opened for writing."""
import argparse
import json
from pathlib import Path
import sys

from . import __version__
from .checks import Config, check_csv


def render_text(report: dict) -> str:
    s = report["summary"]
    lines = [f"SurveillanceQC {report['tool_version']} — {report['source']['name']}",
             f"{report['rows_read']} records; {s['error']} error(s); {s['warning']} warning(s)",
             f"Analysis complete: {report['analysis_complete']}",
             f"Subset check: {report['subset_check']}"]
    for finding in report["findings"]:
        location = f"records {finding['rows']}" if finding['rows'] else "file/group"
        lines.append(f"{finding['severity'].upper()} {finding['code']} ({location}; {', '.join(finding['columns'])}): {finding['message']}")
        if finding["context"]:
            lines.append("  " + json.dumps(finding["context"], ensure_ascii=False, sort_keys=True))
    lines.append("Findings assess the configured schema; they do not validate surveillance accuracy.")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check aggregate count CSVs without changing data.")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--country", default="country")
    parser.add_argument("--period", default="period")
    parser.add_argument("--frequency", choices=["month", "year"], default="month")
    parser.add_argument("--count", action="append", help="Count column; repeat. Defaults to total_cases and lab_confirmed.")
    parser.add_argument("--key-column", action="append", default=[], help="Additional identity column, e.g. disease; repeat.")
    parser.add_argument("--missing-token", action="append", default=[], help="Explicit missing marker; repeat. Blank is always missing.")
    parser.add_argument("--lab", default="lab_confirmed")
    parser.add_argument("--total", default="total_cases")
    parser.add_argument("--subset-basis", help="Enable lab <= total ONLY with documented subset and same scope; record rationale/source here.")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    parser.add_argument("--fail-on", choices=["error", "warning"], default="error")
    args = parser.parse_args(argv)
    try:
        cfg = Config(country=args.country, period=args.period,
                     counts=tuple(args.count or ["total_cases", "lab_confirmed"]),
                     frequency=args.frequency, key_columns=tuple(args.key_column),
                     missing_tokens=tuple(args.missing_token), lab=args.lab,
                     total=args.total, subset_basis=args.subset_basis)
        report = check_csv(args.csv, cfg)
    except (ValueError, OSError, UnicodeError) as error:
        print(f"surveillanceqc: {error}", file=sys.stderr)
        return 2
    output = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n" if args.format == "json" else render_text(report)
    sys.stdout.write(output)
    return int(bool(report["summary"]["error"] or
                    (args.fail_on == "warning" and report["summary"]["warning"])))
