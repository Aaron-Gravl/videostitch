import os
import subprocess
import zipfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Folders for uploads
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def ensure_user_directory(base_folder, user_id):
    user_folder = os.path.join(base_folder, user_id)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

@app.route('/')
def home():
    return "Video Stitcher API is running."

@app.route('/upload', methods=['POST'])
def upload():
    user_id = request.args.get('user_id', 'default_user')
    user_folder = ensure_user_directory(UPLOAD_FOLDER, user_id)

    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No files uploaded."}), 400

    uploaded_files = []
    for file in files:
        file_path = os.path.join(user_folder, file.filename)
        file.save(file_path)
        uploaded_files.append(file.filename)

    return jsonify({"message": "Files uploaded successfully!", "files": uploaded_files})

@app.route('/process', methods=['POST'])
def process_videos():
    try:
        user_id = request.json.get('user_id', 'default_user')
        hooks = request.json.get('hooks', [])
        bodies = request.json.get('bodies', [])
        ctas = request.json.get('ctas', [])

        if not hooks or not bodies or not ctas:
            return jsonify({"error": "Please provide hooks, bodies, and CTAs."}), 400

        user_folder = ensure_user_directory(UPLOAD_FOLDER, user_id)
        output_zip_path = os.path.join(user_folder, "concatenated_videos.zip")

        concatenated_videos = []
        
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
                            concatenated_videos.append(output_file)
                            zipf.write(output_file, arcname=os.path.basename(output_file))
                        else:
                            print(f"Error creating video: {result.stderr}")

        return send_file(output_zip_path, as_attachment=True)
    except Exception as e:
        print(f"Error during video processing: {e}")
        return jsonify({"error": "An error occurred during video processing."}), 500

if __name__ == '__main__':
    app.run(debug=True)
