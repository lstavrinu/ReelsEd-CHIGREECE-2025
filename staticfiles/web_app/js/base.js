// base.js

document.addEventListener("DOMContentLoaded", () => {
    console.log("Base JavaScript loaded!");

    // Configure Toastr options
    toastr.options = {
        closeButton: true,
        progressBar: true,
        positionClass: "toast-top-right",
        timeOut: 5000
    };
});

// Function to show toast messages globally
function showToast(message, type = "success") {
    toastr[type](message);
}

// Handle global AJAX errors
$(document).ajaxError(function (event, jqxhr, settings, thrownError) {
    try {
        let response = JSON.parse(jqxhr.responseText);
        console.error("AJAX Error:", response);

        if (response.errors) {
            let errorMessage = response.errors.join("<br>");
            showToast(errorMessage, "error");
        } else {
            showToast("An unexpected error occurred.", "error");
        }
    } catch (e) {
        console.error("Unknown error:", e);
        showToast("An unknown error occurred.", "error");
    }
});

// Function to send AJAX requests with error handling
function sendAjaxRequest(url, data, successCallback) {
    console.log("Sending AJAX request to:", url);
    console.log("Data:", data);

    $.ajax({
        type: "POST",
        url: url,
        data: data,
        dataType: "json",
        success: function (response) {
            console.log("Success:", response);
            if (response.success) {
                showToast(response.message, "success");
                if (successCallback) successCallback(response);
            } else {
                showToast(response.message || "Something went wrong!", "error");
            }
        },
        error: function (xhr) {
            let errorData = JSON.parse(xhr.responseText);
            console.error("Error:", errorData);

            let errorMessage = errorData.errors ? errorData.errors.join("<br>") : "An error occurred.";
            showToast(errorMessage, "error");
        }
    });
}

// Function to fetch JSON responses and show toast messages
function fetchJson(url, successCallback) {
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast(data.message, "success");
                if (successCallback) successCallback(data);
            } else {
                showToast(data.message || "Something went wrong!", "error");
            }
        })
        .catch(error => {
            console.error("Fetch Error:", error);
            showToast("An error occurred while processing your request.", "error");
        });
}
