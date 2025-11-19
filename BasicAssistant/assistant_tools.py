from langchain.tools import tool
from datetime import datetime
import ast
import requests
import subprocess
import operator

@tool
def get_time() -> str:
	"""Return current UTC time in ISO format."""
	try:
		return datetime.utcnow().isoformat() + "Z"
	except Exception as e:
		return f"Error getting time: {e}"

# Dictionary mapping AST node types to safe mathematical operations
# This creates a whitelist of allowed operations to prevent code injections
# Only basic math operations are permitted, no function calls or imports
_SAFE_OPS = {
		ast.Add: operator.add,              # Addition: +
		ast.Sub: operator.sub,              # Subtraction: -
		ast.Mult: operator.mul,             # Multiplication: *
		ast.Div: operator.truediv,          # Division: / (returns float, not integer division)
		ast.Pow: operator.pow,              # Exponentiation: **
		ast.Mod: operator.mod,              # Module: %
		ast.USub: operator.neg              # Unary minus : -x
}

def _eval_expr(node):
	"""
	Recursively evaluates AST nodes safely by only allowing whitelisted operations.
	This prevents arbitrary code execution while parsing mathematical expressions.
	:param node:
	:return:
	"""
	if isinstance(node, ast.Num):
		return node.n
	elif isinstance(node, ast.Constant):
		return node.value
	elif isinstance(node, ast.BinOp):
		# Recursively evaluate the left and right operands, then apply the operator
		return _SAFE_OPS[type(node.op)](_eval_expr(node.left), _eval_expr(node.right))
	elif isinstance(node, ast.UnaryOp):
		# Recursively evaluate the operand, then apply the unary operator
		return _SAFE_OPS[type(node.op)](_eval_expr(node.operand))
	else:
		# Reject any node type not explicitly allowed (variables, function calls, etc.)
		raise TypeError(node)

@tool
def calc(expressions: str) -> str:
	"""
	Safely evaluate a mathematical expression.
	Supports +, -, *, /, **, % and parentheses.
	Examples: '2+3*4', '(10-2)/4', '2**3'
	:param expressions:
	:return:
	"""
	try:
		expression = expressions.strip()
		if not expression:
			return "Error: Empty Expression"

		# PArse the expression into an Abstract Syntax Tree (AST)
		# model='eval' restricts to expressions only (no statements like assignments)
		tree = ast.parse(expression, mode='eval')
		# Safely evaluate the AST using our whitelisted operations
		result = _eval_expr(tree.body)

		# Format result
		if isinstance(result, float):
			if result.is_integer():
				return str(int(result))
			else:
				return f"{result:.10g}" # Remove trailing zeros
		return str(result)
	except (ValueError, TypeError, ZeroDivisionError, SyntaxError) as e:
		return f"Error: {str(e)}"
	except Exception as e:
		return f"Calculation error: {str(e)}"

@tool
def http_get(url: str) -> str:
	"""
	Make a GET request to the specified URL and return the response content
	:param url:
	:return:
	"""
	try:
		if not url.startswith(('http://', 'https://')):
			return "Error: URL must start with http:// or https://"

		response = requests.get(url, timeout=10)
		response.raise_for_status()

		# Limit response size
		content = response.text
		if len(content) > 2000:
			content = content[:2000] + "... (truncated)"

		return f"Status: {response.status_code}\nContent: {content}"
	except requests.exceptions.Timeout:
		return "Error: Request timed out"
	except requests.exceptions.RequestException as e:
		return f"Error: {str(e)}"
	except Exception as e:
		return f"HTTP error: {str(e)}"

@tool
def launch_app(app_name: str) -> str:
	"""
	Launch an application or open a file/URL cross-platform (Windows/Ubuntu).
	Examples: 'notepad', 'calc', 'firefox', 'https://youtube.com', 'gedit'
	:param app_name:
	:return:
	"""
	try:
		if not app_name.strip():
			return "Error: No application specified"

		import platform
		system = platform.system().lower()

		if system == 'windows':
			# Windows: user 'start' command
			result = subprocess.run(
					['cmd', '/c', 'start', '', app_name],
					capture_output=True,
					text=True,
					timeout=5
			)
		else:
			# Linux: user appropriate commands
			if app_name.startswith(('http://', 'http://')):
				# Open the url in default browser
				result = subprocess.run(
						['xdg-open', app_name],
						capture_output=True,
						text=True,
						timeout=5
				)
			else:
				# Launch application
				# Try direct command first, fallback xdg-open
				try:
					result = subprocess.run(
							[app_name],
							capture_output=True,
							text=True,
							timeout=5
					)
				except FileNotFoundError:
					# Fallback to xdg-open for applications
					result = subprocess.run(
							['xdg-open', app_name],
							capture_output=True,
							text=True,
							timeout=5
					)
		if result.returncode == 0:
			return f"Successfully launch {app_name} on {system.title()}"
		else:
			return f"Failed to launch {app_name}: {result.stderr}"

	except subprocess.TimeoutExpired:
		return f"Timeout launching {app_name}"
	except Exception as e:
		return f"Launch Error : {str(e)}"