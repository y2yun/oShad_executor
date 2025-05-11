import pandas as pd
import plotly.graph_objects as go
from ast import parse, Expr, Expression
import sys
import io
import contextlib
import json

def execute_code(code_str):
    stdout = io.StringIO()
    stderr = io.StringIO()

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

    local_vars = {}

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
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):

            restricted_globals = {
                "__builtins__": safe_builtins,
                "pd": pd,
                "go": go,
            }

            tree = parse(code_str, mode='exec')
            modified_code = code_str.strip() + "\n"

            if tree.body:
                last_node = tree.body[-1]
                if isinstance(last_node, (Expr, Expression)):
                    lines = code_str.strip().splitlines()
                    last_line = lines[-1]
                    modified_code += f"\n_result = ({last_line})"
                else:
                    modified_code += "\n_result = None"
            else:
                modified_code += "\n_result = None"

            exec(modified_code, restricted_globals, local_vars)

        # 处理输出
        console_output = stdout.getvalue().strip()
        error_output = stderr.getvalue().strip()

        if console_output:
            result_data["console"].extend(console_output.splitlines())
        if error_output:
            result_data["console"].append(f"Error: {error_output}")

        result = local_vars.get('_result', None)

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
                unified_content["plotlyData"] = {
                    "type": "plotly",
                    "content": result.get("content")
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

        result_data["result"]["type"] = unified_type
        result_data["result"]["content"] = unified_content

    except Exception as e:
        result_data["error"] = str(e)
        result_data["console"].append(f"Error: {str(e)}")

    return result_data


# 示例调用
if __name__ == "__main__":
    code = """
-----------------------
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

"""

    response = execute_code(code)
    print(json.dumps(response, indent=2))
