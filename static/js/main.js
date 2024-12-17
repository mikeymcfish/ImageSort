document.addEventListener('DOMContentLoaded', function() {
    // Populate folder list
    const folderList = document.getElementById('folderList');
    
    async function updateFolderStats() {
        try {
            const response = await fetch('/folder-stats');
            const stats = await response.json();
            
            for (let i = 1; i <= 9; i++) {
                const folderElement = document.getElementById(`folder-${i}`);
                if (folderElement) {
                    const countElement = folderElement.querySelector('.image-count');
                    countElement.textContent = `${stats[i] || 0} images`;
                }
            }
        } catch (error) {
            console.error('Error updating folder stats:', error);
        }
    }
    
    async function downloadFolder(folder) {
        try {
            window.location.href = `/download-folder/${folder}`;
            showToast('Download started', 'success');
        } catch (error) {
            console.error('Error downloading folder:', error);
            showToast('Download failed', 'error');
        }
    }
    
    async function emptyFolder(folder) {
        if (!confirm(`Are you sure you want to move all images from Folder ${folder} to the archive?`)) {
            return;
        }
        
        try {
            const response = await fetch(`/empty-folder/${folder}`);
            const data = await response.json();
            
            if (data.success) {
                showToast(`Folder ${folder} emptied successfully`, 'success');
                updateFolderStats();
            } else {
                showToast(data.error || 'Failed to empty folder', 'error');
            }
        } catch (error) {
            console.error('Error emptying folder:', error);
            showToast('Failed to empty folder', 'error');
        }
    }
    
    for (let i = 1; i <= 9; i++) {
        const folderCol = document.createElement('div');
        folderCol.className = 'col-md-4 mb-3';
        folderCol.innerHTML = `
            <div class="folder-item" id="folder-${i}">
                <span class="key">${i}</span>
                <div class="folder-info">
                    <span class="folder-name">Folder ${i}</span>
                    <span class="image-count">0 images</span>
                </div>
                <div class="folder-actions">
                    <button onclick="downloadFolder(${i})" class="btn btn-sm btn-primary">
                        <i class="fas fa-download"></i>
                    </button>
                    <button onclick="emptyFolder(${i})" class="btn btn-sm btn-danger">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
        folderList.appendChild(folderCol);
    }
    
    // Update stats periodically
    updateFolderStats();
    setInterval(updateFolderStats, 5000);
    let currentImages = [];
    let currentIndex = 0;
    
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const currentImage = document.getElementById('currentImage');
    const noImageMessage = document.getElementById('noImageMessage');
    const prevButton = document.getElementById('prevButton');
    const nextButton = document.getElementById('nextButton');

    // Initialize
    loadImages();

    // Event Listeners
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);
    prevButton.addEventListener('click', showPreviousImage);
    nextButton.addEventListener('click', showNextImage);
    document.addEventListener('keydown', handleKeyPress);

    // Drag and Drop Handlers
    function handleDragOver(e) {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    }

    function handleDragLeave(e) {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
    }

    function handleDrop(e) {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        
        const files = Array.from(e.dataTransfer.files).filter(file => 
            file.type.startsWith('image/'));
        
        uploadFiles(files);
    }

    function handleFileSelect(e) {
        const files = Array.from(e.target.files).filter(file => 
            file.type.startsWith('image/'));
        uploadFiles(files);
    }

    // File Upload
    async function uploadFiles(files) {
        const uploadProgress = document.getElementById('uploadProgress');
        const progressBar = uploadProgress.querySelector('.progress-bar');
        const progressText = uploadProgress.querySelector('.progress-percentage');
        
        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);

            try {
                uploadProgress.classList.remove('d-none');
                
                const xhr = new XMLHttpRequest();
                await new Promise((resolve, reject) => {
                    xhr.upload.addEventListener('progress', (e) => {
                        if (e.lengthComputable) {
                            const percentComplete = Math.round((e.loaded / e.total) * 100);
                            progressBar.style.width = percentComplete + '%';
                            progressText.textContent = percentComplete + '%';
                        }
                    });

                    xhr.addEventListener('load', async () => {
                        if (xhr.status === 200) {
                            const data = JSON.parse(xhr.responseText);
                            if (data.success) {
                                showToast('File uploaded successfully!', 'success');
                                await loadImages();
                                resolve();
                            } else {
                                showToast(data.error, 'error');
                                reject(new Error(data.error));
                            }
                        } else {
                            showToast('Upload failed', 'error');
                            reject(new Error('Upload failed'));
                        }
                    });

                    xhr.addEventListener('error', () => {
                        showToast('Upload failed', 'error');
                        reject(new Error('Upload failed'));
                    });

                    xhr.open('POST', '/upload');
                    xhr.send(formData);
                });
            } catch (error) {
                console.error('Upload error:', error);
            }
        }
        
        // Hide progress bar after all uploads
        uploadProgress.classList.add('d-none');
        progressBar.style.width = '0%';
        progressText.textContent = '0%';
    }

    // Image Navigation
    async function loadImages() {
        try {
            const response = await fetch('/images/unsorted');
            const data = await response.json();
            currentImages = data.images;
            updateImageDisplay();
        } catch (error) {
            console.error('Error loading images:', error);
            showToast('Failed to load images', 'error');
        }
    }

    // Preload next image
    function preloadImage(index) {
        if (index >= 0 && index < currentImages.length) {
            const img = new Image();
            img.src = `/uploads/unsorted/${currentImages[index]}`;
        }
    }

    function updateImageDisplay() {
        if (currentImages.length === 0) {
            currentImage.classList.add('d-none');
            noImageMessage.classList.remove('d-none');
            return;
        }

        currentImage.classList.add('loading');
        currentImage.classList.remove('d-none');
        noImageMessage.classList.add('d-none');

        // Create a temporary image for loading
        const tempImage = new Image();
        tempImage.onload = () => {
            currentImage.src = tempImage.src;
            currentImage.classList.remove('loading');
            
            // Preload next and previous images
            preloadImage(currentIndex + 1);
            preloadImage(currentIndex - 1);
        };
        tempImage.src = `/uploads/unsorted/${currentImages[currentIndex]}`;
        
        // Update navigation buttons
        prevButton.disabled = currentIndex === 0;
        nextButton.disabled = currentIndex === currentImages.length - 1;
    }

    function showPreviousImage() {
        if (currentIndex > 0) {
            currentIndex--;
            updateImageDisplay();
        }
    }

    function showNextImage() {
        if (currentIndex < currentImages.length - 1) {
            currentIndex++;
            updateImageDisplay();
        }
    }

    // Hotkey Handler
    async function handleKeyPress(e) {
        const key = e.key;
        
        // Handle arrow keys for navigation
        if (key === 'ArrowLeft') {
            showPreviousImage();
            return;
        } else if (key === 'ArrowRight') {
            showNextImage();
            return;
        }
        
        // Handle number keys for moving files
        if (/^[1-9]$/.test(key) && currentImages.length > 0) {
            try {
                const response = await fetch(
                    `/move/${currentImages[currentIndex]}/${key}`
                );
                const data = await response.json();
                
                if (data.success) {
                    showToast(`Moved to folder ${key}`, 'success');
                    currentImages.splice(currentIndex, 1);
                    if (currentIndex >= currentImages.length) {
                        currentIndex = Math.max(0, currentImages.length - 1);
                    }
                    updateImageDisplay();
                } else {
                    showToast(data.error, 'error');
                }
            } catch (error) {
                console.error('Error moving file:', error);
                showToast('Failed to move file', 'error');
            }
        }
    }

    // Toast Notifications
    function showToast(message, type) {
        Toastify({
            text: message,
            duration: 3000,
            gravity: "top",
            position: "right",
            backgroundColor: type === 'success' ? "#28a745" : "#dc3545",
        }).showToast();
    }
});