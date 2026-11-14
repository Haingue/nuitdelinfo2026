"""
Tests pour la validation du token SonarCloud (sonar.py)
"""

import io
import json
from unittest.mock import patch

from quality_factory.sonar import validate_token


def _response(payload: dict):
    """Fabrique un faux objet réponse utilisable en context manager."""
    class FakeResponse(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    return FakeResponse(json.dumps(payload).encode())


class TestValidateToken:
    def test_valid_token(self):
        with patch("quality_factory.sonar.urlopen", return_value=_response({"valid": True})):
            assert validate_token("https://sonarcloud.io", "good-token") is True

    def test_invalid_token(self):
        with patch("quality_factory.sonar.urlopen", return_value=_response({"valid": False})):
            assert validate_token("https://sonarcloud.io", "bad-token") is False

    def test_network_error_does_not_block(self):
        """En cas d'erreur réseau, on laisse le scanner trancher."""
        with patch("quality_factory.sonar.urlopen", side_effect=TimeoutError):
            assert validate_token("https://sonarcloud.io", "any-token") is True
