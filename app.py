import os
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import shutil

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload folders exist
def ensure_folders_exist():
    # Create main upload folder
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # Create numbered folders (1-9) and unsorted
    folders = ['unsorted'] + [str(i) for i in range(1, 10)]
    for folder in folders:
        folder_path = os.path.join(UPLOAD_FOLDER, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

ensure_folders_exist()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, 'unsorted', filename))
        return jsonify({'success': True, 'filename': filename})
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/images/unsorted')
def get_unsorted_images():
    unsorted_path = os.path.join(UPLOAD_FOLDER, 'unsorted')
    images = [f for f in os.listdir(unsorted_path) 
             if os.path.isfile(os.path.join(unsorted_path, f)) and 
             allowed_file(f)]
    return jsonify({'images': images})

@app.route('/uploads/<folder>/<filename>')
def uploaded_file(folder, filename):
    return send_from_directory(os.path.join(UPLOAD_FOLDER, folder), filename)

@app.route('/move/<filename>/<folder>')
def move_file(filename, folder):
    if not folder.isdigit() or not (1 <= int(folder) <= 9):
        return jsonify({'error': 'Invalid folder'}), 400
    
    source = os.path.join(UPLOAD_FOLDER, 'unsorted', filename)
    destination = os.path.join(UPLOAD_FOLDER, folder, filename)
    
    try:
        shutil.move(source, destination)
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error moving file: {str(e)}")
        return jsonify({'error': 'Failed to move file'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
