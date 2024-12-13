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
    document.getElementById("submit-btn").addEventListener("click", () => {
        // Show the loading row
        const loadingRow = document.getElementById('submit-btn');
        loadingRow.style.display = "table-row";
        setTimeout(checkJobStatus, 5000);

        // Poll the job status
        function checkJobStatus(){
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
                    });
            }, 1000);
        }
    });
});