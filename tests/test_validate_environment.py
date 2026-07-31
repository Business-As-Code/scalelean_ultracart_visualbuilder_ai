from __future__ import annotations

from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_environment


BASE = {
    "UVB_ACCOUNT": "test-account",
    "UVB_STOREFRONT_URL": "https://example.invalid",
}

TRANSFER = {
    "UVB_FILE_PROTOCOL": "explicit-ftps",
    "UVB_FILE_HOST": "example.invalid",
    "UVB_FILE_PORT": "21",
    "UVB_FILE_USERNAME": "test-user",
    "UVB_FILE_PASSWORD": "test-password",
    "UVB_FILE_ROOT": "/test",
    "UVB_FILE_PINNED_PUBKEY": "sha256//test",
    "UVB_PRIVATE_ARTIFACT_ROOT": "/tmp/private-test",
}


class ValidateEnvironmentTests(unittest.TestCase):
    def run_main(self, dotenv: dict[str, str]) -> tuple[int, str]:
        output = io.StringIO()
        with (
            patch.object(validate_environment, "load_config", return_value=dotenv),
            patch.dict(validate_environment.os.environ, {}, clear=True),
            redirect_stdout(output),
        ):
            code = validate_environment.main()
        return code, output.getvalue()

    def test_accepts_base_configuration_from_dotenv(self) -> None:
        code, output = self.run_main(BASE)

        self.assertEqual(code, 0)
        self.assertIn("Base configuration is present", output)
        self.assertNotIn("test-account", output)

    def test_accepts_complete_transfer_configuration(self) -> None:
        code, output = self.run_main(BASE | TRANSFER)

        self.assertEqual(code, 0)
        self.assertIn("file-transfer configuration are present", output)
        self.assertNotIn("test-password", output)

    def test_rejects_partial_transfer_configuration(self) -> None:
        code, output = self.run_main(BASE | {"UVB_FILE_HOST": "example.invalid"})

        self.assertEqual(code, 1)
        self.assertIn("Incomplete file-transfer configuration", output)


if __name__ == "__main__":
    unittest.main()
