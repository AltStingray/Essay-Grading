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
    fetch("/loader-status")
        .then(response => response.json())
        .then(data => {
            const showLoaderStatus = data.show_loader; // This will be True or False
            if (showLoaderStatus) {
                // Poll the job status
                const interval = setInterval(() => {
                    fetch('/job-status')
                        .then((response) => response.json())
                        .then((statusData) => {
                            
                            statusData.ids.forEach(id => {
                                const loadingRow = document.getElementById(`loading-row-${id}`);

                                if (statusData.status === "finished"){
                                    print("Job is finished!");
                                    loadingRow.style.display = "none";
                                    alert("Job is finished");
                                    clearInterval(interval);
                                    fetch('/clear-loader-flag', { method: 'POST' });
                                    window.location.reload();
    
                                } else if (statusData.status === "failed"){
                                    
                                    loadingRow.style.display = "none"; // Hide the loading row
                                    alert("The job failed. Please try again.");
                                    clearInterval(interval);
                                    fetch('/clear-loader-flag', { method: 'POST' });
                                    window.location.reload();
    
                                } else if (statusData.status === "in-progress"){
    
                                    // Show the loading row
                                    loadingRow.style.display = "table-row";
                                }
                            });
                        })
                    .catch(err => {
                        console.error("Error fetching job status", err)
                        clearInterval(interval)
                    });
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