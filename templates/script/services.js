$(document).ready( function () {
    $('#servicesTable').DataTable({
        // Configuration options go here
        // Example to enable case-insensitive searching:
        "search": {
            "caseInsensitive": true
        }
    });
});

function deleteService(serviceUrl, event) {
    event.preventDefault(); // Prevent form submission or navigation
    let modal = document.getElementById('deleteModal');
    modal.style.display = 'block'; // Show the modal

    let confirmBtn = document.getElementById('confirmDelete');
    let cancelBtn = document.getElementById('cancelDelete');
    let closeButton = document.querySelector('.close-button');
    let btn = event.target;
    let row = btn.closest('tr'); // Find the parent row

    // Confirm Deletion
    confirmBtn.onclick = function() {
        // Check if it's the only service of its type
        let serviceType = row.querySelector('td:nth-child(2)').textContent;
        let allTypes = [...document.querySelectorAll('td:nth-child(2)')].map(td => td.textContent);
        let typeCount = allTypes.filter(type => type === serviceType).length;

        if(typeCount <= 1) {
            alert('Cannot delete the only service of its type.');
        } else {
            console.log(`Requesting to stop service: ${serviceUrl}`);
            fetch(`/stop_service?service_url=${serviceUrl}`, {
            method: 'DELETE', // Use DELETE method for stopping the service
            headers: {
                'Content-Type': 'application/json',
            }
        })
            .then(response => {
                if (response.ok) {
                    console.log('Service stopped successfully');
                    window.location.reload(); // Reload the page to reflect changes
                } else {
                    console.error('Failed to stop service');
                    alert('Failed to stop service.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while stopping the service.');
            });
    }
        modal.style.display = 'none'; // Hide the modal
    };

    // Cancel Deletion or Close Modal
    function closeModal() {
        modal.style.display = 'none';
    }
    cancelBtn.onclick = closeModal;
    closeButton.onclick = closeModal;

    // Close the modal if the user clicks anywhere outside of it
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    };
}