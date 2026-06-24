from certgen.cli.validate_config import load_config, validate_config


def test_smoke_config_validates():
    config = load_config("configs/certgen_v1_smoke.yaml")
    summary = validate_config(config)
    assert "project=CertGen" in summary
    assert "evidence_status=non_evidence_smoke" in summary
