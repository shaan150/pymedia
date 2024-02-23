document.addEventListener('DOMContentLoaded', () => {
    const audioPlayer = document.querySelector('#audio-player');
    const playPauseBtn = document.querySelector('#play-pause-btn');
    const currentTimeElement = document.querySelector('#current-time');
    const totalTimeElement = document.querySelector('#total-time');
    const progressBar = document.querySelector('#progress-bar');
    const trackImage = document.querySelector('#track-image');
    const trackTitle = document.querySelector('#track-title');
    const downloadBtn = document.querySelector('#download-btn');

    // Function to play a song with provided details
    window.playSong = (songId, songName, artist, imageUrl, songUrl) => {
        trackImage.src = imageUrl;
        trackTitle.innerText = `${songName} by ${artist}`;
        downloadBtn.href = songUrl;
        audioPlayer.src = songUrl;
        audioPlayer.load();
        audioPlayer.play().catch(error => {
            console.warn('Playback failed to start automatically. User interaction required.');
        });
        playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
        // save the song details to local storage
        localStorage.setItem('currentSongUrl', songUrl);
        localStorage.setItem('currentPlaybackTime', '0');
        localStorage.setItem('currentSongName', songName);
        localStorage.setItem('currentArtist', artist);
        localStorage.setItem('currentImageUrl', imageUrl);
    };

    // Load the saved song and playback time
    const loadSavedSong = () => {
        const savedSongUrl = localStorage.getItem('currentSongUrl');
        const savedTime = parseFloat(localStorage.getItem('currentPlaybackTime'));
        const savedSongName = localStorage.getItem('currentSongName');
        const savedArtist = localStorage.getItem('currentArtist');
        const savedImageUrl = localStorage.getItem('currentImageUrl');
        if (savedSongName && savedArtist) {
            trackTitle.innerText = `${savedSongName} by ${savedArtist}`;
        }

        if (savedImageUrl) {
            trackImage.src = savedImageUrl;
        }

        if (savedSongUrl) {
            audioPlayer.src = savedSongUrl;
            downloadBtn.href = savedSongUrl;
            audioPlayer.addEventListener('loadedmetadata', () => {
                totalTimeElement.textContent = formatTime(audioPlayer.duration);
                if (!isNaN(savedTime)) {
                    audioPlayer.currentTime = savedTime;
                }
                audioPlayer.play().catch(error => {
                    console.warn('Playback failed to start automatically. User interaction required.');
                });
            }, { once: true });
        }
    };

    // Toggle play/pause function
    const togglePlayPause = () => {
        if (audioPlayer.paused) {
            audioPlayer.play();
        } else {
            audioPlayer.pause();
        }
    };

    // Update UI with current song time and save playback time
    const updateCurrentTime = () => {
        const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
        progressBar.style.width = `${progress}%`;
        currentTimeElement.textContent = formatTime(audioPlayer.currentTime);
        localStorage.setItem('currentPlaybackTime', audioPlayer.currentTime.toString());
    };

    // Format time from seconds to MM:SS
    const formatTime = (seconds) => {
        const minutes = Math.floor(seconds / 60);
        const secondsPart = Math.floor(seconds % 60);
        return `${minutes}:${secondsPart < 10 ? '0' : ''}${secondsPart}`;
    };

    // Set up event listeners
    playPauseBtn.addEventListener('click', togglePlayPause);
    audioPlayer.addEventListener('timeupdate', updateCurrentTime);
    audioPlayer.addEventListener('play', () => playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>');
    audioPlayer.addEventListener('pause', () => playPauseBtn.innerHTML = '<i class="fas fa-play"></i>');
    audioPlayer.addEventListener('loadedmetadata', () => {
        totalTimeElement.textContent = formatTime(audioPlayer.duration);
    });

    document.querySelector('.progress-container').addEventListener('click', function(e) {
        const width = this.offsetWidth;
        const offsetX = e.pageX - this.offsetLeft;
        const duration = audioPlayer.duration;
        const newTime = (offsetX / width) * duration;
        audioPlayer.currentTime = newTime;
    });

    window.onbeforeunload = () => {
        localStorage.setItem('currentSongUrl', audioPlayer.src);
        localStorage.setItem('currentPlaybackTime', audioPlayer.currentTime.toString());
    };

    loadSavedSong();
});