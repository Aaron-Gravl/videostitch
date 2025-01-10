from flask import Flask, request, jsonify, send_file
import os
import zipfile
import subprocess

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def home():
    return "Video Stitcher API is running."

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file_type = request.args.get('type')
        user_id = request.args.get('user_id', 'default_user')

        if file_type not in ['hooks', 'bodies', 'ctas']:
            return jsonify({"error": "Invalid file type"}), 400

        user_folder = os.path.join(UPLOAD_FOLDER, user_id)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)

        uploaded_files = request.files.getlist('files')
        if not uploaded_files:
            return jsonify({"error": "No files uploaded"}), 400

        saved_files = []
        for file in uploaded_files:
            file_path = os.path.join(user_folder, file.filename)
            file.save(file_path)
            saved_files.append(file.filename)

        return jsonify({"message": "Files uploaded successfully", "files": saved_files}), 200
    except Exception as e:
        return jsonify({"error": "An error occurred during file upload", "details": str(e)}), 500

@app.route('/process', methods=['POST'])
def process_videos():
    try:
        user_id = request.form.get('user_id', 'default_user')
        user_folder = os.path.join(UPLOAD_FOLDER, user_id)

        hooks = request.form.getlist('hooks[]')
        bodies = request.form.getlist('bodies[]')
        ctas = request.form.getlist('ctas[]')

        if not hooks or not bodies or not ctas:
            return jsonify({"error": "Missing hooks, bodies, or CTAs"}), 400

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
                        print(f"Running command: {' '.join(cmd)}")  # Debug log
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        if result.returncode == 0:
                            print(f"Created video: {output_file}")
                            zipf.write(output_file, arcname=os.path.basename(output_file))
                            concatenated_videos.append(output_file)
                        else:
                            print(f"FFmpeg error: {result.stderr}")
                            return jsonify({"error": "Error processing video", "details": result.stderr}), 500

        return jsonify({"message": "Videos processed successfully", "download_url": f"/download?user_id={user_id}"}), 200

    except Exception as e:
        print(f"Error processing videos: {str(e)}")
        return jsonify({"error": "An error occurred during video processing", "details": str(e)}), 500

@app.route('/download', methods=['GET'])
def download_zip():
    try:
        user_id = request.args.get('user_id', 'default_user')
        user_folder = os.path.join(UPLOAD_FOLDER, user_id)
        zip_path = os.path.join(user_folder, "concatenated_videos.zip")

        if not os.path.exists(zip_path):
            return jsonify({"error": "ZIP file not found"}), 404

        return send_file(zip_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": "An error occurred during file download", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
