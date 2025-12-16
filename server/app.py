from flask import Flask, request, jsonify
from flask_cors import CORS
from analysis import run_analysis
import traceback

app = Flask(__name__)
CORS(app)

@app.route("/analyze", methods=["POST"])
def analyze_chat():
    if "chat" not in request.files:
        print("❌ No file found in request.")
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["chat"]
    print("✅ File received:", file.filename)
    print("📄 File type:", type(file))
    print("📄 Content-Type:", file.content_type)

    try:
        results = run_analysis(file)
        print("✅ Analysis complete")
        return jsonify(results)
    except Exception as e:
        print("🔥 Error during analysis:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
