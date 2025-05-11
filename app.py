from flask import Flask, request, jsonify, render_template
from utils.code_executor import execute_code
from config import Config

app = Flask(__name__)
app.config.from_object(Config)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/execute', methods=['POST'])
def execute():
    code = request.json.get('code', '')
    result = execute_code(code)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
