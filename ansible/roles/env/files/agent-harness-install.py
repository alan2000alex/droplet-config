#!/usr/bin/env python3
"""
Agent Installation and Maintenance Script for Linux.

This script automates the setup and update of development tools and AI agent wrappers:
1. Node.js: Fetches the latest LTS or Current version and installs it to a specified directory.
2. uv: Fetches and installs the latest version of the astral-sh/uv package manager.
3. gh: Fetches and installs the latest version of the GitHub CLI.
4. tea: Fetches and installs the latest version of the Gitea CLI.
5. Agent Wrappers: Installs shell script wrappers for AI agents into a binary directory:
   - codex: Wrapper for @openai/codex (bypasses approvals/sandbox)
   - gemini: Wrapper for @google/gemini-cli (enables yolo mode)
   - claude: Wrapper for @anthropic-ai/claude-code (skips permissions check)

Usage:
    sudo python3 agent-install.py [options]

Options:
    --node-latest   Install latest Node.js release instead of the default LTS.
    --install-dir   Directory to install Node.js (default: /opt/node).
    --symlink-dir   Directory for binary symlinks and scripts (default: /usr/local/bin).
    --skip-node     Skip Node.js and agent script installation.
    --skip-uv       Skip uv installation.
    --skip-gh       Skip GitHub CLI installation.
    --skip-tea      Skip Gitea CLI installation.

Prerequisites:
    - Linux operating system.
    - Write access to the symlink and installation directories (usually requires sudo).
"""

import argparse
import json
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional, List, Dict, Any

# --- Configuration & Constants ---
NODE_INDEX_URL = "https://nodejs.org/dist/index.tab"
DEFAULT_INSTALL_DIR = Path("/opt/node")
SYMLINK_DIR = Path("/usr/local/bin")
UV_REPO = "astral-sh/uv"

CODEX_SCRIPT_CONTENT = """#!/bin/bash

exec npx -y @openai/codex@latest --dangerously-bypass-approvals-and-sandbox "$@"
"""

GEMINI_SCRIPT_CONTENT = """#!/bin/bash

exec npx -y @google/gemini-cli@latest --yolo "$@"
"""

CLAUDE_SCRIPT_CONTENT = """#!/bin/bash

exec npx -y @anthropic-ai/claude-code@latest --dangerously-skip-permissions "$@"
"""

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


class InstallationError(Exception):
    """Base class for installation errors."""
    pass


class SystemUtils:
    """System-level utility functions."""

    @staticmethod
    def get_arch_map() -> Dict[str, str]:
        return {
            "x86_64": "x64",
            "amd64": "x64",
            "aarch64": "arm64",
            "arm64": "arm64",
            "armv7l": "armv7l",
        }

    @classmethod
    def get_node_arch(cls) -> str:
        machine = platform.machine().lower()
        return cls.get_arch_map().get(machine, machine)

    @staticmethod
    def get_uv_arch() -> Optional[str]:
        machine = platform.machine().lower()
        if machine in ("x86_64", "amd64"):
            return "x86_64-unknown-linux-musl"
        elif machine in ("aarch64", "arm64"):
            return "aarch64-unknown-linux-musl"
        elif machine == "armv7l":
            return "armv7-unknown-linux-musleabihf"
        return None

    @staticmethod
    def check_permissions(path: Path) -> bool:
        """Check if the current user has write access to the path."""
        if os.getuid() == 0:
            return True
        return os.access(path, os.W_OK)


class Downloader:
    """Handles network requests and downloads."""

    @staticmethod
    def fetch_text(url: str) -> str:
        try:
            with urllib.request.urlopen(url) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            raise InstallationError(f"Failed to fetch data from {url}: {e}")

    @staticmethod
    def download_file(url: str, dest: Path):
        logger.info(f"Downloading {url}...")
        try:
            urllib.request.urlretrieve(url, str(dest))
        except Exception as e:
            raise InstallationError(f"Download failed for {url}: {e}")


class NodeManager:
    """Manages Node.js installation and updates."""

    def __init__(self, install_dir: Path, symlink_dir: Path):
        self.install_dir = install_dir
        self.symlink_dir = symlink_dir
        self.arch = SystemUtils.get_node_arch()

    def get_target_version(self, lts_only: bool = True) -> Optional[str]:
        lines = Downloader.fetch_text(NODE_INDEX_URL).splitlines()
        if not lines:
            return None

        header = lines[0].split('\t')
        try:
            lts_col = header.index('lts')
            ver_col = header.index('version')
        except ValueError:
            raise InstallationError("Unexpected Node.js index.tab format")

        for line in lines[1:]:
            parts = line.split('\t')
            if len(parts) <= max(lts_col, ver_col):
                continue
            version = parts[ver_col].strip()
            lts_val = parts[lts_col].strip().lower()
            is_lts = lts_val not in ('false', '', '-')
            if lts_only and not is_lts:
                continue
            return version
        return None

    def get_current_version(self) -> str:
        node_path = self.install_dir / "bin" / "node"
        if node_path.exists():
            try:
                return subprocess.check_output([str(node_path), "-v"], stderr=subprocess.DEVNULL).decode().strip()
            except (subprocess.CalledProcessError, OSError):
                return "none"
        return "none"

    def install(self, version: str):
        logger.info(f"Updating Node.js to {version}...")
        arch_str = f"linux-{self.arch}"
        ext = "tar.xz"
        url = f"https://nodejs.org/dist/{version}/node-{version}-{arch_str}.{ext}"

        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            archive_path = tmp_dir / f"node.{ext}"

            Downloader.download_file(url, archive_path)

            logger.info("Extracting Node.js archive...")
            try:
                with tarfile.open(archive_path, "r:xz") as tar:
                    extract_kwargs: Dict[str, Any] = {"path": tmp_dir}
                    if sys.version_info >= (3, 12):
                        extract_kwargs["filter"] = "data"
                    tar.extractall(**extract_kwargs)
            except Exception as e:
                raise InstallationError(f"Extraction failed: {e}")

            extracted_folder = tmp_dir / f"node-{version}-{arch_str}"
            self.install_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Syncing Node.js files to {self.install_dir}...")
            # Clean up existing installation
            for item in self.install_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

            # Copy new files
            for item in extracted_folder.iterdir():
                dest = self.install_dir / item.name
                if item.is_symlink():
                    dest.symlink_to(os.readlink(str(item)))
                elif item.is_dir():
                    shutil.copytree(item, dest, symlinks=True)
                else:
                    shutil.copy2(item, dest)

    def create_symlinks(self):
        for binary in ("node", "npm", "npx"):
            src = self.install_dir / "bin" / binary
            dst = self.symlink_dir / binary

            if not src.exists():
                logger.warning(f"Source binary not found: {src}")
                continue

            # Use relative path for symlink if possible
            try:
                rel_src = os.path.relpath(src, dst.parent)
            except ValueError:
                rel_src = str(src)

            if os.path.lexists(str(dst)):
                if dst.is_symlink() and os.readlink(str(dst)) == rel_src:
                    logger.info(f"Symlink OK: {dst} -> {rel_src}")
                    continue
                dst.unlink()

            try:
                dst.symlink_to(rel_src)
                logger.info(f"Symlink created: {dst} -> {rel_src}")
            except OSError as e:
                logger.error(f"Error creating symlink for {binary}: {e}")


class UVManager:
    """Manages uv installation and updates."""

    def __init__(self, symlink_dir: Path):
        self.symlink_dir = symlink_dir
        self.arch = SystemUtils.get_uv_arch()

    def get_latest_version(self) -> Optional[str]:
        api_url = f"https://api.github.com/repos/{UV_REPO}/releases/latest"
        try:
            req = urllib.request.Request(api_url)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                return data["tag_name"].lstrip('v')
        except Exception as e:
            logger.warning(f"GitHub API fetch failed for uv: {e}. Trying fallback.")
            try:
                with urllib.request.urlopen(f"https://github.com/{UV_REPO}/releases/latest") as resp:
                    return resp.geturl().split('/')[-1].lstrip('v')
            except Exception:
                return None

    def get_current_version(self) -> str:
        binary_path = self.symlink_dir / "uv"
        if not binary_path.exists():
            return "none"
        try:
            output = subprocess.check_output([str(binary_path), "--version"], stderr=subprocess.STDOUT).decode().strip()
            return output.split()[1]
        except (subprocess.CalledProcessError, OSError, IndexError):
            return "none"

    def install(self, version: str):
        if not self.arch:
            raise InstallationError(f"Unsupported architecture for uv: {platform.machine()}")

        logger.info(f"Updating uv to {version}...")
        # uv download URL can vary, but usually it matches the tag name.
        # If the version doesn't start with 'v', we might need to add it, 
        # but for recent uv releases the tag name itself is used in the URL.
        # Since get_latest_version lstrips 'v', and some releases use 'v' tags, 
        # we'll try to be smart about it.
        url = f"https://github.com/{UV_REPO}/releases/download/{version}/uv-{self.arch}.tar.gz"

        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            archive_path = tmp_dir / "uv.tar.gz"
            Downloader.download_file(url, archive_path)

            logger.info("Extracting uv archive...")
            try:
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(path=tmp_dir)
            except Exception as e:
                raise InstallationError(f"Extraction failed: {e}")

            extracted_dir = tmp_dir / f"uv-{self.arch}"
            if not extracted_dir.exists():
                # Fallback: search for uv binary
                for root, _, files in os.walk(tmp_dir):
                    if "uv" in files:
                        extracted_dir = Path(root)
                        break

            for binary in ("uv", "uvx"):
                src = extracted_dir / binary
                dst = self.symlink_dir / binary
                if src.exists():
                    logger.info(f"Installing {binary} to {self.symlink_dir}...")
                    if dst.exists():
                        dst.unlink()
                    shutil.copy2(src, dst)
                    dst.chmod(0o755)
                else:
                    logger.warning(f"Binary {binary} not found in archive.")


class GHManager:
    """Manages GitHub CLI installation and updates."""

    def __init__(self, symlink_dir: Path):
        self.symlink_dir = symlink_dir
        self.arch = SystemUtils.get_node_arch() # x64, arm64, etc.
        # Map to GH arch names
        self.gh_arch = {
            "x64": "amd64",
            "arm64": "arm64",
            "armv7l": "armv6",
        }.get(self.arch, self.arch)

    def get_latest_version(self) -> Optional[str]:
        api_url = "https://api.github.com/repos/cli/cli/releases/latest"
        try:
            req = urllib.request.Request(api_url)
            # GitHub API requires User-Agent
            req.add_header("User-Agent", "Mozilla/5.0")
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                return data["tag_name"].lstrip('v')
        except Exception as e:
            logger.warning(f"GitHub API fetch failed for gh: {e}")
            return None

    def get_current_version(self) -> str:
        binary_path = self.symlink_dir / "gh"
        if not binary_path.exists():
            return "none"
        try:
            output = subprocess.check_output([str(binary_path), "--version"], stderr=subprocess.STDOUT).decode().strip()
            # gh version 2.47.0 (2024-04-03)
            # Find first word that starts with digit and has a dot
            match = re.search(r"version\s+v?(\d+\.\d+\.\d+)", output, re.IGNORECASE)
            if match:
                return match.group(1)
            return "none"
        except (subprocess.CalledProcessError, OSError):
            return "none"

    def install(self, version: str):
        logger.info(f"Updating gh to {version}...")
        url = f"https://github.com/cli/cli/releases/download/v{version}/gh_{version}_linux_{self.gh_arch}.tar.gz"

        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            archive_path = tmp_dir / "gh.tar.gz"
            Downloader.download_file(url, archive_path)

            logger.info("Extracting gh archive...")
            try:
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(path=tmp_dir)
            except Exception as e:
                raise InstallationError(f"Extraction failed: {e}")

            # gh extracts to gh_{version}_linux_{gh_arch}/bin/gh
            extracted_dir = tmp_dir / f"gh_{version}_linux_{self.gh_arch}"
            src = extracted_dir / "bin" / "gh"
            if not src.exists():
                # Fallback: find gh binary
                for root, _, files in os.walk(tmp_dir):
                    if "gh" in files and "bin" in root:
                        src = Path(root) / "gh"
                        break

            dst = self.symlink_dir / "gh"
            if src.exists():
                logger.info(f"Installing gh to {self.symlink_dir}...")
                if dst.exists():
                    dst.unlink()
                shutil.copy2(src, dst)
                dst.chmod(0o755)
            else:
                raise InstallationError("gh binary not found in archive.")


class TeaManager:
    """Manages Gitea CLI (tea) installation and updates."""

    def __init__(self, symlink_dir: Path):
        self.symlink_dir = symlink_dir
        self.arch = SystemUtils.get_node_arch()
        # Map to tea arch names
        self.tea_arch = {
            "x64": "amd64",
            "arm64": "arm64",
            "armv7l": "arm-7",
        }.get(self.arch, self.arch)

    def get_latest_version(self) -> Optional[str]:
        api_url = "https://gitea.com/api/v1/repos/gitea/tea/releases/latest"
        try:
            with urllib.request.urlopen(api_url) as response:
                data = json.loads(response.read().decode())
                return data["tag_name"].lstrip('v')
        except Exception as e:
            logger.warning(f"Gitea API fetch failed for tea: {e}")
            return None

    def get_current_version(self) -> str:
        binary_path = self.symlink_dir / "tea"
        if not binary_path.exists():
            return "none"
        try:
            # Version: 0.14.0 golang: 1.26.2  go-sdk: v0.24.1
            output = subprocess.check_output([str(binary_path), "--version"], stderr=subprocess.STDOUT).decode().strip()
            # The output may contain ANSI color codes (e.g., ^[[1m0.14.0^[[0m)
            # and may be separated by tabs or spaces.
            parts = output.split()
            if len(parts) > 1 and "version" in parts[0].lower():
                # Pick the second part (the version) and strip anything that's not a digit or dot
                match = re.search(r"(\d+\.\d+\.\d+)", parts[1])
                if match:
                    return match.group(1)
            return "none"
        except (subprocess.CalledProcessError, OSError):
            return "none"

    def install(self, version: str):
        logger.info(f"Updating tea to {version}...")
        # tea-0.14.0-linux-amd64
        url = f"https://gitea.com/gitea/tea/releases/download/v{version}/tea-{version}-linux-{self.tea_arch}"

        dst = self.symlink_dir / "tea"
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            try:
                Downloader.download_file(url, tmp_path)
                logger.info(f"Installing tea to {self.symlink_dir}...")
                if dst.exists():
                    dst.unlink()
                shutil.copy2(tmp_path, dst)
                dst.chmod(0o755)
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()


class ScriptManager:
    """Manages shell script installation."""

    def __init__(self, name: str, content: str, symlink_dir: Path):
        self.name = name
        self.content = content
        self.dest_path = symlink_dir / name

    def install(self):
        logger.info(f"Checking {self.name} script at {self.dest_path}...")
        
        needs_write = True
        if self.dest_path.exists():
            try:
                current_content = self.dest_path.read_text()
                if current_content == self.content:
                    logger.info(f"{self.name} script is already up to date.")
                    needs_write = False
                else:
                    logger.info(f"{self.name} script is different. Overwriting...")
            except Exception as e:
                logger.warning(f"Failed to read existing {self.name} script: {e}. Overwriting...")

        if needs_write:
            logger.info(f"Writing {self.name} script to {self.dest_path}...")
            try:
                self.dest_path.write_text(self.content)
                self.dest_path.chmod(0o755)
                logger.info(f"{self.name} script installed successfully.")
            except Exception as e:
                raise InstallationError(f"Failed to install {self.name} script: {e}")


def main():
    if platform.system().lower() != "linux":
        logger.error("This script is only supported on Linux.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Install or update Node.js and uv on Linux")
    parser.add_argument("--node-latest", action="store_true", help="Install latest Node.js release")
    parser.add_argument("--node-lts", action="store_true", default=True, help="Install latest Node.js LTS (default)")
    parser.add_argument("--install-dir", type=Path, default=DEFAULT_INSTALL_DIR, help="Node.js install directory")
    parser.add_argument("--symlink-dir", type=Path, default=SYMLINK_DIR, help="Binary symlink directory")
    parser.add_argument("--skip-node", action="store_true", help="Skip Node.js installation")
    parser.add_argument("--skip-uv", action="store_true", help="Skip uv installation")
    parser.add_argument("--skip-gh", action="store_true", help="Skip GitHub CLI installation")
    parser.add_argument("--skip-tea", action="store_true", help="Skip Gitea CLI installation")
    args = parser.parse_args()

    # Permission check
    if not SystemUtils.check_permissions(args.symlink_dir):
        logger.error(f"Need 'sudo' or write access to {args.symlink_dir}")
        sys.exit(1)

    try:
        # 1. Node.js
        if not args.skip_node:
            node = NodeManager(args.install_dir, args.symlink_dir)
            target_node = node.get_target_version(lts_only=not args.node_latest)
            current_node = node.get_current_version()

            logger.info(f"Node.js - Current: {current_node}, Target: {target_node}")
            if target_node and current_node != target_node:
                node.install(target_node)
                node.create_symlinks()
            else:
                logger.info("Node.js is already up to date.")
                node.create_symlinks()
            
            # 1.5 Shell scripts
            ScriptManager("codex", CODEX_SCRIPT_CONTENT, args.symlink_dir).install()
            ScriptManager("gemini", GEMINI_SCRIPT_CONTENT, args.symlink_dir).install()
            ScriptManager("claude", CLAUDE_SCRIPT_CONTENT, args.symlink_dir).install()

        # 2. uv
        if not args.skip_uv:
            uv = UVManager(args.symlink_dir)
            target_uv = uv.get_latest_version()
            current_uv = uv.get_current_version()

            logger.info(f"uv - Current: {current_uv}, Target: {target_uv}")
            if target_uv and current_uv != target_uv:
                uv.install(target_uv)
            else:
                logger.info("uv is already up to date.")

        # 3. gh
        if not args.skip_gh:
            gh = GHManager(args.symlink_dir)
            target_gh = gh.get_latest_version()
            current_gh = gh.get_current_version()

            logger.info(f"gh - Current: {current_gh}, Target: {target_gh}")
            if target_gh and current_gh != target_gh:
                gh.install(target_gh)
            else:
                logger.info("gh is already up to date.")

        # 4. tea
        if not args.skip_tea:
            tea = TeaManager(args.symlink_dir)
            target_tea = tea.get_latest_version()
            current_tea = tea.get_current_version()

            logger.info(f"tea - Current: {current_tea}, Target: {target_tea}")
            if target_tea and current_tea != target_tea:
                tea.install(target_tea)
            else:
                logger.info("tea is already up to date.")

        logger.info("Installation/Update process complete.")

    except InstallationError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
