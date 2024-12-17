# Image Sorter

A powerful web-based digital asset management tool designed for efficient and intuitive image organization. The application provides a robust, keyboard-driven interface with advanced file handling capabilities, focusing on seamless image upload, categorization, and management.

## Features
- Drag and drop image upload
- ZIP file support for bulk uploads
- Keyboard shortcuts for quick sorting (1-9)
- Image preview and navigation
- Folder management system
- Progress tracking for uploads
- Archive system for sorted images

## Requirements
- Python 3.11 or higher
- The following Python packages:
  - Flask 3.0.0
  - Pillow 10.1.0
  - python-dotenv 1.0.0
  - Werkzeug 3.0.1

## Local Installation

1. Clone this repository
2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Create a requirements.txt file with the following content:
   ```
   flask==3.0.0
   Pillow==10.1.0
   python-dotenv==1.0.0
   werkzeug==3.0.1
   ```
4. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Run the Flask application:
   ```bash
   python main.py
   ```
2. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Upload images by:
   - Dragging and dropping images onto the upload area
   - Clicking the upload area to select files
   - Dragging and dropping ZIP files containing images
2. Use number keys (1-9) to sort images into different folders
3. Use arrow keys to navigate between images
4. Use the folder management buttons to:
   - Browse folder contents
   - Download folder contents as ZIP
   - Empty folders (moves contents to archive)

## Directory Structure
- `/uploads` - Contains all uploaded and sorted images
  - `/uploads/unsorted` - Newly uploaded images
  - `/uploads/1` through `/uploads/9` - Sorted image folders
  - `/uploads/archive` - Archive of emptied folders
