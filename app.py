from flask import Flask, request, jsonify, send_from_directory
import os
import zipfile
import subprocess

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/upload", methods=["POST"])
def upload_files():
    """Upload video files to the server."""
    try:
        files = request.files
        if not files:
            return jsonify({"error": "No files uploaded"}), 400
        
        # Save uploaded files to the UPLOAD_FOLDER
        for key, file in files.items():
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
        
        return jsonify({"message": "Files uploaded successfully"})
    except Exception as e:
        return jsonify({"error": f"Upload error: {str(e)}"}), 500

@app.route("/process", methods=["POST"])
def process_videos():
    """Process uploaded videos, concatenate them, and create a ZIP file."""
    try:
        hooks = request.json.get("hooks", [])
        bodies = request.json.get("bodies", [])
        ctas = request.json.get("ctas", [])

        # Validate that all files exist before proceeding
        for file_group in [hooks, bodies, ctas]:
            for file_name in file_group:
                file_path = os.path.join(UPLOAD_FOLDER, file_name)
                if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                    return jsonify({"error": f"File {file_name} is missing or empty"}), 400

        # Create the ZIP file
        output_zip_path = os.path.join(OUTPUT_FOLDER, "concatenated_videos.zip")
        with zipfile.ZipFile(output_zip_path, "w") as zipf:
            for hook in hooks:
                for body in bodies:
                    for cta in ctas:
                        output_file = os.path.join(UPLOAD_FOLDER, f"{hook}_{body}_{cta}.mp4")
                        cmd = [
                            "ffmpeg",
                            "-i", os.path.join(UPLOAD_FOLDER, hook),
                            "-i", os.path.join(UPLOAD_FOLDER, body),
                            "-i", os.path.join(UPLOAD_FOLDER, cta),
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
    if not os.path.exists(zip_file_path) or os.path.getsize(zip_file_path) == 0:
        return jsonify({"error": "ZIP file is missing or empty"}), 404
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
