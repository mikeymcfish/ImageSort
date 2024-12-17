import os
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from werkzeug.utils import secure_filename
import shutil
import google_drive

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
# OAuth2 settings
app.config['SESSION_TYPE'] = 'filesystem'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # For development only

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'zip'}

# Create upload folder and subfolders if they don't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'unsorted'))
    for i in range(1, 10):
        os.makedirs(os.path.join(UPLOAD_FOLDER, str(i)))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': 'No files provided'}), 400

        files = request.files.getlist('files[]')
        uploaded_files = []

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                
                # Handle ZIP files
                if filename.lower().endswith('.zip'):
                    try:
                        import zipfile
                        zip_path = os.path.join(UPLOAD_FOLDER, filename)
                        file.save(zip_path)
                        
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            for zip_info in zip_ref.infolist():
                                if not zip_info.filename.endswith('/'):  # Skip directories
                                    # Get the file extension
                                    _, ext = os.path.splitext(zip_info.filename)
                                    if ext.lower()[1:] in ALLOWED_EXTENSIONS - {'zip'}:  # Don't extract nested zip files
                                        # Extract to unsorted folder
                                        zip_ref.extract(zip_info, os.path.join(UPLOAD_FOLDER, 'unsorted'))
                                        uploaded_files.append(os.path.basename(zip_info.filename))
                        
                        # Remove the ZIP file after extraction
                        os.remove(zip_path)
                    except Exception as e:
                        logging.error(f"Error processing ZIP file: {str(e)}")
                        return jsonify({'error': 'Failed to process ZIP file'}), 500
                else:
                    # Handle regular image files
                    file.save(os.path.join(UPLOAD_FOLDER, 'unsorted', filename))
                    uploaded_files.append(filename)

        return jsonify({'files': uploaded_files})
    except Exception as e:
        logging.error(f"Error uploading files: {str(e)}")
        return jsonify({'error': 'Failed to upload files'}), 500

@app.route('/folder-stats')
def get_folder_stats():
    try:
        stats = {}
        for folder in ['unsorted'] + [str(i) for i in range(1, 10)]:
            folder_path = os.path.join(UPLOAD_FOLDER, folder)
            if os.path.exists(folder_path):
                images = [f for f in os.listdir(folder_path) 
                         if os.path.isfile(os.path.join(folder_path, f)) and 
                         allowed_file(f) and not f.lower().endswith('.zip')]
                stats[folder] = len(images)
        return jsonify(stats)
    except Exception as e:
        logging.error(f"Error getting folder stats: {str(e)}")
        return jsonify({'error': 'Failed to get folder stats'}), 500

@app.route('/images/<folder>')
def get_images(folder):
    try:
        if folder not in ['unsorted'] + [str(i) for i in range(1, 10)]:
            return jsonify({'error': 'Invalid folder'}), 400
            
        folder_path = os.path.join(UPLOAD_FOLDER, folder)
        if not os.path.exists(folder_path):
            return jsonify({'error': 'Folder not found'}), 404
            
        images = []
        for filename in os.listdir(folder_path):
            if allowed_file(filename) and not filename.lower().endswith('.zip'):
                images.append({
                    'name': filename,
                    'folder': folder,
                    'url': url_for('get_image', folder=folder, filename=filename)
                })
                
        return jsonify({'images': images})
    except Exception as e:
        logging.error(f"Error getting images: {str(e)}")
        return jsonify({'error': 'Failed to get images'}), 500

@app.route('/uploads/<folder>/<filename>')
def get_image(folder, filename):
    try:
        return send_from_directory(os.path.join(UPLOAD_FOLDER, folder), filename)
    except Exception as e:
        logging.error(f"Error serving image: {str(e)}")
        return jsonify({'error': 'Failed to serve image'}), 500

@app.route('/move', methods=['POST'])
def move_image():
    try:
        data = request.get_json()
        if not all(k in data for k in ('filename', 'source', 'destination')):
            return jsonify({'error': 'Missing required fields'}), 400

        source = os.path.join(UPLOAD_FOLDER, data['source'], data['filename'])
        destination = os.path.join(UPLOAD_FOLDER, data['destination'], data['filename'])

        if not os.path.exists(source):
            return jsonify({'error': 'Source file not found'}), 404

        shutil.move(source, destination)
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error moving file: {str(e)}")
        return jsonify({'error': 'Failed to move file'}), 500

@app.route('/empty/<folder>', methods=['POST'])
def empty_folder(folder):
    try:
        folder_path = os.path.join(UPLOAD_FOLDER, folder)
        if not os.path.exists(folder_path):
            return jsonify({'error': 'Folder not found'}), 404

        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error emptying folder: {str(e)}")
        return jsonify({'error': 'Failed to empty folder'}), 500

@app.route('/google/auth')
def google_auth():
    flow = google_drive.create_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    flow = google_drive.create_flow()
    flow.fetch_token(authorization_response=request.url)
    
    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    return redirect(url_for('index'))

@app.route('/google/folders')
def list_folders():
    folders = google_drive.list_folders()
    if folders is None:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify({'folders': folders})

@app.route('/google/import/<folder_id>')
def import_folder(folder_id):
    try:
        success, result = google_drive.download_folder_contents(folder_id, UPLOAD_FOLDER)
        if success:
            return jsonify({'success': True, 'files': result})
        return jsonify({'error': result}), 500
    except Exception as e:
        logging.error(f"Error importing folder: {str(e)}")
        return jsonify({'error': 'Failed to import folder'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)