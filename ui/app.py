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
    mode = st.radio("Mode", ["Expression", "Rule Auditor", "Plain English (NL)"], index=0)
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
# Footer
# ---------------------------------------------------------------------------

st.markdown("---")
st.caption("Boolean Algebra Engine · deterministic logic verification · results are mathematically exact")
