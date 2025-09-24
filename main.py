#!/usr/bin/env python -u
#coding: utf-8

import platform
import sys
import yaml
import os
import io
import hashlib
import shutil
import argparse
import time
from rich import print_json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from Core.console import console
from Core.request import create_session
from Core.downloader import FileDownloader
from Core.errors_handler import AndroSH_err
from Core.template import template
from Core.shizuku import Rish
from Core.db import DB
from Core import name

class AndroSH(object):

	def architecture(self) -> str:
		a64 = "aarch64"
		a32 = "armhf"
		x86 = "x86"
		x64 = "x86_64"
		architectures = {
			"arm64-v8a": a64,
			a64: a64,
			"armeabi": a32,
			"armeabi-v7a": a32,
			a32: a32,
			x86: x86,
			x64: x64
		}
		arch = architectures.get(platform.machine())
		if arch is None:
			message = "Unknown architecture."
			self.console.error(message)
			raise AndroSH_err(message)
		return arch
	
	def check_storage(self, path: str = "/sdcard/Download"):
		"""Check if storage path exists and is accessible"""
		if not os.path.exists(path):
			self.console.error(f"Storage path does not exist: {path}")
			sys.exit(1)
		
		if not os.path.isdir(path):
			self.console.error(f"Storage path is not a directory: {path}")
			sys.exit(1)
		
		if not os.access(path, os.R_OK | os.W_OK):
			self.console.error(f"Insufficient permissions for storage path: {path}")
			sys.exit(1)
		
		self.console.info(f"Storage path verified: {path}")
	
	def checksum(self, file: str, hash: str, hashType: str = "sha512") -> bool:
		x = hashlib.new(hashType)
		with io.open(file, mode = "rb") as f:
			content = f.read()
			f.close()
		x.update(content)
		del content
		result = x.hexdigest() == hash
		result or self.console.status("The file is corrupt")
		return result
	
	def alpine_downloader(self, file: str = "alpine.tar.gz"):
		self.check_storage()
		fie_dir = os.path.join(self.resources, file)
		if os.path.exists(fie_dir):
			self.console.info("Alpine downloaded")
			return
		metadata_url = f"http://dl-cdn.alpinelinux.org/alpine/latest-stable/releases/{self.architecture()}/latest-releases.yaml"
		metadata_raw = self.request.get(metadata_url).text
		metadata = yaml.safe_load(metadata_raw)
		mini_metadata = metadata[2]
		self.console.table(mini_metadata, "Alpine metadata")
		version = mini_metadata.get("version")
		if version is None:
			message = "The version hasn't been detected."
			self.console.error(message)
			raise AndroSH_err(message)
		url = f"http://dl-cdn.alpinelinux.org/alpine/latest-stable/releases/{self.architecture()}/alpine-minirootfs-{version}-{self.architecture()}.tar.gz"
		self.console.info(f"Alpine version: {version}")
		self.downloader.download_file(url, fie_dir)
		self.checksum(fie_dir, mini_metadata["sha512"]) or self.alpine_downloader(file)
	
	def assets(self):
		proot = os.path.join(self.resources, self.proot)
		talloc = os.path.join(self.resources, self.talloc)
		assets = {
			"armhf": {
				"proot": "https://raw.githubusercontent.com/Xed-Editor/Karbon-PackagesX/main/arm/proot",
				"talloc": "https://raw.githubusercontent.com/Xed-Editor/Karbon-PackagesX/main/arm/libtalloc.so.2"
			},
			"aarch64": {
				"proot": "https://raw.githubusercontent.com/Xed-Editor/Karbon-PackagesX/main/aarch64/proot",
				"talloc": "https://raw.githubusercontent.com/Xed-Editor/Karbon-PackagesX/main/aarch64/libtalloc.so.2"
			},
			"x86": {
				"proot": "https://raw.githubusercontent.com/Xed-Editor/Karbon-PackagesX/main/x86/proot",
				"talloc": "https://raw.githubusercontent.com/Xed-Editor/Karbon-PackagesX/main/x86/libtalloc.so.2"
			},
			"x86_64": {
				"proot": "https://raw.githubusercontent.com/Xed-Editor/Karbon-PackagesX/main/x86_64/proot",
				"talloc": "https://raw.githubusercontent.com/Xed-Editor/Karbon-PackagesX/main/x86_64/libtalloc.so.2"
			}
		}
		r = [d for d in [proot, talloc] if not os.path.exists(d)]
		if any(r):
			self.downloader.download_multiple(assets[self.architecture()].values(), \
			r)
		else:
			self.console.info("You have proot already downloaded.")
	
	def setup_sandbox(self):
		self.console.info("Sandbox setup process has been started.")

		r = self.cmd("which tar > /dev/null 2>&1 || echo -n error")
		if r.stdout == "error":
			self.console.error("[blue]Tar[/blue] isn't available in your system.")
			sys.exit(1)
		
		main_proot = self.distro_dir #os.path.join(self.root, name)
		#print(main_proot)
		r = self.cmd(f"mkdir -p {main_proot}")
		if r.stderr:
			self.console.error(r.stderr)
			sys.exit(1)
		
		for file in [self.proot, self.talloc]:
			file_path = os.path.join(self.resources, file)
			r = self.cmd(f"cp {file_path} {main_proot}")
			if r.stderr:
				self.console.error(r.stderr)
				sys.exit(1)
		
		file_path = os.path.join(main_proot, self.proot)
		r = self.cmd(f"chmod +x {file_path}")
		if r.stderr:
			self.console.error(r.stderr)
			sys.exit(1)
		
		patched = os.path.join(main_proot, "patched")
		self.cmd(f"rm -rf {patched}")
		
		alpine = os.path.join(self.resources, self.alpine_file)
		alpine_dir = os.path.join(main_proot, self.alpine_dir)
		r = self.cmd(f"mkdir -p {alpine_dir}")
		if r.stderr:
			self.console.error(r.stderr)
			sys.exit(1)
		
		r = self.cmd(f"tar -xf {alpine} -C {alpine_dir}")
		if r.stderr:
			self.console.error(r.stderr)
			sys.exit(1)
		
		self.console.success("The process has been finished successfully.")

	def launch(self):
		self.console.divider()
		if not self.db.exists(self.distro_dir):
			self.console.warning(f"Distro '{self.alpine_dir}' does not exist in ({self.distro_dir}). Please setup first.")
			sys.exit()
		self.console.info("Starting up the sandbox:")
		template(
			os.path.join(self.assets_path, self.sandbox_script),
			os.path.join(self.resources, self.sandbox_script),
			dir = self.distro_dir,
			distro = self.alpine_dir
		)
		sandbox = os.path.join(self.resources, self.sandbox_script)
		self.rish.drun(sandbox)
	
	def setup(self):
		self.console.divider()
		self.console.info("The setup process has been started...")
		self.console.info("Downloading the distro and the needed resources:")
		self.alpine_downloader()
		self.assets()
		self.console.divider()
		self.setup_sandbox()
		template(
			os.path.join(self.assets_path, self.sandbox_script),
			os.path.join(self.resources, self.sandbox_script),
			dir = self.distro_dir,
			distro = self.alpine_dir
		)
		self.db.update({
			self.distro_dir:{
				"name": self.dir_name,
				"distro": self.alpine_dir,
				"base_dir": self.base_dir,
				"date": time.strftime("%Y/%m/%d")
			}
		})
		self.db.setup(name = self.distro_dir)
	
	def argparse(self):
		parser = argparse.ArgumentParser(
			description="AndroSH - Deploy Alpine Linux userland on Android using proot and Shizuku",
			epilog="Ideal for developers, security researchers, and power users wanting isolated Linux environments on Android"
		)
		
		# Main commands
		subparsers = parser.add_subparsers(dest='command', help='Command to execute', required=False)
		
		# Setup command
		setup_parser = subparsers.add_parser('setup', help='Setup a new Alpine Linux environment')
		setup_parser.add_argument('--name', default=name, 
								help=f'Name of the directory/distro (default: {name})')
		setup_parser.add_argument('--resetup', action='store_true',
								help='Resetup without losing data and fix issues')
		
		# Remove command
		remove_parser = subparsers.add_parser('remove', help='Remove an existing distro')
		remove_parser.add_argument('name', help='Name of the distro to remove')
		remove_parser.add_argument('--force', action='store_true',
								help='Force removal without confirmation')
		
		# Launch command
		launch_parser = subparsers.add_parser('launch', help='Launch an existing distro')
		launch_parser.add_argument('name', help='Name of the distro to launch')

		# Clean command
		clean_parser = subparsers.add_parser('clean', help='Clean distro temporary files')
		clean_parser.add_argument('name', 
								help='Clean specific distro')

		# Install command
		path = os.path.join(os.environ["PREFIX"], "bin") if os.environ.get("PREFIX") else None
		install_parser = subparsers.add_parser('install', help='Install shell script for global access')
		install_parser.add_argument('--path', default=path,
								help=f'Installation path for the script (default: {path})')
		install_parser.add_argument('--name', default='androsh',
								help='Command name for global access (default: androsh)')
		
		# List command
		list_parser = subparsers.add_parser('list', help='List all available distros')
		
		# Global arguments
		parser.add_argument('--base-dir', default=self.root,
						help=f'Base directory for the distro (default: {self.root})')
		parser.add_argument('--verbose', '-v', action='store_true',
						help='Verbose output')
		parser.add_argument('--quiet', '-q', action='store_true',
						help='Suppress non-essential output')
		
		args = parser.parse_args()
		
		self.console.banner()
		
		# Execute the appropriate function based on command
		if args.command == 'setup':
			self.setup_distro(args)
		elif args.command == 'remove':
			self.remove_distro(args)
		elif args.command == 'launch':
			self.launch_distro(args)
		elif args.command == 'clean':
			self.clean_distro(args)
		elif args.command == 'install':
			self.install_script(args)
		elif args.command == 'list':
			self.list_distros(args)
		return parser
	
	def setup_distro(self, args):
		"""Setup a new Alpine Linux environment"""
		self.distro_dir = os.path.expanduser(os.path.join(args.base_dir, args.name))
		self.base_dir = args.base_dir
		self.dir_name = args.name
		self.is_setup = True
		
		if args.verbose:
			self.console.status(f"Setting up distro {repr(self.alpine_dir)} in {self.distro_dir}")
			
		if self.db.exists(self.distro_dir) and not args.resetup:
			self.console.warning(f"Distro '{self.distro_dir}' already exists. Use --resetup to reinstall.")
			sys.exit()
		
		# Implementation for setting up Alpine with proot
		self.console.info(f"Setting up Alpine Linux environment: {self.distro_dir}")
	
	def remove_distro(self, args):
		"""Remove an existing distro"""
		distro_dir = os.path.expanduser(os.path.join(args.base_dir, args.name))
		
		if not self.db.exists(distro_dir):
			self.console.error(f"Distro '{distro_dir}' does not exist.")
			sys.exit(1)
		
		if not args.force:
			confirm = input(f"[?] Are you sure you want to remove '{distro_dir}'? [y/N]: ")
			if confirm.lower() != 'y':
				self.console.warning("Removal cancelled.")
				sys.exit()
		
		# Implementation for removal
		self.console.info(f"Removing distro: {distro_dir}")
		self.cmd(f"rm -rf {repr(distro_dir)}")
		self.db.remove(distro_dir)
		self.console.success("Successfully removed.")
		sys.exit()
	
	def launch_distro(self, args):
		"""Launch an existing distro"""
		self.distro_dir = os.path.expanduser(os.path.join(args.base_dir, args.name))
		
		if not self.db.exists(self.distro_dir):
			self.console.warning(f"Distro '{self.alpine_dir}' does not exist in ({self.distro_dir}). Please setup first.")
			sys.exit()
		self.db.setup(name = self.distro_dir)

	def clean_distro(self, args):
		"""Clean temporary files"""
		# Clean specific distro
		distro_dir = os.path.expanduser(os.path.join(args.base_dir, args.name))
		if self.db.exists(distro_dir):
			self.console.info(f"Cleaning distro: {distro_dir}")
			self.cmd(f"rm -rf {os.path.join(distro_dir, "tmp", "*")}")
			self.console.success("Successfully cleaned.")
		else:
			self.console.error(f"Distro '{distro_dir}' does not exist.")
		sys.exit()

	def install_script(self, args):
		"""Install shell script for global access"""
		script_path = os.path.join(args.path, args.name)
		wrapper_script_path = os.path.join(self.assets_path, self.wrapper_script)
		absolute_path = os.path.realpath(__file__)
		path = os.path.dirname(absolute_path)
		main = os.path.basename(absolute_path)
		self.console.status(f"Installing global script to: {script_path}")
		template(
			wrapper_script_path,
			script_path,
			AndroSH = path,
			main = main
		)
		os.chmod(script_path, 0o700)
		
		# Implementation for script installation
		self.console.success(f"Command '[bold green]{args.name}[/bold green]' will be available globally")
		sys.exit()
	
	def list_distros(self, args):
		"""List all available distros"""
		distros = self.db.fetchall()
		table = Table(title="Distros", box=box.ASCII)
		table.add_column("Distro path", style="blue")
		table.add_column("Info", style="green")
		console = Console()

		for key, value in distros.items():
			if key == "done":
				continue
			
			table.add_row(key, "\n".join([f"[white]{k}[/white][red]:[/red] [green]{v}[/green]" for k,v in value.items()]))
		
		console.print(table)
		sys.exit(0)

	
	def __init__(self):
		self.db = DB()
		self.console = console()
		self.request = create_session()
		self.downloader = FileDownloader()
		self.rish = Rish()
		self.root = "/data/local/tmp"
		self.resources = f"/sdcard/Download/{name}"
		self.assets_path = "Assets"
		self.wrapper_script = "AndroSH_wrapper.sh"
		self.alpine_file = "alpine.tar.gz"
		self.alpine_dir = "Alpine"
		self.proot = "proot"
		self.talloc = "libtalloc.so.2"
		self.sandbox_script = "proot.sh"
		self.is_setup = False
		self.force_download = False
		self.distro_dir = None
		self.cmd = lambda c: self.rish.run(f"-c {repr(c)}")
		parser = self.argparse()
		
		self.distro_dir = self.distro_dir if self.distro_dir else self.db.check()
		if self.distro_dir and not self.is_setup:
			self.launch()
		elif self.is_setup:
			self.db.setup(done = False)
			self.setup()
		else:
			parser.print_help()
			sys.exit()


if __name__ == '__main__':
	main = AndroSH()