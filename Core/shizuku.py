import subprocess
import shlex
import shutil
import stat
import tempfile
import os


class Rish:
	
	def dex(self, dex_name: str = "rish_shizuku.dex") -> str:
		dex_path = os.path.join(tempfile.gettempdir(), dex_name)
		if not os.path.exists(dex_path):
			shutil.copy(
				os.path.join(self.assets_path, dex_name),
				dex_path
			)
		
		if os.access(dex_path, os.W_OK):
			os.chmod(dex_path, stat.S_IREAD)
		
		return dex_path
	
	def rish(self, command: list):
		env = os.environ.copy()
		env['RISH_APPLICATION_ID'] = self.app_id

		result = subprocess.run(
			[
				"/system/bin/app_process",
				f"-Djava.class.path={self.dex()}",
				"/system/bin",
				"--nice-name=rish",
				"rikka.shizuku.shell.ShizukuShellLoader"
			] + command,
			capture_output=True,
			text=True,
			env=env
		)
		return result
	
	def run(self, command_string):
		args = shlex.split(command_string)
		result = self.rish(args)
		return result
	
	def drun(self, command_string):
		os.environ["RISH_APPLICATION_ID"] = self.app_id
		status = os.system(f"/system/bin/app_process -Djava.class.path=\"{self.dex()}\" /system/bin --nice-name=rish rikka.shizuku.shell.ShizukuShellLoader {command_string}")
		if not status == 0:
			exit(1)
	
	def __init__(self, app_id: str = "com.termux"):
		self.assets_path = "Assets"
		self.app_id = app_id