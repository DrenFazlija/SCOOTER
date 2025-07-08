/* displayed value can't get update otherwise */
document.documentElement.classList.add("js");
const finishStudyButton = document.getElementById("finish-study");

document.getElementById("slider-form").addEventListener("input", (e) => {
  let _t = e.target;
  _t.parentNode.style.setProperty("--val", _t.value);
  const output = _t.parentNode.querySelector("output");
  output.textContent = getCustomText(parseInt(_t.value)); // Update output with custom text
  output.style.display = "block";

  if (ratings[slideIndex - 1] === undefined) {
    numberOfRatings++;
    // Update the completion bar
    const completionPercentage = Math.round(
      (numberOfRatings / numberOfImages) * 100
    );
    updateCompletionBar(completionPercentage);
    updateDotColor(slideIndex - 1);

    if (numberOfRatings === numberOfImages) {
      finishStudyButton.classList.add("unlocked");
      finishStudyButton.removeAttribute("disabled");
      finishStudyButton.onclick = finishStudy;
      finishStudyButton.innerHTML = "Finish Study";
      const span = document.createElement("span");
      span.classList.add("material-symbols-outlined");
      span.innerHTML = "check_circle";
      finishStudyButton.append(span);
    }
  }
  ratings[slideIndex - 1] = _t.parentNode.style.getPropertyValue("--val");
  updateRatings();
});

function loadImageFromUrl(url, id) {
  jQuery.ajax({
    url: url,
    cache: false,
    xhr: function () {
      // Seems like the only way to get access to the xhr object
      var xhr = new XMLHttpRequest();
      xhr.responseType = "blob";
      return xhr;
    },
    success: function (data) {
      var img = document.getElementById(id);
      var url = window.URL || window.webkitURL;
      img.src = url.createObjectURL(data);
    },
    error: function () {},
  });
}

function getCustomText(value) {
  if (value < 0) return "I'm " + Math.abs(value) + "% sure it's MODIFIED";
  if (value > 0) return "I'm " + value + "% sure it's REAL";

  return "I don't know";
}

function resetSlider() {
  document.getElementById("r").value = 0;
  document.getElementById("slider-form").style.setProperty("--val", 0);
  document.querySelector("#slider-form > output").style.display = "none";

  displayPreviousInput();
}

function displayPreviousInput() {
  if (ratings[slideIndex - 1] !== undefined) {
    document.getElementById("r").value = ratings[slideIndex - 1];
    document
      .getElementById("slider-form")
      .style.setProperty("--val", ratings[slideIndex - 1]);
    document.querySelector("#slider-form > output").style.display = "block";
    document.querySelector("#slider-form > output").textContent = getCustomText(
      ratings[slideIndex - 1]
    );
  }
}

function finishStudy() {
  Swal.fire({
    title: "Are you sure?",
    text: "You won't be able to revert this!",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#3085d6",
    cancelButtonColor: "#d33",
    confirmButtonText: "Yes, I want to submit my answers!",
  }).then((result) => {
    if (result.isConfirmed) {
      returnTask();
    }
  });
}

function updateRatings() {
  // Make a fetch request to update the session parameter ratings
  fetch("/update-ratings", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ratings: ratings,
    }),
  })
  .then(response => {
    if (response.ok) {
      return response.json();
    }
    throw new Error('Failed to update ratings: Server responded with status ' + response.status);
  })
  .then(data => {
    if (data.message === "Ratings updated successfully!") {
      console.log("Ratings successfully updated in the session.");
    } else {
      console.error("Failed to update ratings in the session.");
    }
  })
  .catch(error => console.error('Error:', error));
}

function updateImageIndex() {
  // Make a fetch request to update the session parameter imageIndex
  fetch("/update-image-index", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      imageIndex: slideIndex,
    }),
  })
  .then(response => {
    if (response.ok) {
      return response.json();
    }
    throw new Error('Failed to update image index: Server responded with status ' + response.status);
  })
  .then(data => {
    if (data.message === "Image index updated successfully!") {
      console.log("Image index successfully updated in the session.");
    } else {
      console.error("Failed to update image index in the session.");
    }
  })
  .catch(error => console.error('Error:', error));
}
