"""CSV validation with explicit assumptions and deterministic JSON-ready reports."""
from collections import Counter, defaultdict
import csv
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import io
from pathlib import Path
import re


@dataclass(frozen=True)
class Config:
    country: str = "country"
    period: str = "period"
    counts: tuple[str, ...] = ("total_cases", "lab_confirmed")
    frequency: str = "month"
    key_columns: tuple[str, ...] = ()
    missing_tokens: tuple[str, ...] = ()
    lab: str = "lab_confirmed"
    total: str = "total_cases"
    subset_basis: str | None = None

    def __post_init__(self):
        if self.frequency not in ("month", "year"):
            raise ValueError("frequency must be month or year")
        columns = (self.country, self.period, *self.key_columns, *self.counts)
        if not self.counts or any(not c.strip() for c in columns):
            raise ValueError("configure at least one count and nonempty column names")
        if len(set(columns)) != len(columns):
            raise ValueError("key, period, and count columns must be distinct")
        if self.subset_basis is not None:
            if not self.subset_basis.strip():
                raise ValueError("subset_basis must explain the shared scope and subset definition")
            if self.lab == self.total or not {self.lab, self.total} <= set(self.counts):
                raise ValueError("subset columns must be distinct configured count columns")


def _period_index(value: str, frequency: str) -> int | None:
    pattern = r"[0-9]{4}-[0-9]{2}" if frequency == "month" else r"[0-9]{4}"
    if not re.fullmatch(pattern, value):
        return None
    year = int(value[:4])
    if not 1 <= year <= 9999:
        return None
    if frequency == "year":
        return year
    month = int(value[5:])
    return year * 12 + month - 1 if 1 <= month <= 12 else None


def _format_period(index: int, frequency: str) -> str:
    if frequency == "year":
        return f"{index:04d}"
    year, month = divmod(index, 12)
    return f"{year:04d}-{month + 1:02d}"


def check_csv(path: str | Path, config: Config | None = None) -> dict:
    """Read UTF-8 CSV without writing to it. Row numbers are CSV record ordinals.

    OSError/UnicodeError are operational failures handled by the CLI. Malformed
    CSV and schema problems are findings. Blank physical lines are ignored by csv.
    """
    cfg = config or Config()
    raw = Path(path).read_bytes()
    findings = []
    report = {
        "report_version": "1.0", "tool_version": "0.1.1rc1",
        "source": {"name": Path(path).name, "sha256": hashlib.sha256(raw).hexdigest()},
        "config": asdict(cfg), "rows_read": 0, "analysis_complete": True,
        "subset_check": "enabled_by_user" if cfg.subset_basis is not None else "skipped_no_definition",
        "findings": findings,
    }

    def add(code, severity, message, rows=(), columns=(), **context):
        findings.append(dict(code=code, severity=severity, message=message,
                             rows=list(rows), columns=list(columns), context=context))

    def finish():
        report["summary"] = {s: sum(f["severity"] == s for f in findings)
                             for s in ("error", "warning")}
        return report

    reader = csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
    try:
        header = next(reader, None)
        if not header:
            add("EMPTY_FILE", "error", "No CSV header found.")
            report["analysis_complete"] = False
            return finish()
        duplicates = [c for c, n in Counter(header).items() if n > 1]
        if duplicates or any(not c.strip() for c in header):
            add("INVALID_HEADER", "error", "Headers must be nonempty and unique.", columns=duplicates)
            report["analysis_complete"] = False
            return finish()
        required = (cfg.country, cfg.period, *cfg.key_columns, *cfg.counts)
        absent = [c for c in required if c not in header]
        if absent:
            add("MISSING_COLUMNS", "error", "Required configured columns are absent.", columns=absent)
            report["analysis_complete"] = False
            return finish()
        keys = {}
        groups = defaultdict(set)
        missing = {"", *(t.strip() for t in cfg.missing_tokens)}
        for row_number, cells in enumerate(reader, start=2):
            report["rows_read"] += 1
            if len(cells) != len(header):
                add("ROW_WIDTH", "error", "Record has a different field count from the header.",
                    [row_number], expected=len(header), actual=len(cells))
                continue
            row = dict(zip(header, cells))
            group_columns = (cfg.country, *cfg.key_columns)
            key_valid = True
            for col in group_columns:
                if row[col].strip() in missing:
                    add("MISSING_KEY", "error", "Record identity is missing.", [row_number], [col])
                    key_valid = False
                elif row[col] != row[col].strip():
                    add("KEY_WHITESPACE", "warning", "Key has outer whitespace; identity uses exact text.",
                        [row_number], [col])
            period = (None if row[cfg.period].strip() in missing
                      else _period_index(row[cfg.period], cfg.frequency))
            if row[cfg.period].strip() in missing:
                add("MISSING_PERIOD", "error", "Reporting period is missing.", [row_number], [cfg.period])
            elif period is None:
                add("INVALID_PERIOD", "error", "Period must be YYYY-MM (month) or YYYY (year), as configured.",
                    [row_number], [cfg.period])
            if key_valid and period is not None:
                group = tuple(row[c] for c in group_columns)
                key = (*group, period)
                if key in keys:
                    add("DUPLICATE_KEY", "error", "Repeated configured identity and reporting period; review strata or revisions.",
                        [keys[key], row_number], [*group_columns, cfg.period])
                else:
                    keys[key] = row_number
                groups[group].add(period)
            numbers = {}
            for col in cfg.counts:
                text = row[col].strip()
                if text in missing:
                    add("MISSING_COUNT", "warning", "Count is missing; no zero was substituted.", [row_number], [col])
                    continue
                try:
                    # Decimal avoids float rounding for large integral counts.
                    if not re.fullmatch(r"[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?", text):
                        raise InvalidOperation
                    number = Decimal(text)
                    if not number.is_finite() or number != number.to_integral_value():
                        raise InvalidOperation
                except InvalidOperation:
                    add("INVALID_COUNT", "error", "Count must be a finite whole number; rates and separators are unsupported.",
                        [row_number], [col])
                    continue
                if number < 0:
                    add("NEGATIVE_COUNT", "error", "Count is negative under the configured count schema.", [row_number], [col])
                else:
                    numbers[col] = number
            if cfg.subset_basis is not None and {cfg.lab, cfg.total} <= numbers.keys():
                if numbers[cfg.lab] > numbers[cfg.total]:
                    add("SUBSET_EXCEEDS_TOTAL", "error", "Lab count exceeds total under the user-declared subset definition.",
                        [row_number], [cfg.lab, cfg.total])
        # Warn only about interior gaps within each observed group, not unobserved
        # countries, leading/trailing periods, or an assumed global date range.
        for group, periods in sorted(groups.items()):
            ordered = sorted(periods)
            for previous, current in zip(ordered, ordered[1:]):
                if current - previous > 1:
                    add("PERIOD_GAP", "warning", "Interior period(s) absent; confirm the expected reporting schedule.",
                        columns=[*group_columns, cfg.period], group=dict(zip(group_columns, group)),
                        first_missing=_format_period(previous + 1, cfg.frequency),
                        last_missing=_format_period(current - 1, cfg.frequency),
                        missing_period_count=current - previous - 1)
        if report["rows_read"] == 0:
            add("NO_OBSERVATIONS", "warning", "Header exists but there are no observations.")
    except csv.Error:
        add("MALFORMED_CSV", "error", "CSV parsing failed; findings before this point are partial.")
        report["analysis_complete"] = False
    return finish()
