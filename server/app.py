from flask import Flask, request
from flask_cors import CORS
from server.analysis import run_analysis
import traceback

app = Flask(__name__)
CORS(app)

# Homepage with upload form
@app.route("/", methods=["GET"])
def upload_form():
    return '''
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>Chat Analysis App</title>
        <style>
          body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; }
          .card { max-width: 720px; margin: 0 auto; padding: 1.5rem; border: 1px solid #e5e7eb; border-radius: 12px; }
          h1 { margin-top: 0; }
          form { display: flex; gap: 1rem; align-items: center; }
          input[type="file"] { flex: 1; }
          .btn { background: #111827; color: white; border: none; padding: 0.6rem 1rem; border-radius: 8px; cursor: pointer; }
          .btn:hover { background: #374151; }
          .results { max-width: 720px; margin: 2rem auto; padding: 1.5rem; border: 1px solid #e5e7eb; border-radius: 12px; }
          ul { line-height: 1.6; }
          .error { color: #b91c1c; }
          .success { color: #065f46; }
          a { color: #2563eb; text-decoration: none; }
          a:hover { text-decoration: underline; }
        </style>
      </head>
      <body>
        <div class="card">
          <h1>Chat Analysis App</h1>
          <p>Upload a WhatsApp chat <strong>.txt</strong> file to analyze it.</p>
          <form action="/analyze" method="post" enctype="multipart/form-data">
            <input type="file" name="chat" accept=".txt" required>
            <button class="btn" type="submit">Analyze Chat</button>
          </form>
        </div>
      </body>
    </html>
    '''

# Handle file upload and show results
@app.route("/analyze", methods=["POST"])
def analyze_chat():
    if "chat" not in request.files:
        return '''
        <!doctype html>
        <html><body>
          <h2 class="error">❌ No file uploaded</h2>
          <p>Please choose a .txt file exported from WhatsApp.</p>
          <p><a href="/">Go back</a></p>
        </body></html>
        ''', 400

    file = request.files["chat"]

    try:
        results = run_analysis(file)

        # Build a readable HTML output
        def format_value(v):
            if isinstance(v, dict):
                items = ''.join(f'<li><strong>{k}:</strong> {format_value(val)}</li>' for k, val in v.items())
                return f'<ul>{items}</ul>'
            elif isinstance(v, list):
                items = ''.join(f'<li>{format_value(item)}</li>' for item in v)
                return f'<ul>{items}</ul>'
            else:
                return str(v)

        items_html = ''.join(f'<li><strong>{key}:</strong> {format_value(value)}</li>' for key, value in results.items())

        return f'''
        <!doctype html>
        <html>
          <head>
            <meta charset="utf-8" />
            <title>Analysis Results</title>
            <style>
              body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; }}
              .results {{ max-width: 960px; margin: 0 auto; padding: 1.5rem; border: 1px solid #e5e7eb; border-radius: 12px; }}
              h2 {{ margin-top: 0; }}
              ul {{ line-height: 1.6; }}
              .success {{ color: #065f46; }}
              .actions {{ margin-top: 1rem; }}
              .btn {{ display: inline-block; background: #111827; color: white; border: none; padding: 0.6rem 1rem; border-radius: 8px; text-decoration: none; }}
              .btn:hover {{ background: #374151; }}
            </style>
          </head>
          <body>
            <div class="results">
              <h2 class="success">✅ Analysis Results</h2>
              <ul>{items_html}</ul>
              <div class="actions">
                <a class="btn" href="/">Analyze another file</a>
              </div>
            </div>
          </body>
        </html>
        '''

    except Exception as e:
        traceback.print_exc()
        return f'''
        <!doctype html>
        <html><body>
          <h2 class="error">🔥 Error during analysis</h2>
          <p>{str(e)}</p>
          <p><a href="/">Try again</a></p>
        </body></html>
        ''', 500

# Local dev entrypoint (ignored by Gunicorn in production)
if __name__ == "__main__":
    app.run(debug=True)
