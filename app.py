from flask import Flask, request, jsonify, send_from_directory
import os
import subprocess
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Folders for uploads and outputs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def ensure_user_directory(base_folder, user_id):
    user_folder = os.path.join(base_folder, user_id)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

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
    user_output_folder = ensure_user_directory(OUTPUT_FOLDER, user_id)

    permutations = []

    def standardize_video(input_file, output_file):
        """
        Standardizes the video to have the same resolution, frame rate, codec, etc.
        """
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-vf', 'scale=1920:1080',
            '-r', '30',
            '-pix_fmt', 'yuv420p',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            output_file
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error standardizing {input_file}: {result.stderr}")

    for hook in hooks:
        for body in bodies:
            for cta in ctas:
                standardized_hook = os.path.join(user_folder, f"std_{hook}")
                standardized_body = os.path.join(user_folder, f"std_{body}")
                standardized_cta = os.path.join(user_folder, f"std_{cta}")

                standardize_video(os.path.join(user_folder, hook), standardized_hook)
                standardize_video(os.path.join(user_folder, body), standardized_body)
                standardize_video(os.path.join(user_folder, cta), standardized_cta)

                output_file = os.path.join(user_output_folder, f"{hook}_{body}_{cta}.mp4")
                cmd = [
                    'ffmpeg',
                    '-i', standardized_hook,
                    '-i', standardized_body,
                    '-i', standardized_cta,
                    '-filter_complex', 'concat=n=3:v=1:a=1',
                    output_file
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    permutations.append(output_file)
                else:
                    print(f"Error concatenating {hook}, {body}, {cta}: {result.stderr}")

    return jsonify({"message": "Videos processed!", "files": permutations, "user_id": user_id})

@app.route('/download/<user_id>/<filename>', methods=['GET'])
def download(user_id, filename):
    user_output_folder = os.path.join(OUTPUT_FOLDER, user_id)
    if not os.path.exists(os.path.join(user_output_folder, filename)):
        return jsonify({"error": "File not found."}), 404
    return send_from_directory(user_output_folder, filename)

if __name__ == '__main__':
    app.run(debug=True)





