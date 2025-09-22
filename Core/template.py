import re
from pathlib import Path

def template(template_file, output_file=None, **replacements):
	"""
	Replace {{key}} patterns in a file with provided values.
	"""
	if output_file is None:
		output_file = template_file
	
	# Read the template
	with open(template_file, 'r', encoding='utf-8') as f:
		content = f.read()
	
	# Replace all occurrences
	for key, value in replacements.items():
		pattern = r'\{\{\s*' + re.escape(key) + r'\s*\}\}'
		content = re.sub(pattern, str(value), content)
	
	# Write the result
	with open(output_file, 'w', encoding='utf-8') as f:
		f.write(content)