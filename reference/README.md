# Reference models

These programs illustrate finite semantics and model-relative checks. They are not deployed security services, provider adapters, or proofs that real providers satisfy the necessary evidence-completeness assumptions.

`two_phase_checks.py` evaluates sixteen targeted deterministic regression cases. Its historical causal traversal is separate from future-guard reachability and its hidden truth bit is not read by the decision procedure. `TWO_PHASE_RESULTS.txt` is the captured exact output.

`nightcrawler_ref.py` is a historically retained synthetic graph model. Its 20,000-world run and ablations can be reproduced with `python3 reference/nightcrawler_ref.py 20000` after installing `networkx` from `requirements-ci.txt`. `RESULTS.txt` also documents a separately run 200,000-world sweep.

The historical synthetic model uses generated fault flags to assign several conditions. Its zero-false-COMPLETE results are therefore **not** independent field validation or an empirical safety guarantee for the newer paper.
