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
    "content": {
      "dataframeData": {
        "content": "<HTML string representing the DataFrame table>",
        "type": "dataframe"
      },
      "plotlyData": {
        "content": {
          "data": "<Plotly trace data>",
          "layout": "<Plotly layout object>"
        },
        "type": "plotly"
      },
      "textData": {
        "content": "<Plain text result>",
        "type": "text"
      }
    },
    "type": "<Type of result: 'dataframe', 'plotly', or 'text'>"
  }
}

