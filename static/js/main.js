document.addEventListener('DOMContentLoaded', function() {
    // Populate folder list
    const folderList = document.getElementById('folderList');
    for (let i = 1; i <= 9; i++) {
        const folderCol = document.createElement('div');
        folderCol.className = 'col-md-4';
        folderCol.innerHTML = `
            <div class="folder-item">
                <span class="key">${i}</span>
                <span class="folder-name">Folder ${i}</span>
            </div>
        `;
        folderList.appendChild(folderCol);
    }
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
        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                
                if (data.success) {
                    showToast('File uploaded successfully!', 'success');
                    await loadImages();
                } else {
                    showToast(data.error, 'error');
                }
            } catch (error) {
                showToast('Upload failed', 'error');
                console.error('Upload error:', error);
            }
        }
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

    function updateImageDisplay() {
        if (currentImages.length === 0) {
            currentImage.classList.add('d-none');
            noImageMessage.classList.remove('d-none');
            return;
        }

        currentImage.classList.remove('d-none');
        noImageMessage.classList.add('d-none');
        currentImage.src = `/uploads/unsorted/${currentImages[currentIndex]}`;
        
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
