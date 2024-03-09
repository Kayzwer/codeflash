import os
import unittest
from unittest.mock import mock_open, patch

from returns.result import Success, Failure

from codeflash.code_utils.shell_utils import save_api_key_to_rc, read_api_key_from_shell_config


class TestShellUtils(unittest.TestCase):

    @patch(
        "codeflash.code_utils.shell_utils.open",
        new_callable=mock_open,
        read_data="existing content",
    )
    @patch("codeflash.code_utils.shell_utils.get_shell_rc_path")
    def test_save_api_key_to_rc_success(self, mock_get_shell_rc_path, mock_file):
        mock_get_shell_rc_path.return_value = "/fake/path/.bashrc"
        api_key = "cf-12345"
        result = save_api_key_to_rc(api_key)
        self.assertTrue(isinstance(result, Success))
        mock_file.assert_called_with("/fake/path/.bashrc", "r+", encoding="utf8")
        handle = mock_file()
        handle.write.assert_called_once()
        handle.truncate.assert_called_once()

    @patch(
        "codeflash.code_utils.shell_utils.open",
        new_callable=mock_open,
        read_data="existing content",
    )
    @patch("codeflash.code_utils.shell_utils.get_shell_rc_path")
    def test_save_api_key_to_rc_failure(self, mock_get_shell_rc_path, mock_file):
        mock_get_shell_rc_path.return_value = "/fake/path/.bashrc"
        mock_file.side_effect = IOError("Permission denied")
        api_key = "cf-12345"
        result = save_api_key_to_rc(api_key)
        self.assertTrue(isinstance(result, Failure))
        mock_file.assert_called_once_with("/fake/path/.bashrc", "r+", encoding="utf8")


# unit tests
class TestReadApiKeyFromShellConfig(unittest.TestCase):

    def setUp(self):
        """Setup a temporary shell configuration file for testing."""
        self.test_rc_path = "test_shell_rc"
        self.api_key = "cf-1234567890abcdef"
        os.environ["SHELL"] = "/bin/bash"  # Set a default shell for testing

    def tearDown(self):
        """Cleanup the temporary shell configuration file after testing."""
        if os.path.exists(self.test_rc_path):
            os.remove(self.test_rc_path)
        del os.environ["SHELL"]  # Remove the SHELL environment variable

    def test_valid_api_key(self):
        with patch("codeflash.code_utils.shell_utils.get_shell_rc_path") as mock_get_shell_rc_path:
            mock_get_shell_rc_path.return_value = self.test_rc_path
            with patch(
                "builtins.open", mock_open(read_data=f'export CODEFLASH_API_KEY="{self.api_key}"\n')
            ) as mock_file:
                self.assertEqual(read_api_key_from_shell_config(), self.api_key)
                mock_file.assert_called_once_with(self.test_rc_path, "r", encoding="utf8")

    @patch("codeflash.code_utils.shell_utils.get_shell_rc_path")
    def test_no_api_key(self, mock_get_shell_rc_path):
        """Test with no API key export."""
        mock_get_shell_rc_path.return_value = self.test_rc_path
        with patch("builtins.open", mock_open(read_data="# No API key here\n")) as mock_file:
            self.assertIsNone(read_api_key_from_shell_config())
            mock_file.assert_called_once_with(self.test_rc_path, "r", encoding="utf8")

    @patch("codeflash.code_utils.shell_utils.get_shell_rc_path")
    def test_malformed_api_key_export(self, mock_get_shell_rc_path):
        """Test with a malformed API key export."""
        mock_get_shell_rc_path.return_value = self.test_rc_path
        with patch(
            "builtins.open", mock_open(read_data=f"export CODEFLASH_API_KEY={self.api_key}\n")
        ) as mock_file:
            self.assertIsNone(read_api_key_from_shell_config())
            mock_file.assert_called_once_with(self.test_rc_path, "r", encoding="utf8")

    @patch("codeflash.code_utils.shell_utils.get_shell_rc_path")
    def test_multiple_api_key_exports(self, mock_get_shell_rc_path):
        """Test with multiple API key exports."""
        mock_get_shell_rc_path.return_value = self.test_rc_path
        with patch(
            "builtins.open",
            mock_open(
                read_data=f'export CODEFLASH_API_KEY="firstkey"\nexport CODEFLASH_API_KEY="{self.api_key}"\n'
            ),
        ) as mock_file:
            self.assertEqual(read_api_key_from_shell_config(), self.api_key)
            mock_file.assert_called_once_with(self.test_rc_path, "r", encoding="utf8")

    @patch("codeflash.code_utils.shell_utils.get_shell_rc_path")
    def test_api_key_export_with_extra_text(self, mock_get_shell_rc_path):
        """Test with extra text around API key export."""
        mock_get_shell_rc_path.return_value = self.test_rc_path
        with patch(
            "builtins.open",
            mock_open(
                read_data=f'# Setting API Key\nexport CODEFLASH_API_KEY="{self.api_key}"\n# Done\n'
            ),
        ):
            self.assertEqual(read_api_key_from_shell_config(), self.api_key)

    @patch("codeflash.code_utils.shell_utils.get_shell_rc_path")
    def test_api_key_in_comment(self, mock_get_shell_rc_path):
        """Test with API key export in a comment."""
        mock_get_shell_rc_path.return_value = self.test_rc_path
        with patch(
            "builtins.open", mock_open(read_data=f'# export CODEFLASH_API_KEY="{self.api_key}"\n')
        ):
            self.assertIsNone(read_api_key_from_shell_config())

    @patch("codeflash.code_utils.shell_utils.get_shell_rc_path")
    def test_file_does_not_exist(self, mock_get_shell_rc_path):
        """Test when the shell configuration file does not exist."""
        mock_get_shell_rc_path.return_value = self.test_rc_path
        with patch("builtins.open", side_effect=FileNotFoundError):
            self.assertIsNone(read_api_key_from_shell_config())

    @patch("codeflash.code_utils.shell_utils.get_shell_rc_path")
    def test_file_not_readable(self, mock_get_shell_rc_path):
        """Test when the shell configuration file is not readable."""
        mock_get_shell_rc_path.return_value = self.test_rc_path
        with patch("builtins.open", side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                read_api_key_from_shell_config()

        self.assertEqual(read_api_key_from_shell_config(), self.api_key)


if __name__ == "__main__":
    unittest.main()
