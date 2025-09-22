#!/usr/bin/env python -u
#coding: utf-8

import platform
import sys
import yaml
import os
import io
import hashlib
import shutil
from rich import print_json
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
			exit(1)
		
		if not os.path.isdir(path):
			self.console.error(f"Storage path is not a directory: {path}")
			exit(1)
		
		if not os.access(path, os.R_OK | os.W_OK):
			self.console.error(f"Insufficient permissions for storage path: {path}")
			exit(1)
		
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
		metadata_url = f"http://dl-cdn.alpinelinux.org/alpine/latest-stable/releases/{self.architecture()}/latest-releases.yaml"
		metadata_raw = self.request.get(metadata_url).text
		metadata = yaml.safe_load(metadata_raw)
		mini_metadata = metadata[2]
		self.console.table(mini_metadata)
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
		self.downloader.download_multiple(assets[self.architecture()].values(), \
		[os.path.join(self.resources, self.proot), os.path.join(self.resources, self.talloc)])
	
	def setup_sandbox(self):
		self.console.info("Sandbox setup process has been started.")
		cmd = lambda c: self.rish.run(f"-c \"{c}\"")
		
		r = cmd("which tar")
		if not r.returncode == 0:
			self.console.error("[blue]Tar[/blue] isn't available in your system.")
			exit(1)
		
		main_proot = os.path.join(self.root, name)
		#print(main_proot)
		r = cmd(f"mkdir -p {main_proot}")
		if not r.returncode == 0:
			self.console.error(r.stderr)
		for file in [self.proot, self.talloc]:
			file_path = os.path.join(self.resources, file)
			r = cmd(f"cp {file_path} {main_proot}")
			if not r.returncode == 0:
				self.console.error(r.stderr)
		
		file_path = os.path.join(main_proot, self.proot)
		r = cmd(f"chmod +x {file_path}")
		if not r.returncode == 0:
			self.console.error(r.stderr)
		
		alpine = os.path.join(self.resources, self.alpine_file)
		alpine_dir = os.path.join(main_proot, self.alpine_dir)
		r = cmd(f"mkdir -p {alpine_dir}")
		if not r.returncode == 0:
			self.console.error(r.stderr)
		r = cmd(f"tar -xf {alpine} -C {alpine_dir}")
		if not r.returncode == 0:
			self.console.error(r.stderr)
		self.console.success("The process has been finished successfully.")

	def launch(self):
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
			name = name,
			distro = self.alpine_dir
		)
		self.db.setup()
	
	def __init__(self):
		self.console = console()
		self.request = create_session()
		self.downloader = FileDownloader()
		self.rish = Rish()
		self.root = "/data/local/tmp"
		self.resources = f"/sdcard/Download/{name}"
		self.assets_path = "Assets"
		self.alpine_file = "alpine.tar.gz"
		self.alpine_dir = "Alpine"
		self.proot = "proot"
		self.talloc = "libtalloc.so.2"
		self.sandbox_script = "proot.sh"
		self.console.banner()
		self.db = DB()
		if self.db.check():
			self.launch()
		else:
			self.setup()


if __name__ == '__main__':
	main = AndroSH()