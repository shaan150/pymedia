let currentSongMd5 = '';
function checkMd5() {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput.files.length) {
        alert('Please select a file.');
        return;
    }
    const file = fileInput.files[0];
    const reader = new FileReader();
    reader.onload = function(event) {
        const arrayBuffer = event.target.result;
        const wordArray = CryptoJS.lib.WordArray.create(arrayBuffer);
        const md5 = CryptoJS.MD5(wordArray).toString();
        compareMd5(md5);
    };
    reader.onerror = function(event) {
        alert('Error reading file: ' + event.target.error);
    };
    reader.readAsArrayBuffer(file);
}

function compareMd5(fileMd5) {
    let resultText = 'MD5 does not match.';
    // print md5
    console.log('File MD5: ' + fileMd5);
    console.log('Current Song MD5: ' + currentSongMd5);
    if (fileMd5 === currentSongMd5) {
        resultText = 'MD5 matches!';
    }
    document.getElementById('md5Result').innerText = resultText;
}

function openMd5CheckModal(songMd5) {
    currentSongMd5 = songMd5;
    document.getElementById('md5CheckModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('md5CheckModal').style.display = 'none';
}

window.onclick = function(event) {
    let modal = document.getElementById('md5CheckModal');
    if (event.target === modal) {
        modal.style.display = "none";
    }
}
