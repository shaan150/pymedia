$(document).ready(function() {
    $('#libraryTable').DataTable({
        "paging": true, // Enable pagination
        "ordering": true, // Enable column-based sorting
        "info": true, // Display table info (e.g., showing 1 to 10 of 50 entries)
        "searching": true // Enable search functionality
    });
});

$(document).ready( function () {
    $('#playlistTable').DataTable();
} );