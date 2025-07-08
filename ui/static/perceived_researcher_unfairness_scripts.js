// Function to open the popup
function openPopup(popup_id) {
  return function () {
    document.getElementById(popup_id).style.display = "block";
  };
}

// Function to close the popup
function closePopup(popup_id) {
  return function () {
    document.getElementById(popup_id).style.display = "none";
  };
}

function clickReturnTask() {
  Swal.fire({
    title: "Are you sure?",
    text: "If you return the task, you will not be able to continue the study later on. However, you will still be compensated for your time up until now.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Yes, return the task!",
    cancelButtonText: "No, keep working",
    confirmButtonColor: "#3085d6",
    cancelButtonColor: "#d33",
  }).then((result) => {
    if (result.isConfirmed) {
      returnTask();
    }
  });
}

async function send_email() {
  const { value: formValues } = await Swal.fire({
    title: "Contact Researcher",
    html: `
      <style>
        .swal2-input, .swal2-textarea {
          width: 80%; /* Sets the width of inputs and text area to be the same */
          box-sizing: border-box; /* Includes padding and border in the element's total width and height */
        }
        .swal2-textarea {
          min-height: 100px; /* Sets a minimum height for the text area */
        }
        .swal-label {
          display: block; /* Ensures the label takes up the full width */
          text-align: center; /* Aligns the label text to the left */
          margin-top: 0.5em; /* Adds space above the label */
          margin-bottom: -5vh; /* Adds space below the label */
        }
        .swal2-html-container {
          align-items: flex-start; /* Aligns items to the start of the container */
        }
      </style>
      <div style="display: flex; flex-direction: column;">
        <input id="pid-swal2" class="swal2-input" placeholder="Enter your ID">

        <input id="subject-swal2" class="swal2-input" placeholder="Subject of your message">

        <textarea id="message-swal2" class="swal2-textarea" placeholder="Enter your message here"></textarea>
      </div>
    `,
    showCancelButton: true,
    confirmButtonText: "Yes, sent the message!",
    cancelButtonText: "No, cancel!",
    confirmButtonColor: "#3085d6",
    cancelButtonColor: "#d33",
    preConfirm: () => {
      return {
        pid: document.getElementById("pid-swal2").value,
        subject: document.getElementById("subject-swal2").value,
        message: document.getElementById("message-swal2").value,
      };
    },
  });

  if (formValues) {
    if (formValues["pid"] == "") {
      Swal.fire({
        title: "Sorry!",
        text: "Please enter your ID.",
        icon: "error",
      });
      return;
    } else if (formValues["subject"] == "") {
      Swal.fire({
        title: "Sorry!",
        text: "Please enter the subject of your message.",
        icon: "error",
      });
      return;
    } else if (formValues["message"] == "") {
      Swal.fire({
        title: "Sorry!",
        text: "Please enter your message.",
        icon: "error",
      });
      return;
    }
    setupEmail(JSON.stringify(formValues));
    return;
  }
}

/* Function to setup popup -- should be included in DOMContentLoaded event of a page */
function setupPopup() {
  var contactResearcherButton = document.getElementById("contact-researcher");
  contactResearcherButton.onclick = send_email;

  var returnTaskButton = document.getElementById("return-task");
  returnTaskButton.onclick = clickReturnTask;
}

function returnTask() {
  // Get the current site URL
  const current_site = window.location.pathname;
  to_be_parsed_ratings = null;
  if (current_site == "/main-study") {
    to_be_parsed_ratings = ratings;
  }

  logUrlAndTime();

  fetch("/study-completed", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      PROLIFIC_PID: prolificPid,
      RATINGS: to_be_parsed_ratings,
    }),
  })
    .then((response) => {
      if (response.ok) {
        return response.json(); // If OK, return the JSON
      } else {
        // If the server responds with a non-OK (error) status, handle it here
        return response.json().then((errorData) => {
          // Use the errorData to display a specific message or take action
          // console.error("Error from server:", errorData);
          throw new Error(`Server responded with status: ${response.status}`);
        });
      }
    })
    .then((data) => {
      if (data && data.status === "success") {
        // Clear the session storage by calling the python flask clear_session() function
        fetch("/clear-session", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ PROLIFIC_PID: prolificPid }),
        }).then((data) => {
          console.log("Session cleared");
          window.location.replace("/feedback?PROLIFIC_PID=" + prolificPid);
        })
        .catch((error) => {
          // Handle any error that occurred in any part of the code
          console.error("An unexpected error occurred:", error);
          // Optionally, redirect to a generic error page or display an error message
        });
      } else {
        // Handle any other status received in the data
        console.error("Error status received:", data.status);
      }
    })
    .catch((error) => {
      // Handle any error that occurred in any part of the code
      console.error("An unexpected error occurred:", error);
      // Optionally, redirect to a generic error page or display an error message
    });
}

function setupEmail(formValues) {
  fetch("/send_email", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: formValues,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        Swal.fire({
          title: "Thank you!",
          text: "The message was sent successfully.",
          icon: "success",
        });
      } else {
        Swal.fire({
          title: "Sorry!",
          text: "Sending the message failed. Please try again later.",
          icon: "error",
        });
      }
    })
    .catch((error) => {
      Swal.fire({
        title: "Sorry!",
        text: "An unexpected error occurred: " + error,
        icon: "error",
      });
    });
}

/*Standardized Code snippet to check alphanumeric string (only numbers and lowercase chars)*/
function isAlphaNumeric(str) {
  var code, i, len;

  for (i = 0, len = str.length; i < len; i++) {
    code = str.charCodeAt(i);
    if (
      !(code > 47 && code < 58) && // numeric (0-9)
      !(code > 96 && code < 123) // lower alpha (a-z)
    ) {
      return false;
    }
  }
  return true;
}

function logUrlAndTime() {
  const currentUrl = window.location.href;
  const pid = new URLSearchParams(window.location.search).get('PROLIFIC_PID');
  const currentTime = new Date().toISOString(); // ISO 8601 format

  console.log(`Current URL: ${currentUrl}`);
  console.log(`Current Time: ${currentTime}`);
  console.log(`Prolific PID: ${pid}`);

  // Send the data to the server
  fetch('/log', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json'
      },
      body: JSON.stringify({ url: currentUrl, time: currentTime, pid: pid})
  })
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
}

// Log URL and time on initial page load
document.addEventListener('DOMContentLoaded', logUrlAndTime);

// Log URL and time on back/forward navigation
window.addEventListener('popstate', logUrlAndTime);

// Log URL and time on hash change
window.addEventListener('hashchange', logUrlAndTime);

// Optionally, log URL and time on link clicks
document.addEventListener('click', (event) => {
  if (event.target.tagName === 'A' && event.target.href) {
      logUrlAndTime();
  }
});