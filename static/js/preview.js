let currentFrame = '';
let isPlaying = false;
let eventSource = null;

function initPreview(videoId, streamUrl, audioUrl) {
    const asciiDisplay = document.getElementById('asciiDisplay');
    const audioPlayer = document.getElementById('audioPlayer');
    const playBtn = document.getElementById('playBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const fullscreenBtn = document.getElementById('fullscreenBtn');

    playBtn.addEventListener('click', () => {
        if (!isPlaying) {
            startStreaming();
            audioPlayer.play();
            isPlaying = true;
        }
    });

    pauseBtn.addEventListener('click', () => {
        if (isPlaying) {
            stopStreaming();
            audioPlayer.pause();
            isPlaying = false;
        }
    });

    fullscreenBtn.addEventListener('click', () => {
        if (asciiDisplay.requestFullscreen) {
            asciiDisplay.requestFullscreen();
        } else if (asciiDisplay.webkitRequestFullscreen) {
            asciiDisplay.webkitRequestFullscreen();
        } else if (asciiDisplay.msRequestFullscreen) {
            asciiDisplay.msRequestFullscreen();
        }
    });

    // Sync audio with ASCII display
    audioPlayer.addEventListener('play', () => {
        if (!isPlaying) {
            startStreaming();
            isPlaying = true;
        }
    });

    audioPlayer.addEventListener('pause', () => {
        if (isPlaying) {
            stopStreaming();
            isPlaying = false;
        }
    });

    function startStreaming() {
        if (eventSource) {
            eventSource.close();
        }

        // Use EventSource for server-sent events (simplified approach)
        // In a real implementation, you might want to use WebSockets for better sync
        eventSource = new EventSource(streamUrl);
        
        eventSource.onmessage = function(event) {
            currentFrame = event.data;
            asciiDisplay.textContent = currentFrame;
            
            // Scroll to bottom to show latest frame
            asciiDisplay.scrollTop = asciiDisplay.scrollHeight;
        };

        eventSource.onerror = function(error) {
            console.error('EventSource failed:', error);
            stopStreaming();
        };
    }

    function stopStreaming() {
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
    }

    // Clean up on page unload
    window.addEventListener('beforeunload', stopStreaming);
}