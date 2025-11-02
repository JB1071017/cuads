document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const result = document.getElementById('result');
    const curlCommand = document.getElementById('curlCommand');
    const previewLink = document.getElementById('previewLink');
    const streamLink = document.getElementById('streamLink');

    // Drag and drop functionality
    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.background = '#f0f8ff';
        uploadArea.style.borderColor = '#4CAF50';
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.background = '';
        uploadArea.style.borderColor = '#667eea';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.background = '';
        uploadArea.style.borderColor = '#667eea';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });
    
    function handleFile(file) {
        // Validate file type and size
        const allowedTypes = ['video/mp4', 'video/quicktime', 'video/x-matroska', 'video/webm', 'video/x-msvideo'];
        const maxSize = 200 * 1024 * 1024; // 200MB
        
        if (!allowedTypes.some(type => file.type.includes(type.replace('video/', '')))) {
            alert('Please select a valid video file (MP4, MOV, MKV, WEBM, AVI)');
            return;
        }
        
        if (file.size > maxSize) {
            alert('File size must be less than 200MB');
            return;
        }
        
        uploadVideo(file);
    }
    
    async function uploadVideo(file) {
        const formData = new FormData();
        formData.append('video', file);
        
        uploadProgress.style.display = 'block';
        progressFill.style.width = '10%';
        progressText.textContent = 'Uploading video...';
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                progressFill.style.width = '30%';
                progressText.textContent = 'Processing video...';
                
                // Poll for processing status
                await waitForProcessing(data.video_id);
            } else {
                throw new Error(data.error || 'Upload failed');
            }
        } catch (error) {
            progressText.textContent = `Error: ${error.message}`;
            progressFill.style.background = '#f44336';
        }
    }
    
    async function waitForProcessing(videoId) {
        const maxAttempts = 300; // 5 minutes at 1 second intervals
        let attempts = 0;
        
        while (attempts < maxAttempts) {
            try {
                const response = await fetch(`/api/status/${videoId}`);
                const status = await response.json();
                
                if (status.status === 'completed') {
                    // Processing complete
                    progressFill.style.width = '100%';
                    progressText.textContent = 'Processing complete!';
                    
                    // Show result
                    setTimeout(() => {
                        uploadProgress.style.display = 'none';
                        result.style.display = 'block';
                        
                        curlCommand.textContent = status.curl_command || `curl -N ${window.location.origin}/stream/${videoId}`;
                        previewLink.href = `/preview/${videoId}`;
                        streamLink.href = `/stream/${videoId}`;
                    }, 1000);
                    
                    return;
                } else if (status.status === 'error') {
                    throw new Error(status.error || 'Processing failed');
                } else {
                    // Still processing
                    const progress = 30 + (attempts / maxAttempts) * 60;
                    progressFill.style.width = `${progress}%`;
                    progressText.textContent = `Processing... (${attempts}s)`;
                }
            } catch (error) {
                progressText.textContent = `Error: ${error.message}`;
                progressFill.style.background = '#f44336';
                break;
            }
            
            attempts++;
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        if (attempts >= maxAttempts) {
            progressText.textContent = 'Processing timeout - video might still be processing';
        }
    }
});

function copyCurlCommand() {
    const curlCommand = document.getElementById('curlCommand');
    const textArea = document.createElement('textarea');
    textArea.value = curlCommand.textContent;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = 'Copied!';
    setTimeout(() => {
        button.textContent = originalText;
    }, 2000);
}