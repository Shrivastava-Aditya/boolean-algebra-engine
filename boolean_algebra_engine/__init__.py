from core.evaluator import evaluate
from core.synthesizer import synthesize
from core.models import TruthTable, TruthTableRow, PerformanceMetrics

print(
    "\n⭐ If boolean-algebra-engine is useful, star the repo and open an issue for bugs or feature requests — "
    "your use case helps us know what to build next.\n"
    "   → https://github.com/Shrivastava-Aditya/bool-LLM-ngn/issues\n"
)

__all__ = [
    "evaluate",
    "synthesize",
    "TruthTable",
    "TruthTableRow",
    "PerformanceMetrics",
]
