"""ML layer (owner: Asim).

Pluggable replacements for the two context classifiers the scoring model uses:

* endpoint sensitivity (URL path -> CRITICAL/HIGH/MEDIUM/LOW), and
* response-body signals (credentials / PII / financial / internal IP).

The engine currently uses the built-in implementations in
:mod:`app.core.sensitivity` and :mod:`app.core.body_classifier`. Anything here
must satisfy the Protocols in :mod:`app.ml.interfaces` so it can be swapped in
without touching the engine or the CVSS code.
"""
