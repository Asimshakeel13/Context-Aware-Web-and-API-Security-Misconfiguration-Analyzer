"""ML layer (owner: Asim).

The two context classifiers the scoring model uses, with the interfaces from
docs/cvss-mapping-contract.md (types in :mod:`app.core.contracts`):

* :func:`app.ml.sensitivity.classify` -- endpoint -> SensitivityClass
* :func:`app.ml.body_classifier.analyze` -- response -> set[BodySignal]

Both are stubs that delegate to the built-in classifiers in ``app.core`` until
Asim replaces them; ``tests/unit/test_ml_stubs.py`` keeps them conforming.
"""
