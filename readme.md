# Python Code Executor API Documentation

This project provides a Python code execution interface that supports returning results (e.g., DataFrame tables) and console output in JSON format. This interface is suitable for scenarios where user-submitted Python code needs to be executed and the results retrieved.

## API Response Format

All requests return a unified response format through the API. The response includes three fields: `console`, `error`, and `result`.

### Response Structure

The structure of the API response is as follows:

```json
{
  "console": [],
  "error": null,
  "result": {
    "content": "<Content based on the type>",
    "type": "<Type of result: 'text', 'dataframe', 'plotly', etc.>"
  }
}
