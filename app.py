from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import zipfile
import subprocess

app = Flask(__name__, static_folder="static")
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    user_id = request.args.get('user_id', 'default_user')
    upload_type = request.args.get('type')  # hooks, bodies, ctas
    user_folder = os.path.join(UPLOAD_FOLDER, user_id, upload_type)
    os.makedirs(user_folder, exist_ok=True)
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join(user_folder, file.filename)
    file.save(file_path)
    return jsonify({"message": "File uploaded successfully", "path": file_path})

@app.route('/process', methods=['POST'])
def process_videos():
    user_id = request.args.get('user_id', 'default_user')
    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    output_zip_path = os.path.join(OUTPUT_FOLDER, f"{user_id}_videos.zip")
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    hooks = os.listdir(os.path.join(user_folder, 'hooks'))
    bodies = os.listdir(os.path.join(user_folder, 'bodies'))
    ctas = os.listdir(os.path.join(user_folder, 'ctas'))

    with zipfile.ZipFile(output_zip_path, "w") as zipf:
        for hook in hooks:
            for body in bodies:
                for cta in ctas:
                    hook_path = os.path.join(user_folder, 'hooks', hook)
                    body_path = os.path.join(user_folder, 'bodies', body)
                    cta_path = os.path.join(user_folder, 'ctas', cta)
                    output_file = f"{os.path.splitext(hook)[0]}_{os.path.splitext(body)[0]}_{os.path.splitext(cta)[0]}.mp4"
                    output_path = os.path.join(OUTPUT_FOLDER, output_file)

                    cmd = [
                        'ffmpeg',
                        '-i', hook_path,
                        '-i', body_path,
                        '-i', cta_path,
                        '-filter_complex', 'concat=n=3:v=1:a=1',
                        output_path
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True)

                    if result.returncode == 0:
                        zipf.write(output_path, os.path.basename(output_path))
                    else:
                        return jsonify({"error": f"FFmpeg failed: {result.stderr}"}), 500

    return jsonify({"message": "Processing completed", "zip_path": output_zip_path})

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
