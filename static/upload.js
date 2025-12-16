document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.querySelector('.drop-zone');
    const fileInput = document.getElementById('report-input');
    const fileListContainer = document.getElementById('file-list');

    // Store files in a mutable array
    let selectedFiles = [];

    if (dropZone) {
        // Trigger file input click
        dropZone.addEventListener('click', () => {
            fileInput.click();
        });

        // Drag over
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag');
        });

        // Drag leave
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag');
        });

        // Drop
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag');
            const files = Array.from(e.dataTransfer.files);
            if (files.length) {
                selectedFiles = [...selectedFiles, ...files]; // Add new files
                updateFileList();
            }
        });
    }

    // Update file list on change
    fileInput.addEventListener('change', (event) => {
        const newFiles = Array.from(event.target.files);
        selectedFiles = [...selectedFiles, ...newFiles]; // Add new files
        updateFileList();
    });

    function updateFileList() {
        fileListContainer.innerHTML = ''; // Clear previous list

        if (selectedFiles.length === 0) {
            fileListContainer.style.display = 'block'; // Ensure it's visible to show the message
            const noFileMessage = document.createElement('p');
            noFileMessage.className = 'no-files-selected-message';
            noFileMessage.textContent = 'No files selected.';
            fileListContainer.appendChild(noFileMessage);
            return;
        }

        fileListContainer.style.display = 'block';
        const list = document.createElement('ul');
        selectedFiles.forEach((file, index) => {
            const item = document.createElement('li');
            item.className = 'selected-file-item';
            
            const fileNameSpan = document.createElement('span');
            fileNameSpan.textContent = file.name;
            item.appendChild(fileNameSpan);

            const deleteButton = document.createElement('button');
            deleteButton.className = 'delete-file-btn';
            deleteButton.innerHTML = '&times;'; // 'x' icon
            deleteButton.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent dropZone click event
                removeFile(index);
            });
            item.appendChild(deleteButton);
            list.appendChild(item);
        });
        fileListContainer.appendChild(list);

        // Update the hidden file input with the new FileList
        const dataTransfer = new DataTransfer();
        selectedFiles.forEach(file => dataTransfer.items.add(file));
        fileInput.files = dataTransfer.files;
    }

    function removeFile(index) {
        selectedFiles.splice(index, 1); // Remove file from array
        updateFileList(); // Re-render the list
    }

    // Call updateFileList initially to display the "No files selected" placeholder
    updateFileList();
});
