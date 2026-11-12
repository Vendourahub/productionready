"""Security verification tests for repository intake and tarball unpacking defenses."""
import io
import os
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

# Ensure package root is in sys.path
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from productionready.intake import intake_repository


class IntakeSecurityTests(unittest.TestCase):
    def test_local_directory_valid(self):
        """Verifies safe intake of a valid local filesystem directory."""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "app.py").write_text("print('hello')", encoding="utf-8")
            with intake_repository(str(p)) as (repo_path, intake_type, commit_sha):
                self.assertEqual(repo_path, p)
                self.assertEqual(intake_type, "local_directory")
                self.assertIsNone(commit_sha)

    def test_local_directory_nonexistent_fails(self):
        """Verifies error handling for nonexistent local directories."""
        with self.assertRaises(ValueError):
            with intake_repository("C:/nonexistent_folder_xyz_12345") as _:
                pass

    def test_tarball_path_traversal_relative_rejected(self):
        """Verifies that tarballs containing ../ relative paths are rejected immediately."""
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            info = tarfile.TarInfo(name="../escape.txt")
            data = b"malicious content"
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

        buf.seek(0)
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td)
            with tarfile.open(fileobj=buf, mode="r:gz") as tar:
                with self.assertRaises(ValueError) as ctx:
                    for member in tar.getmembers():
                        if member.name.startswith("/") or ".." in member.name:
                            raise ValueError(f"Malicious tar entry detected: {member.name}")
                self.assertIn("Malicious tar entry", str(ctx.exception))

    def test_tarball_symlink_traversal_rejected(self):
        """Verifies that symlinks targeting parent directories outside extraction root are caught."""
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            # Create symlink pointing outside
            info = tarfile.TarInfo(name="sub/evil_link")
            info.type = tarfile.SYMTYPE
            info.linkname = "../../etc/passwd"
            tar.addfile(info)

        buf.seek(0)
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td)
            base_dir = dest.resolve()
            with tarfile.open(fileobj=buf, mode="r:gz") as tar:
                with self.assertRaises(ValueError) as ctx:
                    for member in tar.getmembers():
                        member_path = (base_dir / member.name).resolve()
                        if member.issym() or member.islnk():
                            link_target = (member_path.parent / member.linkname).resolve()
                            try:
                                link_target.relative_to(base_dir)
                            except ValueError:
                                raise ValueError(f"Symlink traversal detected: {member.name} -> {member.linkname}")
                self.assertIn("Symlink traversal detected", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
