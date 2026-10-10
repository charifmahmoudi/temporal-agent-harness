"""Run the conventional exhaustive suffix baseline with the original scorer."""
import run_nexus_context
from prepare_nexus_continuations import SUFFIXES

if __name__ == "__main__":
    run_nexus_context.CASES = [f"nexus_continuation_{suffix}_{cache}"
        for suffix in SUFFIXES for cache in ("cached", "cold")]
    run_nexus_context.main()
