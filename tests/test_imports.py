def test_package_imports():
    import certgen
    import certgen.certs.decision
    import certgen.cli.make_smoke_artifacts
    import certgen.core.io
    import certgen.gates.claim_gate
    import certgen.metrics.registry
    import certgen.pilots.registry
    import certgen.reporting.certificate_report

    assert certgen.__version__
