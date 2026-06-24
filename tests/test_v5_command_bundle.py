from pathlib import Path

from certgen.commands.generate_v5_command_bundle import generate_v5_command_bundle


def test_v5_command_bundle_safe_scripts(tmp_path):
    payload = generate_v5_command_bundle(tmp_path)
    assert len(payload["scripts"]) == 7
    for script in payload["scripts"]:
        path = Path(script)
        text = path.read_text(encoding="utf-8")
        assert "set -euo pipefail" in text
        assert "/Users/" not in text
        assert path.stat().st_mode & 0o111
    assert "CERTGEN_LEDGER" in (tmp_path / "01_validate_provenance_ledger.sh").read_text(encoding="utf-8")
