from __future__ import annotations

import json
from pathlib import Path


def fmt(x: float) -> str:
    # compact scientific formatting
    return f"{x:.6g}"


def main():
    summary = json.loads(Path("outputs/summary.json").read_text())
    params = summary["params"]
    solver = summary["solver"]
    residual = summary["residual"]
    chk = summary["integrated_check"]
    err = summary["analytic_error"]

    m = float(params["m"])
    c = float(params["c"])

    md = []
    md.append("Key numbers are taken from `outputs/summary.json`.\n")
    md.append("| Quantity | Value |\n|---|---:|\n")
    md.append(f"| m | {fmt(m)} |\n")
    md.append(f"| c | {fmt(c)} |\n")
    md.append(f"| stop threshold eps_stop | {params['eps_stop']:.1e} |\n")
    md.append(f"| theoretical front position $\\xi_\\mathrm{{front}}$ | {fmt(summary['xi_front_theory'])} |\n")
    md.append(f"| event termination $\\xi_\\mathrm{{end}}$ (where $f=\\varepsilon$) | {fmt(solver['xi_end_event'])} |\n")
    md.append(f"| residual $\\|R\\|_2$ | {fmt(residual['l2'])} |\n")
    md.append(f"| residual $\\|R\\|_\\infty$ | {fmt(residual['linf'])} |\n")
    md.append(f"| residual relative $\\|R\\|_2$ | {fmt(residual['rel_l2'])} |\n")
    md.append(f"| residual relative $\\|R\\|_\\infty$ | {fmt(residual['rel_linf'])} |\n")
    md.append(f"| integrated check $\\|G\\|_2$ | {fmt(chk['G_l2'])} |\n")
    md.append(f"| integrated check $\\|G\\|_\\infty$ | {fmt(chk['G_linf'])} |\n")
    md.append(f"| error vs analytic $\\|f-f_{{\\mathrm{{ref}}}}\\|_2$ | {fmt(err['err_l2'])} |\n")
    md.append(f"| error vs analytic $\\|f-f_{{\\mathrm{{ref}}}}\\|_\\infty$ | {fmt(err['err_linf'])} |\n")

    report_path = Path("report/report.md")
    text = report_path.read_text(encoding="utf-8")

    start = "<!-- RUN_SUMMARY_START -->"
    end = "<!-- RUN_SUMMARY_END -->"
    if start not in text or end not in text:
        raise RuntimeError("Markers not found in report/report.md")

    pre, rest = text.split(start, 1)
    middle, post = rest.split(end, 1)

    new_text = pre + start + "\n" + "".join(md) + end + post
    report_path.write_text(new_text, encoding="utf-8")


if __name__ == "__main__":
    main()
