from flask import Flask, request, jsonify, send_from_directory
import os
import subprocess
import zipfile
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Folders for uploads and outputs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    # Serve index.html directly from the root directory
    return send_from_directory('.', 'index.html')

def ensure_user_directory(base_folder, user_id):
    user_folder = os.path.join(base_folder, user_id)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

@app.route('/upload', methods=['POST'])
def upload():
    user_id = request.args.get('user_id', 'default_user')
    user_folder = ensure_user_directory(UPLOAD_FOLDER, user_id)

    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No files uploaded."}), 400

    for file in files:
        file.save(os.path.join(user_folder, file.filename))

    return jsonify({"message": "Files uploaded successfully!", "user_id": user_id})

@app.route('/process', methods=['POST'])
def process_videos():
    user_id = request.json.get('user_id', 'default_user')
    hooks = request.json.get('hooks', [])
    bodies = request.json.get('bodies', [])
    ctas = request.json.get('ctas', [])
    if not hooks or not bodies or not ctas:
        return jsonify({"error": "Please provide hooks, bodies, and CTAs."}), 400

    user_folder = ensure_user_directory(UPLOAD_FOLDER, user_id)
    output_zip_path = os.path.join(user_folder, "concatenated_videos.zip")
    concatenated_videos = []

    try:
        with zipfile.ZipFile(output_zip_path, "w") as zipf:
            for hook in hooks:
                for body in bodies:
                    for cta in ctas:
                        output_file = os.path.join(user_folder, f"{hook}_{body}_{cta}.mp4")
                        cmd = [
                            'ffmpeg',
                            '-i', os.path.join(user_folder, hook),
                            '-i', os.path.join(user_folder, body),
                            '-i', os.path.join(user_folder, cta),
                            '-filter_complex', 'concat=n=3:v=1:a=1',
                            output_file
                        ]
                        print(f"Running command: {' '.join(cmd)}")  # Debugging log
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        if result.returncode == 0:
                            print(f"Created video: {output_file}")
                            zipf.write(output_file, arcname=os.path.basename(output_file))
                            concatenated_videos.append(output_file)
                        else:
                            print(f"Error creating video: {result.stderr}")
    except Exception as e:
        print(f"Error during video processing: {e}")
        return jsonify({"error": "An error occurred during video processing"}), 500

    return jsonify({"message": "Videos processed successfully!", "zip_file": output_zip_path})

@app.route('/download/<user_id>', methods=['GET'])
def download(user_id):
    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    zip_file_path = os.path.join(user_folder, "concatenated_videos.zip")
    if not os.path.exists(zip_file_path):
        return jsonify({"error": "File not found."}), 404
    return send_from_directory(user_folder, "concatenated_videos.zip", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
