#!/usr/bin/env python3

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

NODE_INDEX_URL = "https://nodejs.org/dist/index.tab"
DEFAULT_INSTALL_DIR = Path("/opt/node")
SYMLINK_DIR = Path("/usr/local/bin")

OPENSPEC_SCRIPT_CONTENT = """#!/bin/bash

exec npx -y @fission-ai/openspec@latest "$@"
"""

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
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
                return response.read().decode("utf-8")
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

        header = lines[0].split("\t")
        try:
            lts_col = header.index("lts")
            ver_col = header.index("version")
        except ValueError:
            raise InstallationError("Unexpected Node.js index.tab format")

        for line in lines[1:]:
            parts = line.split("\t")
            if len(parts) <= max(lts_col, ver_col):
                continue
            version = parts[ver_col].strip()
            lts_val = parts[lts_col].strip().lower()
            is_lts = lts_val not in ("false", "", "-")
            if lts_only and not is_lts:
                continue
            return version
        return None

    def get_current_version(self) -> str:
        node_path = self.install_dir / "bin" / "node"
        if node_path.exists():
            try:
                return (
                    subprocess.check_output(
                        [str(node_path), "-v"], stderr=subprocess.DEVNULL
                    )
                    .decode()
                    .strip()
                )
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


class ScriptManager:
    """Manages script installations."""

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
                logger.warning(
                    f"Failed to read existing {self.name} script: {e}. Overwriting..."
                )

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

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--node-latest", action="store_true", help="Install latest Node.js release"
    )
    parser.add_argument(
        "--node-lts",
        action="store_true",
        default=True,
        help="Install latest Node.js LTS (default)",
    )
    parser.add_argument(
        "--skip-node", action="store_true", help="Skip Node.js installation"
    )
    parser.add_argument("--install-dir", type=Path, default=DEFAULT_INSTALL_DIR)
    parser.add_argument(
        "--symlink-dir", type=Path, default=SYMLINK_DIR, help="Binary symlink dir"
    )
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
            ScriptManager(
                "openspec", OPENSPEC_SCRIPT_CONTENT, args.symlink_dir
            ).install()

    except InstallationError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
