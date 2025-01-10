from flask import Flask, request, jsonify, send_from_directory
import os
import zipfile
import subprocess

app = Flask(__name__, static_folder='static')

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/")
def home():
    """Serve the index.html file."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route("/upload", methods=["POST"])
def upload():
    """Handle file uploads."""
    user_id = request.args.get("user_id", "default_user")
    file_type = request.args.get("type", "unknown")
    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    os.makedirs(user_folder, exist_ok=True)

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    file_path = os.path.join(user_folder, f"{file_type}_{file.filename}")
    file.save(file_path)

    return jsonify({"message": f"File {file.filename} uploaded successfully"})


@app.route("/process", methods=["POST"])
def process_videos():
    """Process uploaded videos and create a concatenated zip file."""
    user_id = request.args.get("user_id", "default_user")
    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    output_zip_path = os.path.join(OUTPUT_FOLDER, f"{user_id}_videos.zip")

    hooks = [os.path.join(user_folder, f) for f in os.listdir(user_folder) if f.startswith("hooks")]
    bodies = [os.path.join(user_folder, f) for f in os.listdir(user_folder) if f.startswith("bodies")]
    ctas = [os.path.join(user_folder, f) for f in os.listdir(user_folder) if f.startswith("ctas")]

    with zipfile.ZipFile(output_zip_path, "w") as zipf:
        for hook in hooks:
            for body in bodies:
                for cta in ctas:
                    output_file = os.path.join(user_folder, f"{os.path.basename(hook)}_{os.path.basename(body)}_{os.path.basename(cta)}.mp4")
                    cmd = [
                        "ffmpeg",
                        "-i", hook,
                        "-i", body,
                        "-i", cta,
                        "-filter_complex", "concat=n=3:v=1:a=1",
                        "-y", output_file
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        zipf.write(output_file, os.path.basename(output_file))
                    else:
                        return jsonify({"error": f"FFmpeg error: {result.stderr}"}), 500

    return jsonify({"message": "Videos processed successfully", "zip_path": output_zip_path})


@app.route("/download/<path:filename>", methods=["GET"])
def download_file(filename):
    """Serve the zip file for download."""
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)


@app.route("/static/<path:filename>")
def static_files(filename):
    """Serve static files such as CSS and JS."""
    return send_from_directory(app.static_folder, filename)


if __name__ == "__main__":
    app.run(debug=True)
