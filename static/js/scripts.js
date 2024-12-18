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

document.getElementById("submit-btn").addEventListener("click", () => {
    fetch("/loader-status")
        .then(response => response.json())
        .then(data => {
            const showLoader = data.show_loader;
            if (showLoader){
                startLoader()
            }
        })
});

function startLoader(){
    // Show the loading row
    const loadingRow = document.getElementById('loading-row');
    loadingRow.style.display = "table-row";
    
    // Poll the job status
    console.log("Polling the job status!");
    const interval = setInterval(() => {
    fetch('/job-status')
        .then((response) => response.json())
        .then((statusData) => {
            if (statusData.status === "finished"){
                clearInterval(interval); // Stop polling
                window.location.reload();
            } else if (statusData.status === "failed"){
                clearInterval(interval);
                alert("The job failed. Please try again.");
                loadingRow.style.display = "none"; // Hide the loading row
            }
        })
        .catch(error => {
            console.error("Error checking job status:", error);
            clearInterval(interval)
            loadingRow.style.display = "none";
        });
    }, 1000); // Polling interval of 1 second
};


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