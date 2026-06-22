"""Stage report writer -- emits the TESTING_PLAN report skeleton as markdown.

Same skeleton as the SPICE reports so bench and sim results are comparable.
Output lands in ``reports/test/`` (generated, committed for traceability).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as date_cls
from pathlib import Path
from typing import List, Optional, Sequence

from lib.paths import REPORT_DIR, ensure_dir


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    head = "| " + " | ".join(str(h) for h in headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = [
        "| " + " | ".join(_fmt(c) for c in row) + " |"
        for row in rows
    ]
    return "\n".join([head, sep, *body])


def _fmt(cell: object) -> str:
    if isinstance(cell, float):
        return f"{cell:.6g}"
    return str(cell)


@dataclass
class StageReport:
    """Builds one markdown report following the TESTING_PLAN skeleton."""

    stage_name: str
    objective: str
    kind: str = "bench"               # "bench" | "sim"
    setup: str = ""
    method: str = ""
    results_intro: str = ""
    results_table: Optional[str] = None
    figures: List[str] = field(default_factory=list)
    passed: Optional[bool] = None
    criterion: str = ""
    margin: str = ""
    anomalies: str = ""
    next_action: str = ""
    run_date: Optional[str] = None

    def render(self) -> str:
        d = self.run_date or date_cls.today().isoformat()
        verdict = "N/A"
        if self.passed is True:
            verdict = "PASS"
        elif self.passed is False:
            verdict = "FAIL"

        lines: List[str] = []
        lines.append(f"# {self.stage_name} — {d} — {self.kind}")
        lines.append("")
        lines.append("## Objective")
        lines.append(self.objective.strip() or "_TBD_")
        lines.append("")
        lines.append("## Setup")
        lines.append(self.setup.strip() or "_TBD_")
        lines.append("")
        lines.append("## Method")
        lines.append(self.method.strip() or "_TBD_")
        lines.append("")
        lines.append("## Results")
        if self.results_intro.strip():
            lines.append(self.results_intro.strip())
            lines.append("")
        if self.results_table:
            lines.append(self.results_table)
            lines.append("")
        for fig in self.figures:
            lines.append(f"![{Path(fig).stem}]({fig})")
        if not self.results_table and not self.figures and not self.results_intro.strip():
            lines.append("_No results recorded._")
        lines.append("")
        lines.append("## Pass / Fail")
        crit = self.criterion.strip() or "_criterion TBD_"
        margin = f" — {self.margin.strip()}" if self.margin.strip() else ""
        lines.append(f"{crit}\n\n**{verdict}**{margin}")
        lines.append("")
        lines.append("## Anomalies & notes")
        lines.append(self.anomalies.strip() or "None.")
        lines.append("")
        lines.append("## Next")
        lines.append(self.next_action.strip() or "_TBD_")
        lines.append("")
        return "\n".join(lines)

    def write(self, out_dir: Path = REPORT_DIR, filename: Optional[str] = None) -> Path:
        ensure_dir(out_dir)
        if filename is None:
            slug = self.stage_name.lower().split("—")[0].strip().replace(" ", "_")
            d = (self.run_date or date_cls.today().isoformat()).replace("-", "")
            filename = f"{slug}_{d}.md"
        path = out_dir / filename
        path.write_text(self.render(), encoding="utf-8")
        return path