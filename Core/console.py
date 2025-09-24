import shutil
import random
import pyfiglet
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from Core import name, developer, version

class console:
	def __init__(self):
		self.console = Console()
	
	def status(self, message: str):
		self.console.print(f"[cyan][STATUS][/cyan] {message}")
	
	def error(self, message: str):
		self.console.print(f"[bold red][ERROR][/bold red] {message}")
	
	def warning(self, message: str):
		self.console.print(f"[yellow][WARNING][/yellow] {message}")
	
	def success(self, message: str):
		self.console.print(f"[green][SUCCESS][/green] {message}")
	
	def info(self, message: str):
		self.console.print(f"[blue][INFO][/blue] {message}")
	
	def debug(self, message: str):
		self.console.print(f"[magenta][DEBUG][/magenta] {message}")
	
	def header(self, title: str):
		self.console.print(Panel.fit(f"[bold]{title}[/bold]", border_style="green"))
	
	def divider(self):
		self.console.rule(style="white")
	
	def table(self, data: dict, title: str = ""):
		table = Table(title=title, box=box.ROUNDED)
		table.add_column("Key", style="cyan")
		table.add_column("Value", style="green")
		
		for key, value in data.items():
			table.add_row(str(key), str(value))
		
		self.console.print(table)
	
	def banner(self):
		width = shutil.get_terminal_size().columns
		fonts = pyfiglet.Figlet().getFonts()
		fig = pyfiglet.Figlet(font=random.choice(fonts), justify="center", width=width)
		logo = fig.renderText(name)
		print(logo)
		d = \
		f"Created by [bold green]{developer["name"]}[/bold green]\n"+\
		f"GitHub: {developer["github"]}\n"+\
		f"Version: [red]{version}[/red]"
		
		self.header(d)