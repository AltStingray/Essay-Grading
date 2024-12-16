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

window.addEventListener("DOMContentLoaded", () => {

    const loadingRow = document.getElementById('submit-btn');

    if (loadingRow) {
        loadingRow.addEventListener('click');
    }
    else {
        console.error("submit-btn element not found in the DOM!");
    }

    loadingRow.style.display = "table-row";

    // Poll the job status
    const interval = setInterval(() => {
        fetch('/job-status')
            .then(response => response.json())
            .then(statusData => {
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
            })
    }, 1000);
});