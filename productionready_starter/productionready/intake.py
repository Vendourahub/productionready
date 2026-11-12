"""Repository intake engine supporting local paths and ephemeral GitHub fetching.

Enforces zero-storage policy: remote code is extracted to temporary scratch space
and purged immediately upon scan completion.
"""
from __future__ import annotations
import contextlib
import io
import json
import os
import re
import shutil
import tarfile
import tempfile
import urllib.request
import urllib.error
from pathlib import Path
from typing import Generator, Optional, Tuple


GITHUB_REPO_REGEX = re.compile(
    r"^(?:https?://github\.com/)?([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+?)(?:\.git)?$"
)


IntakeResult = Tuple[Path, str, Optional[str]]


def parse_github_spec(repo_spec: str) -> Optional[Tuple[str, str]]:
    """Extracts (owner, repo) from a GitHub URL or 'owner/repo' string."""
    m = GITHUB_REPO_REGEX.match(repo_spec.strip().rstrip("/"))
    if m:
        return m.group(1), m.group(2)
    return None


@contextlib.contextmanager
def intake_repository(
    target: str,
    github_token: Optional[str] = None,
    ref: Optional[str] = None,
) -> Generator[Tuple[Path, str, Optional[str]], None, None]:
    """Yields (resolved_dir_path, intake_type, commit_sha) inside an ephemeral context.

    If target is a local path, resolves and yields it directly.
    If target is a GitHub repository, downloads the tarball ephemerally, extracts to
    a TemporaryDirectory, yields the path, and wipes the directory when done.
    """
    github_parsed = parse_github_spec(target)
    
    if github_parsed and not Path(target).exists():
        owner, repo = github_parsed
        ref_branch = ref or "main"
        url = f"https://api.github.com/repos/{owner}/{repo}/tarball/{ref_branch}"
        
        headers = {
            "User-Agent": "ProductionReady-Scanner/0.2.0",
            "Accept": "application/vnd.github.v3+json",
        }
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"
            
        req = urllib.request.Request(url, headers=headers)
        
        with tempfile.TemporaryDirectory(prefix="prodready_intake_") as temp_dir:
            temp_path = Path(temp_dir)
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    tar_data = resp.read()
                    commit_sha = resp.headers.get("ETag", "").strip('"') or None
            except urllib.error.HTTPError as e:
                if e.code == 404 and ref_branch == "main":
                    # Fallback to master if main doesn't exist
                    fallback_url = f"https://api.github.com/repos/{owner}/{repo}/tarball/master"
                    req_fallback = urllib.request.Request(fallback_url, headers=headers)
                    with urllib.request.urlopen(req_fallback, timeout=30) as resp:
                        tar_data = resp.read()
                        commit_sha = resp.headers.get("ETag", "").strip('"') or None
                else:
                    raise RuntimeError(f"Failed to fetch GitHub repository '{owner}/{repo}': HTTP {e.code} - {e.reason}") from e

            # Extract tarball safely with path and symlink traversal defenses
            with tarfile.open(fileobj=io.BytesIO(tar_data), mode="r:*") as tar:
                base_dir = temp_path.resolve()
                safe_members = []
                for member in tar.getmembers():
                    # Reject absolute paths or relative traversal
                    if member.name.startswith("/") or member.name.startswith("\\") or ".." in member.name:
                        raise ValueError(f"Malicious tar entry detected: {member.name}")

                    # Resolve anticipated target path
                    member_path = (base_dir / member.name).resolve()
                    try:
                        member_path.relative_to(base_dir)
                    except ValueError:
                        raise ValueError(f"Path traversal detected in archive member: {member.name}")

                    # Defend against symlink and hardlink directory escape
                    if member.issym() or member.islnk():
                        link_target = (member_path.parent / member.linkname).resolve()
                        try:
                            link_target.relative_to(base_dir)
                        except ValueError:
                            raise ValueError(
                                f"Symlink traversal detected in archive member: {member.name} -> {member.linkname}"
                            )

                    safe_members.append(member)

                # Use data filter on Python 3.12+ if available, otherwise safe members list
                if hasattr(tarfile, "data_filter"):
                    tar.extractall(path=temp_path, filter="data")
                else:
                    tar.extractall(path=temp_path, members=safe_members)

            # GitHub tarballs unpack into a single root folder named {owner}-{repo}-{sha}
            extracted_subdirs = [p for p in temp_path.iterdir() if p.is_dir()]
            target_dir = extracted_subdirs[0] if extracted_subdirs else temp_path

            yield target_dir, "github_repository", commit_sha
    else:
        # Local filesystem path
        try:
            local_path = Path(target).expanduser().resolve(strict=True)
        except (FileNotFoundError, OSError):
            raise ValueError(f"Target '{target}' does not exist.")
        if not local_path.is_dir():
            raise ValueError(f"Target '{target}' is not a directory.")
        yield local_path, "local_directory", None
