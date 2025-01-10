import os
import zipfile
import glob
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

@app.route('/')
def home():
    return "Video Stitcher API is running."

@app.route('/upload', methods=['POST'])
def upload():
    user_id = request.args.get('user_id', 'default_user')
    upload_type = request.args.get('type')
    
    if not upload_type or upload_type not in ['hooks', 'bodies', 'ctas']:
        return jsonify({"error": "Invalid upload type."}), 400

    user_folder = os.path.join('uploads', user_id, upload_type)
    os.makedirs(user_folder, exist_ok=True)

    for file in request.files.getlist('file'):
        file_path = os.path.join(user_folder, file.filename)
        file.save(file_path)
        print(f"Uploaded file: {file_path}")

    return jsonify({"success": True}), 200

@app.route('/process', methods=['POST'])
def process_videos():
    user_folder = 'uploads/default_user'
    hooks = glob.glob(os.path.join(user_folder, "hooks", "*"))
    bodies = glob.glob(os.path.join(user_folder, "bodies", "*"))
    ctas = glob.glob(os.path.join(user_folder, "ctas", "*"))

    if not hooks or not bodies or not ctas:
        print("Error: Missing uploaded videos in one or more categories.")
        return jsonify({"error": "Missing uploaded videos in one or more categories."}), 400

    output_folder = 'outputs'
    os.makedirs(output_folder, exist_ok=True)

    output_zip_path = os.path.join(output_folder, "concatenated_videos.zip")
    concatenated_videos = []

    try:
        with zipfile.ZipFile(output_zip_path, "w") as zipf:
            for hook in hooks:
                for body in bodies:
                    for cta in ctas:
                        output_file = os.path.join(output_folder, f"{os.path.basename(hook)}_{os.path.basename(body)}_{os.path.basename(cta)}.mp4")

                        # Simulate concatenation (replace this with actual ffmpeg logic)
                        with open(output_file, "w") as f:
                            f.write("Simulated video content")

                        concatenated_videos.append(output_file)
                        zipf.write(output_file, os.path.basename(output_file))

        if os.path.exists(output_zip_path):
            print(f"ZIP file created: {output_zip_path}")
            print(f"ZIP file size: {os.path.getsize(output_zip_path)} bytes")
        else:
            print("Error: ZIP file was not created!")
            return jsonify({"error": "Failed to create ZIP file."}), 500

    except Exception as e:
        print(f"Error during video processing: {e}")
        return jsonify({"error": "Error during video processing."}), 500

    return jsonify({"zip_path": "concatenated_videos.zip"}), 200

@app.route('/download/<path:filename>', methods=['GET'])
def download(filename):
    output_folder = 'outputs'
    file_path = os.path.join(output_folder, filename)

    if not os.path.exists(file_path):
        print(f"Error: File not found - {file_path}")
        return jsonify({"error": "File not found"}), 404

    if os.path.getsize(file_path) == 0:
        print("Error: ZIP file is empty!")
        return jsonify({"error": "ZIP file is empty"}), 400

    try:
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        print(f"Error in serving file: {e}")
        return jsonify({"error": "Failed to send file"}), 500

if __name__ == "__main__":
    app.run(debug=True)
