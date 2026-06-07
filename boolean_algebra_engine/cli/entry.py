import sys


def entrypoint():
    try:
        from boolean_algebra_engine.cli.main import _entrypoint
    except ImportError:
        sys.exit(
            "boolcalc requires CLI dependencies.\n"
            "Install them with:  pip install 'boolean-algebra-engine[cli]'"
        )
    _entrypoint()
