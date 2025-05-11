import pandas as pd
import plotly.graph_objects as go
import sys
import io
import contextlib
import json
import ast
from ast import parse, Expression


def execute_code(code_str):
    """
    执行用户提交的 Python 代码，并捕获控制台输出。
    自动识别最后一行表达式作为结果返回。
    """

    stdout = io.StringIO()
    stderr = io.StringIO()

    safe_builtins = {
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
        "result": None,
        "console": [],
        "error": None
    }

    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):

            restricted_globals = {
                "__builtins__": safe_builtins,
                "pd": pd,
                "go": go,
            }

            # 解析 AST 判断最后一行为表达式
            try:
                tree = parse(code_str, mode='exec')
            except SyntaxError as se:
                result_data["error"] = f"Syntax Error: {se}"
                result_data["console"].append(f"Syntax Error: {se}")
                return result_data

            modified_code = code_str.strip() + "\n"
            if tree.body:
                last_node = tree.body[-1]
                if isinstance(last_node, (Expression, ast.Expr)):
                    lines = code_str.strip().splitlines()
                    last_line = lines[-1]
                    modified_code += f"\n_result = {last_line}"
                else:
                    modified_code += "\n_result = None"
            else:
                modified_code += "\n_result = None"

            exec(modified_code, restricted_globals, local_vars)

        # 获取输出
        console_output = stdout.getvalue().strip()
        error_output = stderr.getvalue().strip()

        if console_output:
            result_data["console"].extend(console_output.splitlines())
        if error_output:
            result_data["console"].extend(error_output.splitlines())

        # 获取 _result
        result = local_vars.get('_result', None)

        # 匹配 DataFrame 或 Plotly 图表
        if isinstance(result, pd.DataFrame):
            result_data["result"] = {
                "type": "dataframe",
                "content": result.to_html(index=False)
            }
        elif isinstance(result, dict) and 'data' in result and 'layout' in result:
            result_data["result"] = {
                "type": "plotly",
                "content": json.dumps(result)
            }
        elif result is not None:
            result_data["result"] = {
                "type": "text",
                "content": str(result)
            }

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