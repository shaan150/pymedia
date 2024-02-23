$(document).ready(function() {
    $('#libraryTable').DataTable({
        "paging": true, // Enable pagination
        "ordering": true, // Enable column-based sorting
        "info": true, // Display table info (e.g., showing 1 to 10 of 50 entries)
        "searching": true // Enable search functionality
    });
});

function confirmDelete(songId) {
    // Show modal logic here, store songId in a data attribute or global variable for use in delete confirmation
    let modal = document.getElementById('deleteModal');
    modal.style.display = 'block';
    let confirmDeleteBtn = document.getElementById('confirmDelete');
    confirmDeleteBtn.onclick = function() { deleteSong(songId); }; // Assign the delete function to the confirm button
}

function deleteSong(songId) {
    // Send request to delete song
    fetch(`/songs/song/delete?song_id=${songId}`, { method: 'DELETE' })
        .then(response => {
            if (response.ok) {
                window.location.reload();
            }
        })
        .catch(error => console.error('Error:', error));
}

$(document).ready( function () {
    $('#playlistTable').DataTable();
} );