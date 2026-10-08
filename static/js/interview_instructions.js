let count = 20;

const countdownNumber =
    document.getElementById("countdownNumber");

const startingText =
    document.getElementById("startingText");

const countdownTimer = setInterval(function () {

    count--;

    countdownNumber.textContent = count;

    if (count <= 0) {

        clearInterval(countdownTimer);

        startingText.textContent =
            "Starting interview...";

        // Start the interview
        window.location.href = "/interview";
    }

}, 1000);