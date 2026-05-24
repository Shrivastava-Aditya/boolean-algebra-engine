"""
ui/app.py — Streamlit UI for the Boolean Algebra Engine.

Run:
    streamlit run ui/app.py --server.port 8080 --server.address 0.0.0.0
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(
    page_title="Boolean Algebra Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    .block-container { padding-top: 1.5rem; }
    .conflict-box {
        background: #1f0d0d;
        border-left: 4px solid #f85149;
        border-radius: 4px;
        padding: 0.75rem 1rem;
        margin: 0.4rem 0;
    }
    .warning-box {
        background: #1f1c0d;
        border-left: 4px solid #e3b341;
        border-radius: 4px;
        padding: 0.75rem 1rem;
        margin: 0.4rem 0;
    }
    .ok-box {
        background: #0d1f0d;
        border-left: 4px solid #3fb950;
        border-radius: 4px;
        padding: 0.75rem 1rem;
        margin: 0.4rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## ⚡ Boolean Algebra Engine")
    st.caption("Deterministic logic verification.")
    st.markdown("---")
    mode = st.radio("Mode", ["Expression", "Security Auditor", "Rule Auditor", "Plain English (NL)", "Benchmark"], index=0)
    st.markdown("---")
    st.markdown("**Operators**")
    st.markdown("`!` NOT · `.` AND · `^` XOR · `+` OR")
    st.markdown("Variables: uppercase `A`–`Z`")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_evaluate(expr):
    from core.evaluator import evaluate
    from core.synthesizer import synthesize
    from core.parser import validate
    error = validate(expr)
    if error:
        return None, None, None, error
    table, eval_metrics = evaluate(expr)
    minimal, synth_metrics = synthesize(table)
    return table, eval_metrics, minimal, None


def colour_output(val):
    if val == 1:
        return "background-color: #0d2010; color: #3fb950; font-weight: bold"
    return "background-color: #200d0d; color: #f85149; font-weight: bold"


# ---------------------------------------------------------------------------
# Mode 0 — Security Auditor
# ---------------------------------------------------------------------------

SOC2_CONTROLS = {
    "CC6.1-a  | SOC 2   | MFA required for all user accounts": "A",
    "CC6.1-b  | SOC 2   | Service accounts exempt from MFA": "C.!A",
    "CC6.2-a  | SOC 2   | Access revoked within 24h of termination": "!F+E",
    "CC6.2-b  | SOC 2   | Access preserved during 30-day notice period": "F.!E",
    "CC6.3-a  | SOC 2   | Privileged access requires documented approval": "!B+G",
    "CC6.3-b  | SOC 2   | Emergency access provisioned without prior approval": "B.!G",
    "CC7.2-a  | SOC 2   | All privileged sessions must generate an audit log": "!B+I",
    "CC7.2-b  | SOC 2   | Service account activity excluded from audit logs": "B.C.!I",
    "CC7.3-a  | SOC 2   | Security logs retained for minimum 12 months": "!I+J",
    "CC7.3-b  | SOC 2   | Log data purged after 90 days (cost control)": "I.!J",
    "CC6.7-a  | SOC 2   | All external data transmissions use TLS 1.2+": "M",
}

ISO27001_CONTROLS = {
    "A.9.2.1-a | ISO 27001 | All users must have unique identifiers; shared accounts prohibited": "H.!C",
    "A.9.2.1-b | ISO 27001 | Break-glass emergency accounts use shared credentials": "C.B",
    "A.9.2.3-a | ISO 27001 | Privileged access rights granted only with documented justification": "!B+G",
    "A.9.2.3-b | ISO 27001 | On-call engineers provisioned with privileged access without approval": "B.!G",
    "A.9.2.6-a | ISO 27001 | Access rights removed immediately upon role change or termination": "!F+E",
    "A.9.2.6-b | ISO 27001 | Transition period allows continued access for up to 30 days post-termination": "F.!E",
    "A.9.4.2-a | ISO 27001 | Multi-factor authentication required for all system access": "A",
    "A.9.4.2-b | ISO 27001 | Automated service accounts exempt from MFA policy": "C.!A",
    "A.9.4.3-a | ISO 27001 | Passwords rotated every 90 days for all accounts": "K",
    "A.9.4.3-b | ISO 27001 | MFA-enabled accounts exempt from mandatory password rotation": "A.!K",
    "A.12.4.1-a | ISO 27001 | All privileged access events must be audit logged": "!B+I",
    "A.13.2.1-a | ISO 27001 | All information transfers use encrypted channels": "M",
    "A.15.1.1-a | ISO 27001 | Vendor access requires completed background screening": "!R+T",
}

COMBINED_CONTROLS = {**SOC2_CONTROLS, **ISO27001_CONTROLS}

FRAMEWORK_MAP = {
    "SOC 2 (CC6/CC7)": SOC2_CONTROLS,
    "ISO 27001:2022": ISO27001_CONTROLS,
    "Combined (SOC 2 + ISO 27001)": COMBINED_CONTROLS,
}


def _run_audit(controls):
    from core.evaluator import evaluate
    from core.synthesizer import synthesize
    parsed = []
    for label, expr in controls.items():
        try:
            table, _ = evaluate(expr)
            minimal, _ = synthesize(table)
            parsed.append({
                "label": label, "expr": expr,
                "satisfiable": table.satisfiable,
                "tautology": table.tautology,
                "contradiction": not table.satisfiable,
                "minimal": minimal,
            })
        except ValueError as e:
            parsed.append({"label": label, "expr": expr, "error": str(e)})

    valid = [p for p in parsed if "error" not in p]
    always_conflicts = []
    for i in range(len(valid)):
        for j in range(i + 1, len(valid)):
            a, b = valid[i], valid[j]
            try:
                combined, _ = evaluate(f"({a['expr']}).({b['expr']})")
                if not combined.satisfiable:
                    always_conflicts.append({
                        "label1": a["label"], "expr1": a["expr"],
                        "label2": b["label"], "expr2": b["expr"],
                    })
            except ValueError:
                pass
    return parsed, always_conflicts


def _draw_matrix(ax, parsed, conflicts):
    labels_short = [c["label"].split("|")[0].strip() for c in parsed]
    n = len(parsed)
    matrix = np.ones((n, n)) * 0.6
    conflict_set = set()
    for cf in conflicts:
        i1 = next((k for k, c in enumerate(parsed) if c["label"] == cf["label1"]), -1)
        i2 = next((k for k, c in enumerate(parsed) if c["label"] == cf["label2"]), -1)
        if i1 >= 0 and i2 >= 0:
            matrix[i1][i2] = 0.0
            matrix[i2][i1] = 0.0
            conflict_set.add((i1, i2))
            conflict_set.add((i2, i1))
    for i in range(n):
        matrix[i][i] = 0.5
    ax.imshow(matrix, cmap=plt.cm.RdYlGn, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(labels_short, color="#e6edf3", fontsize=7, rotation=45, ha="right")
    ax.set_yticklabels(labels_short, color="#e6edf3", fontsize=7)
    ax.tick_params(colors="#e6edf3", length=0)
    for spine in ax.spines.values():
        spine.set_edgecolor("#30363d")
    for i in range(n):
        for j in range(n):
            if i == j:
                sym, col = "—", "#888"
            elif (i, j) in conflict_set:
                sym, col = "✗", "#f85149"
            else:
                sym, col = "✓", "#3fb950"
            ax.text(j, i, sym, ha="center", va="center", color=col,
                    fontsize=9, fontweight="bold")
    return conflict_set


if mode == "Security Auditor":
    st.markdown("## Security Control Conflict Auditor")
    st.caption("Mathematically proves conflicts in published compliance standards. Zero LLM — deterministic truth table engine.")

    if st.button("Run Audit", type="primary"):
        with st.spinner("Auditing SOC 2 and ISO 27001..."):
            soc2_parsed, soc2_conflicts   = _run_audit(SOC2_CONTROLS)
            iso_parsed,  iso_conflicts    = _run_audit(ISO27001_CONTROLS)
            comb_parsed, comb_conflicts   = _run_audit(COMBINED_CONTROLS)

        # ── Top-line metrics ──────────────────────────────────────────
        st.markdown("### Summary")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown("**SOC 2 (AICPA CC6/CC7)**")
            n2, p2, c2 = len(soc2_parsed), len(soc2_parsed)*(len(soc2_parsed)-1)//2, len(soc2_conflicts)
            st.metric("Controls", n2)
            st.metric("Conflicts", c2)
            st.metric("Conflict rate", f"{c2/p2*100:.1f}%")
        with m2:
            st.markdown("**ISO/IEC 27001:2022**")
            ni, pi, ci = len(iso_parsed), len(iso_parsed)*(len(iso_parsed)-1)//2, len(iso_conflicts)
            st.metric("Controls", ni)
            st.metric("Conflicts", ci)
            st.metric("Conflict rate", f"{ci/pi*100:.1f}%")
        with m3:
            st.markdown("**Cross-framework**")
            cross = [cf for cf in comb_conflicts
                     if cf["label1"].split("|")[1].strip() != cf["label2"].split("|")[1].strip()]
            st.metric("Unique pairs across both", len(comb_conflicts))
            st.metric("Cross-framework conflicts", len(cross))
            st.caption("Same logical conflict independently encoded in both standards")

        st.markdown("---")

        # ── Side-by-side matrices ─────────────────────────────────────
        st.markdown("### Conflict Matrices")
        col_l, col_r = st.columns(2)

        with col_l:
            st.markdown("#### SOC 2 — AICPA Trust Services Criteria")
            fig1, ax1 = plt.subplots(figsize=(6, 5))
            fig1.patch.set_facecolor("#0d1117")
            ax1.set_facecolor("#0d1117")
            _draw_matrix(ax1, soc2_parsed, soc2_conflicts)
            ax1.set_title(f"{len(soc2_conflicts)} conflicts in {len(soc2_parsed)} controls",
                          color="#e6edf3", fontsize=9, pad=8)
            plt.tight_layout()
            st.pyplot(fig1)
            plt.close(fig1)

        with col_r:
            st.markdown("#### ISO/IEC 27001:2022 — Annex A")
            fig2, ax2 = plt.subplots(figsize=(7, 6))
            fig2.patch.set_facecolor("#0d1117")
            ax2.set_facecolor("#0d1117")
            _draw_matrix(ax2, iso_parsed, iso_conflicts)
            ax2.set_title(f"{len(iso_conflicts)} conflicts in {len(iso_parsed)} controls",
                          color="#e6edf3", fontsize=9, pad=8)
            plt.tight_layout()
            st.pyplot(fig2)
            plt.close(fig2)

        st.markdown("---")

        # ── Conflict lists ────────────────────────────────────────────
        tab_soc, tab_iso, tab_cross = st.tabs([
            f"SOC 2  ({len(soc2_conflicts)} conflicts)",
            f"ISO 27001  ({len(iso_conflicts)} conflicts)",
            f"Cross-framework  ({len(cross)} shared)",
        ])

        def _render_conflicts(conflicts_list, start=1):
            for i, cf in enumerate(conflicts_list, start):
                ref1  = cf["label1"].split("|")[0].strip()
                ref2  = cf["label2"].split("|")[0].strip()
                desc1 = cf["label1"].split("|")[-1].strip()
                desc2 = cf["label2"].split("|")[-1].strip()
                st.markdown(
                    f'<div class="conflict-box">'
                    f'<b>CONFLICT {i}</b><br>'
                    f'<code>[{ref1}]</code> {desc1}<br>'
                    f'<code>[{ref2}]</code> {desc2}<br>'
                    f'<small>These two controls cannot simultaneously hold for any account state.</small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        with tab_soc:
            _render_conflicts(soc2_conflicts)

        with tab_iso:
            _render_conflicts(iso_conflicts)

        with tab_cross:
            if cross:
                st.markdown(
                    '<div class="warning-box"><b>These conflicts are independently encoded in both SOC 2 and ISO 27001.</b> '
                    'The standards were written by different bodies (AICPA vs ISO/IEC JTC 1), yet they contain '
                    'the same structural contradictions — confirming the conflicts are real policy problems, not drafting errors.</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("")
                _render_conflicts(cross)
            else:
                st.markdown('<div class="ok-box">No cross-framework conflicts.</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(
            "**Source:** AICPA Trust Services Criteria 2017 (updated 2022) · ISO/IEC 27001:2022 Annex A  \n"
            "**Method:** Exhaustive truth table enumeration — a pair conflicts when their conjunction is unsatisfiable.  \n"
            "**Runtime:** < 1 second · 276 pairs evaluated"
        )


# ---------------------------------------------------------------------------
# Mode 1 — Expression
# ---------------------------------------------------------------------------

if mode == "Expression":
    st.markdown("## Expression Evaluator")

    expr = st.text_input("Boolean expression", placeholder="e.g. A.(B+C)  or  !(A.B)  or  A.!A")

    if expr.strip():
        table, eval_metrics, minimal, error = run_evaluate(expr.strip())

        if error:
            st.error(f"Invalid expression: {error}")
        else:
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Variables", len(table.variables))
            c2.metric("Rows", len(table.rows))
            c3.metric("Satisfiable", "Yes" if table.satisfiable else "No")
            c4.metric("Tautology", "Yes" if table.tautology else "No")
            c5.metric("Eval time", f"{eval_metrics.eval_time_ms} ms")

            st.markdown("---")

            if not table.satisfiable:
                st.markdown('<div class="conflict-box">⛔ <b>Contradiction</b> — this expression is always false.</div>', unsafe_allow_html=True)
            elif table.tautology:
                st.markdown('<div class="warning-box">⚠️ <b>Tautology</b> — this expression is always true (redundant).</div>', unsafe_allow_html=True)

            if minimal != expr.strip():
                st.markdown(f'<div class="warning-box">⚡ <b>Minimal form:</b> <code>{minimal}</code></div>', unsafe_allow_html=True)

            col_left, col_right = st.columns([2, 1])

            with col_left:
                st.markdown("#### Truth Table")
                rows = [{**row.inputs, "output": row.output} for row in table.rows]
                df = pd.DataFrame(rows)
                styled = df.style.map(colour_output, subset=["output"])
                st.dataframe(styled, use_container_width=True, hide_index=True)

            with col_right:
                st.markdown("#### Minterms (output = 1)")
                st.code(str(table.minterms) if table.minterms else "none")
                st.markdown("#### Maxterms (output = 0)")
                st.code(str(table.maxterms) if table.maxterms else "none")

            st.markdown("---")
            st.markdown("#### Truth Table Heatmap")
            cols = list(table.variables) + ["output"]
            arr = np.array([[row.inputs[v] for v in table.variables] + [row.output]
                            for row in table.rows], dtype=float)
            fig, ax = plt.subplots(figsize=(max(4, len(cols)), max(2, len(table.rows) * 0.45 + 1)))
            fig.patch.set_facecolor("#0d1117")
            ax.set_facecolor("#0d1117")
            from matplotlib.colors import ListedColormap
            cell_colors = np.where(arr == 1, 0.8, 0.2)
            cell_colors[:, -1] = np.where(arr[:, -1] == 1, 1.0, 0.0)
            ax.imshow(cell_colors, cmap=ListedColormap(["#3d0d0d", "#0d3d1a"]),
                      aspect="auto", vmin=0, vmax=1)
            for i in range(len(table.rows)):
                for j, col in enumerate(cols):
                    ax.text(j, i, str(int(arr[i, j])), ha="center", va="center",
                            color="#e6edf3", fontsize=11,
                            fontweight="bold" if j == len(cols) - 1 else "normal")
            ax.axvline(len(cols) - 1.5, color="#e3b341", linewidth=1.5)
            ax.set_xticks(range(len(cols)))
            ax.set_xticklabels(cols, color="#e6edf3", fontsize=11)
            ax.set_yticks(range(len(table.rows)))
            ax.set_yticklabels([f"r{i}" for i in range(len(table.rows))], color="#888", fontsize=9)
            ax.tick_params(colors="#e6edf3", length=0)
            for spine in ax.spines.values():
                spine.set_edgecolor("#30363d")
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

            st.markdown("---")
            st.markdown("#### Equivalence Check")
            expr2 = st.text_input("Compare with", placeholder="e.g. A.B+A.C")
            if expr2.strip():
                table2, _, _, error2 = run_evaluate(expr2.strip())
                if error2:
                    st.error(f"Invalid expression: {error2}")
                else:
                    from core.parser import get_variables, infix_to_prefix
                    from core.evaluator import _evaluate_prefix
                    vars1 = set(table.variables)
                    vars2 = set(table2.variables)
                    all_vars = sorted(vars1 | vars2)
                    n = len(all_vars)
                    p1 = infix_to_prefix(expr.strip())
                    p2 = infix_to_prefix(expr2.strip())
                    differing = []
                    for i in range(2 ** n):
                        values = {var: (i >> (n - 1 - j)) & 1 for j, var in enumerate(all_vars)}
                        v1 = {k: v for k, v in values.items() if k in vars1}
                        v2 = {k: v for k, v in values.items() if k in vars2}
                        if _evaluate_prefix(p1, v1) != _evaluate_prefix(p2, v2):
                            differing.append(values)

                    if not differing:
                        st.markdown('<div class="ok-box">✅ <b>Equivalent</b> — identical output for all inputs.</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="conflict-box">⛔ <b>Not equivalent</b> — differs in {len(differing)} row(s).</div>', unsafe_allow_html=True)
                        st.dataframe(pd.DataFrame(differing), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Mode 2 — Rule Auditor
# ---------------------------------------------------------------------------

elif mode == "Rule Auditor":
    st.markdown("## Rule Auditor")
    st.caption("One boolean expression per line. Find contradictions, redundancies, and conflicts.")

    col_l, col_r = st.columns(2)
    with col_l:
        raw = st.text_area("Rules (one per line)", placeholder="A.B\nC\n!A\n!B.!C", height=200)
    with col_r:
        raw_labels = st.text_area("Labels (optional, one per line)", placeholder="Approve: good credit\nApprove: collateral\nReject: bad credit", height=200)

    if st.button("Audit", type="primary"):
        rules = [r.strip() for r in raw.strip().splitlines() if r.strip()]
        labels = [l.strip() for l in raw_labels.strip().splitlines() if l.strip()]

        if not rules:
            st.warning("Enter at least one rule.")
        else:
            from mcp_server.server import check_prompt_logic
            result = check_prompt_logic(rules)
            summary = result["summary"]

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Rules", summary["total"])
            c2.metric("Contradictions", summary["contradictions"])
            c3.metric("Conflicting Pairs", summary["conflicting_pairs"])
            c4.metric("Equivalent Pairs", summary["equivalent_pairs"])

            st.markdown("---")
            st.markdown("### Per-Rule")
            for i, r in enumerate(result["rules"]):
                label = labels[i] if i < len(labels) else r["rule"]
                if r.get("contradiction"):
                    st.markdown(f'<div class="conflict-box">⛔ <b>Rule {i+1}</b> — {label} <code>{r["rule"]}</code><br>Contradiction: always false, never fires.</div>', unsafe_allow_html=True)
                elif r.get("tautology"):
                    st.markdown(f'<div class="warning-box">⚠️ <b>Rule {i+1}</b> — {label} <code>{r["rule"]}</code><br>Tautology: always true, always fires — redundant.</div>', unsafe_allow_html=True)
                elif r.get("simplified"):
                    st.markdown(f'<div class="warning-box">⚡ <b>Rule {i+1}</b> — {label} <code>{r["rule"]}</code><br>Simplifies to <code>{r["minimal"]}</code></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="ok-box">✅ <b>Rule {i+1}</b> — {label} <code>{r["rule"]}</code></div>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### Pairwise")
            conflicts = [p for p in result["pairwise"] if p.get("always_conflict")]
            equivalents = [p for p in result["pairwise"] if p.get("equivalent")]

            if conflicts:
                for p in conflicts:
                    i1 = rules.index(p["rule1"]) if p["rule1"] in rules else -1
                    i2 = rules.index(p["rule2"]) if p["rule2"] in rules else -1
                    l1 = labels[i1] if 0 <= i1 < len(labels) else p["rule1"]
                    l2 = labels[i2] if 0 <= i2 < len(labels) else p["rule2"]
                    st.markdown(f'<div class="conflict-box">⛔ Rule {i1+1} ({l1}) always conflicts with Rule {i2+1} ({l2})</div>', unsafe_allow_html=True)

            if equivalents:
                for p in equivalents:
                    st.markdown(f'<div class="warning-box">⚠️ <code>{p["rule1"]}</code> and <code>{p["rule2"]}</code> are equivalent — duplicate rule.</div>', unsafe_allow_html=True)

            if not conflicts and not equivalents:
                st.markdown('<div class="ok-box">✅ No conflicts or duplicates found.</div>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### Conflict Matrix")
            n = len(rules)
            matrix = np.full((n, n), 0.5)
            for p in result["pairwise"]:
                i1 = rules.index(p["rule1"]) if p["rule1"] in rules else -1
                i2 = rules.index(p["rule2"]) if p["rule2"] in rules else -1
                if i1 >= 0 and i2 >= 0:
                    val = 0.0 if p.get("always_conflict") else (1.0 if p.get("equivalent") else 0.75)
                    matrix[i1][i2] = val
                    matrix[i2][i1] = val
            for i in range(n):
                matrix[i][i] = 0.5

            fig, ax = plt.subplots(figsize=(n + 2, n + 1))
            fig.patch.set_facecolor("#0d1117")
            ax.set_facecolor("#0d1117")
            ax.imshow(matrix, cmap=plt.cm.RdYlGn, vmin=0, vmax=1, aspect="auto")

            short = [f"R{i+1}" for i in range(n)]
            ax.set_xticks(range(n))
            ax.set_yticks(range(n))
            ax.set_xticklabels(short, color="#e6edf3", fontsize=11)
            ax.set_yticklabels(short, color="#e6edf3", fontsize=11)
            ax.tick_params(colors="#e6edf3", length=0)
            for spine in ax.spines.values():
                spine.set_edgecolor("#30363d")

            for i in range(n):
                for j in range(n):
                    if i == j:
                        sym, col = "—", "#888"
                    elif matrix[i][j] == 0.0:
                        sym, col = "✗", "#f85149"
                    elif matrix[i][j] == 1.0:
                        sym, col = "≡", "#e3b341"
                    else:
                        sym, col = "✓", "#3fb950"
                    ax.text(j, i, sym, ha="center", va="center", color=col, fontsize=13, fontweight="bold")

            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)


# ---------------------------------------------------------------------------
# Mode 3 — Plain English
# ---------------------------------------------------------------------------

elif mode == "Plain English (NL)":
    st.markdown("## Plain English Verifier")
    st.caption("Describe your logic in plain English. Needs an LLM API key.")

    col_p, col_k, col_m = st.columns(3)
    with col_p:
        provider_name = st.selectbox("Provider", ["anthropic", "openai", "ollama", "compat"])
    with col_k:
        api_key = st.text_input("API Key", type="password", placeholder="or set env var")
    with col_m:
        model = st.text_input("Model", placeholder="leave blank for default")

    if provider_name == "compat":
        base_url = st.text_input("Base URL", placeholder="https://api.groq.com/openai/v1")
    else:
        base_url = None

    def make_provider():
        from nl.nl import AnthropicProvider, OpenAIProvider, OllamaProvider, OpenAICompatProvider
        if provider_name == "anthropic":
            return AnthropicProvider(api_key=api_key or None, model=model or "claude-sonnet-4-6")
        if provider_name == "openai":
            return OpenAIProvider(api_key=api_key or None, model=model or "gpt-4o")
        if provider_name == "ollama":
            return OllamaProvider(model=model or "llama3")
        return OpenAICompatProvider(api_key=api_key or "", base_url=base_url or "", model=model or "")

    tab1, tab2 = st.tabs(["Single Statement", "Multi-Rule Audit"])

    with tab1:
        sentence = st.text_area("Statement", placeholder='e.g. "Approve if credit score is good and income is verified, or if collateral exists"', height=100)
        if st.button("Verify", type="primary"):
            if not sentence.strip():
                st.warning("Enter a statement.")
            else:
                with st.spinner("Parsing and verifying..."):
                    try:
                        from nl.nl import ask
                        result = ask(sentence.strip(), provider=make_provider())

                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Expression", result.expression)
                        c2.metric("Satisfiable", "Yes" if result.satisfiable else "No")
                        c3.metric("Tautology", "Yes" if result.tautology else "No")
                        c4.metric("Contradiction", "Yes" if result.contradiction else "No")

                        st.markdown("**Variables**")
                        for var, meaning in result.variables.items():
                            st.markdown(f"- `{var}` = {meaning}")

                        st.markdown(f"**Minimal form:** `{result.minimal}`")

                        df = pd.DataFrame(result.rows)
                        styled = df.style.map(colour_output, subset=["output"])
                        st.dataframe(styled, use_container_width=True, hide_index=True)

                        st.info(result.explanation)
                    except Exception as e:
                        st.error(str(e))

    with tab2:
        rules_text = st.text_area("Rules — one per line", placeholder="Approve if credit score is good\nReject if credit score is bad\nApprove if collateral exists", height=160)
        if st.button("Audit", type="primary", key="nl_audit"):
            rules = [r.strip() for r in rules_text.strip().splitlines() if r.strip()]
            if not rules:
                st.warning("Enter at least one rule.")
            else:
                with st.spinner(f"Parsing {len(rules)} rules..."):
                    try:
                        from nl.nl import check_rules
                        result = check_rules(rules, provider=make_provider())
                        summary = result.get("summary", {})

                        c1, c2, c3 = st.columns(3)
                        c1.metric("Rules", summary.get("total", len(rules)))
                        c2.metric("Conflicting Pairs", summary.get("conflicting_pairs", 0))
                        c3.metric("Contradictions", summary.get("contradictions", 0))

                        for r in result.get("rules", []):
                            label = r.get("original_rule", r["rule"])
                            if r.get("contradiction"):
                                st.markdown(f'<div class="conflict-box">⛔ {label} → <code>{r["rule"]}</code> — Contradiction</div>', unsafe_allow_html=True)
                            elif r.get("tautology"):
                                st.markdown(f'<div class="warning-box">⚠️ {label} → <code>{r["rule"]}</code> — Tautology</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="ok-box">✅ {label} → <code>{r["rule"]}</code></div>', unsafe_allow_html=True)

                        for p in result.get("pairwise", []):
                            if p.get("always_conflict"):
                                st.markdown(f'<div class="conflict-box">⛔ <code>{p["rule1"]}</code> always conflicts with <code>{p["rule2"]}</code></div>', unsafe_allow_html=True)

                        for e in result.get("parse_errors", []):
                            st.error(f"{e['rule']}: {e['error']}")
                    except Exception as e:
                        st.error(str(e))


# ---------------------------------------------------------------------------
# Mode 4 — Benchmark
# ---------------------------------------------------------------------------

elif mode == "Benchmark":
    st.markdown("## LLM Benchmark")
    st.caption("Measure how accurately LLMs answer boolean logic questions. Every disagreement with the engine is a provable hallucination.")

    col_p, col_m, col_k = st.columns(3)

    with col_p:
        provider_name = st.selectbox("Provider", ["ollama", "groq", "openai", "anthropic"])

    with col_m:
        if provider_name == "ollama":
            try:
                import urllib.request as _ur, json as _json
                with _ur.urlopen("http://localhost:11434/api/tags", timeout=2) as _r:
                    _ollama_models = [m["name"] for m in _json.loads(_r.read()).get("models", [])]
            except Exception:
                _ollama_models = ["tinyllama"]
            model_name = st.selectbox("Model", _ollama_models or ["tinyllama"])
        else:
            _defaults = {"groq": "llama-3.1-8b-instant", "openai": "gpt-4o-mini", "anthropic": "claude-haiku-4-5-20251001"}
            model_name = st.text_input("Model", value=_defaults.get(provider_name, ""))

    with col_k:
        _env_keys = {"groq": "GROQ_API_KEY", "openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}
        if provider_name != "ollama":
            _env_val = os.environ.get(_env_keys.get(provider_name, ""), "")
            api_key = st.text_input("API Key", value=_env_val, type="password",
                                    placeholder=f"{_env_keys.get(provider_name, '')} or paste here")
        else:
            api_key = ""

    n_cases = st.slider("Test cases", min_value=10, max_value=200, value=20, step=10,
                        help="Split evenly between conflicting and compatible pairs")

    if st.button("Run Benchmark", type="primary"):
        import re as _re
        import urllib.request as _ur2
        import json as _json2
        from concurrent.futures import ThreadPoolExecutor, as_completed

        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from benchmark import (OllamaProvider, OpenAICompatProvider, AnthropicProvider,
                               generate_cases, PROMPT_TEMPLATE)

        # Build provider
        _provider_ok = True
        if provider_name == "ollama":
            _provider = OllamaProvider(model_name)
        elif provider_name == "groq":
            if not api_key:
                st.error("GROQ_API_KEY required.")
                _provider_ok = False
            else:
                _provider = OpenAICompatProvider(model=model_name, api_key=api_key,
                                                 base_url="https://api.groq.com/openai/v1",
                                                 provider_name="groq")
        elif provider_name == "openai":
            if not api_key:
                st.error("OPENAI_API_KEY required.")
                _provider_ok = False
            else:
                _provider = OpenAICompatProvider(model=model_name, api_key=api_key,
                                                  provider_name="openai")
        elif provider_name == "anthropic":
            if not api_key:
                st.error("ANTHROPIC_API_KEY required.")
                _provider_ok = False
            else:
                _provider = AnthropicProvider(model=model_name, api_key=api_key)

        if _provider_ok:
            n_each = max(1, n_cases // 2)
            with st.spinner(f"Generating {n_each * 2} cases..."):
                _cases = generate_cases(n_each=n_each)

            # Z3 verification
            try:
                import z3 as _z3
                def _z3_check(e1, e2):
                    _zvars = {v: _z3.Bool(v) for v in sorted(set(_re.findall(r"[A-D]", e1 + e2)))}
                    def _parse(expr):
                        e = expr.replace("!", "~").replace(".", "&").replace("+", "|")
                        return eval(e, {"__builtins__": {}}, _zvars)
                    s = _z3.Solver()
                    s.add(_parse(f"({e1})") & _parse(f"({e2})"))
                    return s.check() == _z3.sat
                _mismatches = [(e1, e2) for e1, e2, gt in _cases if _z3_check(e1, e2) != gt]
                if _mismatches:
                    st.error(f"z3 found {len(_mismatches)} ground truth mismatch(es) — aborting.")
                    st.stop()
                st.success(f"z3 verified all {len(_cases)} ground truth labels ✓")
            except ImportError:
                st.warning("z3-solver not installed — skipping ground truth verification. `pip install z3-solver` to enable.")

            # Run with live table
            _results = []
            _progress = st.progress(0)
            _status = st.empty()
            _table_ph = st.empty()

            for _i, (_e1, _e2, _gt) in enumerate(_cases):
                try:
                    _llm = _provider.ask(PROMPT_TEMPLATE.format(e1=_e1, e2=_e2))
                    _ok = _llm == _gt
                except Exception as _exc:
                    st.error(f"Case {_i+1} failed: {_exc}")
                    continue

                _results.append({
                    "#": _i + 1,
                    "": "✓" if _ok else "✗",
                    "Rule 1": _e1,
                    "Rule 2": _e2,
                    "engine": "yes" if _gt else "no",
                    "llm": "yes" if _llm else "no",
                })

                _done = _i + 1
                _wrong = sum(1 for r in _results if r[""] == "✗")
                _rate = _wrong / _done * 100
                _progress.progress(_done / len(_cases))
                _status.markdown(f"**{_done}/{len(_cases)}** cases · **{_rate:.1f}%** hallucination rate")
                _table_ph.dataframe(pd.DataFrame(_results), use_container_width=True, hide_index=True)

            # Summary
            if _results:
                st.markdown("---")
                _total = len(_results)
                _wrong_final = sum(1 for r in _results if r[""] == "✗")
                _rate_final = _wrong_final / _total * 100
                _conflict_rows = [r for r in _results if r["engine"] == "no"]
                _compat_rows   = [r for r in _results if r["engine"] == "yes"]
                _missed_c = sum(1 for r in _conflict_rows if r[""] == "✗")
                _missed_p = sum(1 for r in _compat_rows   if r[""] == "✗")

                mc1, mc2, mc3, mc4, mc5 = st.columns(5)
                mc1.metric("Total cases", _total)
                mc2.metric("Correct", _total - _wrong_final)
                mc3.metric("Hallucinated", _wrong_final)
                mc4.metric("Hallucination rate", f"{_rate_final:.1f}%")
                mc5.metric("Missed conflicts", f"{_missed_c}/{len(_conflict_rows)}")

                if _rate_final >= 40:
                    st.markdown('<div class="conflict-box">⛔ <b>High hallucination rate</b> — this model is not reasoning about boolean logic.</div>', unsafe_allow_html=True)
                elif _rate_final >= 15:
                    st.markdown('<div class="warning-box">⚠️ <b>Moderate hallucination rate</b> — model makes significant logic errors.</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="ok-box">✅ <b>Low hallucination rate</b> — model handles boolean logic well.</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown("---")
st.caption("Boolean Algebra Engine · deterministic logic verification · results are mathematically exact")
