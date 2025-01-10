from flask import Flask, request, jsonify, send_from_directory
import os
import zipfile
import subprocess

app = Flask(__name__, static_folder="static")  # Define static folder for frontend files

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def home():
    """Serve the main UI."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/process", methods=["POST"])
def process_videos():
    """Process uploaded videos, concatenate them, and create a ZIP file."""
    try:
        # Simulate getting video files (e.g., hooks, bodies, ctas) from request
        user_folder = UPLOAD_FOLDER
        hooks = request.json.get("hooks", [])
        bodies = request.json.get("bodies", [])
        ctas = request.json.get("ctas", [])

        output_zip_path = os.path.join(OUTPUT_FOLDER, "concatenated_videos.zip")

        with zipfile.ZipFile(output_zip_path, "w") as zipf:
            for hook in hooks:
                for body in bodies:
                    for cta in ctas:
                        output_file = os.path.join(user_folder, f"{hook}_{body}_{cta}.mp4")
                        cmd = [
                            "ffmpeg",
                            "-i", os.path.join(user_folder, hook),
                            "-i", os.path.join(user_folder, body),
                            "-i", os.path.join(user_folder, cta),
                            "-filter_complex", "concat=n=3:v=1:a=1",
                            "-y", output_file
                        ]
                        result = subprocess.run(cmd, capture_output=True, text=True)

                        if result.returncode == 0:
                            zipf.write(output_file, os.path.basename(output_file))
                        else:
                            return jsonify({"error": f"FFmpeg error: {result.stderr}"}), 500

        return jsonify({"message": "Videos processed successfully", "zip_path": "concatenated_videos.zip"})

    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"}), 500


@app.route("/download/<path:filename>", methods=["GET"])
def download_file(filename):
    """Serve the ZIP file for download."""
    zip_file_path = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(zip_file_path):
        return jsonify({"error": "ZIP file not found"}), 404
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)


@app.route("/static/<path:filename>")
def static_files(filename):
    """Serve static files like JS, CSS, etc."""
    return send_from_directory(app.static_folder, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
