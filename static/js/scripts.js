document.addEventListener("DOMContentLoaded", function() {
    const highlights = document.querySelectorAll(".highlight");

    highlights.forEach((highlight) => {
        highlight.addEventListener("mouseover", function() {
            const commentId = highlight.getAttribute("data-comment");
            const commentBox = document.getElementById(commentId);
            if (commentBox) {
                commentBox.classList.add("highlight");
            }
        });

        highlight.addEventListener("mouseout", function() {
            const commentId = highlight.getAttribute("data-comment");
            const commentBox = document.getElementById(commentId);
            if (commentBox) {
                commentBox.classList.remove("highlight");
            }
        });
    });
});


function handleFormSubmission(event, messageid){
    const successMessage = document.getElementById(messageid);
    successMessage.style.display = 'block';
};

document.addEventListener("DOMContentLoaded", () => {
    const pageIdentifier = document.body.getAttribute("data-page")
    if (pageIdentifier === "summary-report-logs"){
        alert("Welcome to the Summary Report History Logs!");
    }
})

window.onload = function(){
    
    const loadingRow = document.getElementById('loading-row');

    fetch("/loader-status")
        .then(response => response.json())
        .then(data => {
            const showLoaderStatus = data.show_loader; // This will be True or False
            if (showLoaderStatus) {

                // Poll the job status
                console.log("Polling the job status!");
                const interval = setInterval(() => {
                fetch('/job-status')
                    .then((response) => response.json())
                    .then((statusData) => {
                        if (statusData.status === "finished"){

                            clearInterval(interval); // Stop polling
                            window.location.reload();
                            fetch('/clear-loader-flag', { method: 'POST'}) // Clear the server-side flag

                        } else if (statusData.status === "failed"){

                            clearInterval(interval);
                            alert("The job failed. Please try again.");
                            loadingRow.style.display = "none"; // Hide the loading row
                            fetch('/clear-loader-flag', { method: 'POST'}) // Clear the server-side flag

                        } else if (statusData.status === "in-progress"){

                            // Show the loading row
                            loadingRow.style.display = "table-row";
                        }
                    })
                }, 1000); // Polling interval of 1 second
            }
        })
}


function toggleMenu(button) {
    // Find the next row (menu row)
    const menuRow = button.closest('tr').nextElementSibling;

    if (menuRow.classList.contains('hidden')) {
        // Show the menu row
        menuRow.classList.remove('hidden');
        button.textContent = "▼"; // Change the button to a down arrow
    } else {
        // Hide the menu row
        menuRow.classList.add('hidden');
        button.textContent = "▶"; // Change the button to a right arrow
    }
}