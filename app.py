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

@app.route('/images/<folder>')
def get_folder_images(folder):
    if folder != 'unsorted' and (not folder.isdigit() or not (1 <= int(folder) <= 9)):
        return jsonify({'error': 'Invalid folder'}), 400
    
    folder_path = os.path.join(UPLOAD_FOLDER, folder)
    if not os.path.exists(folder_path):
        return jsonify({'error': 'Folder not found'}), 404
        
    images = [f for f in os.listdir(folder_path) 
             if os.path.isfile(os.path.join(folder_path, f)) and 
             allowed_file(f)]
    return jsonify({'images': images})

@app.route('/uploads/<folder>/<filename>')
def uploaded_file(folder, filename):
    return send_from_directory(os.path.join(UPLOAD_FOLDER, folder), filename)

@app.route('/move/<filename>/<source_folder>/<dest_folder>')
def move_file(filename, source_folder, dest_folder):
    # Validate source folder
    if source_folder != 'unsorted' and (not source_folder.isdigit() or not (1 <= int(source_folder) <= 9)):
        return jsonify({'error': 'Invalid source folder'}), 400
    
    # Validate destination folder
    if dest_folder != 'unsorted' and (not dest_folder.isdigit() or not (1 <= int(dest_folder) <= 9)):
        return jsonify({'error': 'Invalid destination folder'}), 400
    
    source = os.path.join(UPLOAD_FOLDER, source_folder, filename)
    destination = os.path.join(UPLOAD_FOLDER, dest_folder, filename)
    
    if not os.path.exists(source):
        return jsonify({'error': 'Source file not found'}), 404
    
    try:
        shutil.move(source, destination)
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error moving file: {str(e)}")
        return jsonify({'error': 'Failed to move file'}), 500

@app.route('/folder-stats')
def get_folder_stats():
    stats = {}
    folders = [str(i) for i in range(1, 10)]
    
    for folder in folders:
        folder_path = os.path.join(UPLOAD_FOLDER, folder)
        if os.path.exists(folder_path):
            images = [f for f in os.listdir(folder_path) 
                     if os.path.isfile(os.path.join(folder_path, f)) and 
                     allowed_file(f)]
            stats[folder] = len(images)
    
    return jsonify(stats)

@app.route('/download-folder/<folder>')
def download_folder(folder):
    if not folder.isdigit() or not (1 <= int(folder) <= 9):
        return jsonify({'error': 'Invalid folder'}), 400
    
    folder_path = os.path.join(UPLOAD_FOLDER, folder)
    if not os.path.exists(folder_path):
        return jsonify({'error': 'Folder not found'}), 404
    
    # Create a temporary zip file
    import tempfile
    import zipfile
    
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f'folder_{folder}.zip')
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                if allowed_file(file):
                    file_path = os.path.join(root, file)
                    arcname = os.path.basename(file_path)
                    zipf.write(file_path, arcname)
    
    return send_from_directory(temp_dir, f'folder_{folder}.zip', as_attachment=True)

# Create archive folder if it doesn't exist
ARCHIVE_FOLDER = os.path.join(UPLOAD_FOLDER, 'archive')
if not os.path.exists(ARCHIVE_FOLDER):
    os.makedirs(ARCHIVE_FOLDER)

@app.route('/empty-folder/<folder>')
def empty_folder(folder):
    if not folder.isdigit() or not (1 <= int(folder) <= 9):
        return jsonify({'error': 'Invalid folder'}), 400
    
    source_folder = os.path.join(UPLOAD_FOLDER, folder)
    if not os.path.exists(source_folder):
        return jsonify({'error': 'Folder not found'}), 404
    
    try:
        # Move all files to archive folder
        for filename in os.listdir(source_folder):
            if os.path.isfile(os.path.join(source_folder, filename)) and allowed_file(filename):
                source = os.path.join(source_folder, filename)
                # Add timestamp to prevent filename conflicts
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                archive_filename = f'{timestamp}_{filename}'
                destination = os.path.join(ARCHIVE_FOLDER, archive_filename)
                shutil.move(source, destination)
        
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error emptying folder: {str(e)}")
        return jsonify({'error': 'Failed to empty folder'}), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
