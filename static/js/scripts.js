console.log("Javascript is loaded and running!") // Test

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

console.log(document.getElementById("submit-btn"));

document.addEventListener("DOMContentLoaded", () => {
    const submitButton = document.getElementById("submit-btn");
    const loadingRow = document.getElementById('loading-row'); // Replace with correct ID for the loading row
    
    // Check if elements exist
    if (!submitButton || !loadingRow) {
        console.error("Required elements (submit button or loading row) are missing from the DOM.");
        return;
    }

    submitButton.addEventListener("click", () => {
        // Show the loading row
        loadingRow.style.display = "table-row";

        // Wait 5 seconds before starting polling
        setTimeout(checkJobStatus, 5000);
    });

    // Function to check job status
    function checkJobStatus() {
        const interval = setInterval(() => {
            fetch('/job-status')
                .then(response => response.json())
                .then(statusData => {
                    if (statusData.status === "finished") {
                        clearInterval(interval); // Stop polling
                        window.location.reload();
                    } else if (statusData.status === "failed") {
                        clearInterval(interval);
                        alert("The job failed. Please try again.");
                        loadingRow.style.display = "none"; // Hide the loading row
                    }
                })
                .catch(error => {
                    console.error("Error checking job status:", error);
                    clearInterval(interval);
                    loadingRow.style.display = "none";
                });
        }, 1000);
    }
});