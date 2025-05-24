import contextlib
import io
from ast import parse, Expr, Expression
from typing import cast, Any, Dict

import pandas as pd
import plotly.graph_objects as go


def prepare_restricted_globals():
    """
    Prepare a restricted global environment with limited built-in functions and libraries.
    """
    safe_builtins = {
        'print': print,
        '__import__': __import__,
        'abs': abs,
        'all': all,
        'any': any,
        'ascii': ascii,
        'bin': bin,
        'bool': bool,
        'bytearray': bytearray,
        'bytes': bytes,
        'callable': callable,
        'chr': chr,
        'classmethod': classmethod,
        'complex': complex,
        'dict': dict,
        'divmod': divmod,
        'enumerate': enumerate,
        'filter': filter,
        'float': float,
        'format': format,
        'frozenset': frozenset,
        'getattr': getattr,
        'hasattr': hasattr,
        'hash': hash,
        'hex': hex,
        'id': id,
        'int': int,
        'isinstance': isinstance,
        'issubclass': issubclass,
        'iter': iter,
        'len': len,
        'list': list,
        'map': map,
        'max': max,
        'min': min,
        'next': next,
        'object': object,
        'oct': oct,
        'ord': ord,
        'pow': pow,
        'range': range,
        'repr': repr,
        'reversed': reversed,
        'round': round,
        'set': set,
        'slice': slice,
        'sorted': sorted,
        'str': str,
        'sum': sum,
        'tuple': tuple,
        'type': type,
        'zip': zip,
    }

    return {
        "__builtins__": safe_builtins,
        "__name__": "__main__",
        "pd": pd,
        "go": go,
    }


def modify_code_for_result(code_str):
    """
    Modify the input code to capture the result of the last expression in _result variable.
    """
    code_lines = code_str.strip().splitlines()
    if not code_lines:
        return code_str + "\n_result = None"

    tree = parse(code_str, mode='exec')
    modified_code = code_str.strip() + "\n"

    if tree.body and isinstance(tree.body[-1], (Expr, Expression)):
        last_line = code_lines[-1]
        modified_code += f"\n_result = ({last_line})"
    else:
        modified_code += "\n_result = None"

    return modified_code


def run_code_in_sandbox(modified_code, restricted_globals, local_vars):
    """
    Execute the given code in a sandboxed environment and capture stdout/stderr.
    """
    stdout = io.StringIO()
    stderr = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec(modified_code, restricted_globals, local_vars)
    except Exception as e:
        raise RuntimeError(f"Execution error: {e}") from e

    return stdout.getvalue(), stderr.getvalue()


def process_output(stdout, stderr):
    """
    Process standard output and error output into a list of console messages.
    """
    console_output = stdout.strip().splitlines() if stdout.strip() else []
    error_output = stderr.strip()
    console = console_output[:]
    if error_output:
        console.append(f"Error: {error_output}")
    return console, error_output


def format_result(result):
    """
    Format the execution result into a unified structure for response.
    """
    unified_content = {
        "textData": None,
        "dataframeData": None,
        "plotlyData": None
    }
    unified_type = None

    if isinstance(result, pd.DataFrame):
        unified_type = "dataframe"
        unified_content["dataframeData"] = {
            "type": "dataframe",
            "content": result.to_html(index=False)
        }

    elif isinstance(result, dict):
        result_type = result.get("type")

        if result_type == "dataframe":
            unified_type = "dataframe"
            unified_content["dataframeData"] = {
                "type": "dataframe",
                "content": result.get("content")
            }

        elif result_type == "plotly" and isinstance(result.get("content"), dict):
            unified_type = "plotly"
            content_dict = cast(Dict[str, Any], result.get("content"))
            unified_content["plotlyData"] = {
                "type": "plotly",
                "content": content_dict
            }

        elif "data" in result and "layout" in result:
            unified_type = "plotly"
            unified_content["plotlyData"] = {
                "type": "plotly",
                "content": result
            }

        elif result_type == "text":
            unified_type = "text"
            unified_content["textData"] = {
                "type": "text",
                "content": result.get("content")
            }

        else:
            unified_type = "text"
            unified_content["textData"] = {
                "type": "text",
                "content": result
            }

    elif result is not None:
        unified_type = "text"
        unified_content["textData"] = {
            "type": "text",
            "content": result
        }

    return unified_type, unified_content


def execute_code(code_str):
    """
    Main function to execute user-provided Python code in a secure sandbox.
    Returns structured output including console logs, errors, and results.
    """
    result_data = {
        "console": [],
        "error": None,
        "result": {
            "type": None,
            "content": {
                "textData": None,
                "dataframeData": None,
                "plotlyData": None
            }
        }
    }

    try:
        restricted_globals = prepare_restricted_globals()
        local_vars = {}

        modified_code = modify_code_for_result(code_str)
        stdout, stderr = run_code_in_sandbox(modified_code, restricted_globals, local_vars)

        console, error_output = process_output(stdout, stderr)
        result_data["console"] = console

        result = local_vars.get('_result', None)
        unified_type, unified_content = format_result(result)

        result_data["result"]["type"] = unified_type
        result_data["result"]["content"] = unified_content

    except Exception as e:
        result_data["error"] = str(e)
        result_data["console"].append(f"Error: {str(e)}")

    return result_data


"""
import pandas as pd

df = pd.DataFrame({
    '姓名': ['张三', '李四', '王五'],
    '分数': [85, 90, 78]
})

{'type': 'dataframe', 'content': df.to_html(index=False)}

-----------------------
import plotly.graph_objects as go

fig = go.Figure(data=[go.Bar(x=['A', 'B', 'C'], y=[10, 20, 15])])
{'type': 'plotly', 'content': fig.to_dict()}

-----------------------
{'type': 'text', 'content': '这是一个纯文本输出'}

-----------------------
import pandas as pd

def get_equity_broker_quotes() -> pd.DataFrame:

    quotes = [
        {"symbol": "eurusd", "bid": 1.1, "ask": 1.09, "tenor": "spot"},
        {"symbol": "eurusd", "bid": None, "ask": 1.12, "tenor": "1m"},
        {"symbol": "eurusd", "bid": 1.09, "ask": 1.08, "tenor": "1m"},
        {"symbol": "eurusd", "bid": 1.11, "ask": 1.12, "tenor": "3m"}
    ]
    
    return pd.DataFrame(quotes)

if __name__ == "__main__":
    quotes_df = get_equity_broker_quotes()
    print(quotes_df)
        
"""

