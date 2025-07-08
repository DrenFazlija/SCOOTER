/* displayed value can't get update otherwise */
document.documentElement.classList.add("js");

const continueButton = document.getElementById("continue-button");

document.getElementById("slider-form").addEventListener("input", (e) => {
  let _t = e.target;
  _t.parentNode.style.setProperty("--val", _t.value);
  const output = _t.parentNode.querySelector("output");
  output.textContent = getCustomText(parseInt(_t.value)); // Update output with custom text
  output.style.display = "block";

  if (_t.value == randomNumber) {
    continueButton.classList.add("unlocked");
    continueButton.removeAttribute("disabled");
  } else {
    continueButton.classList.remove("unlocked");
    continueButton.setAttribute("disabled", "true");
  }
});

function getCustomText(value) {
  if (value < 0) return "I'm " + Math.abs(value) + "% sure it's MODIFIED";
  if (value > 0) return "I'm " + value + "% sure it's REAL";

  return "I don't know";
}

/*Randomly choose a prime number number smaller than 100*/
function getRandomPrime() {
  const primes = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
    73, 79, 83, 89, 97,
  ];
  /*Randomly decide on positive or negative number*/
  if (Math.random() < 0.5) {
    return -primes[Math.floor(Math.random() * primes.length)];
  }
  return primes[Math.floor(Math.random() * primes.length)];
}

function operationTestText(randomNumber) {
  if (randomNumber < 0) {
    return "I'm " + Math.abs(randomNumber) + "% sure it's MODIFIED";
  }
  if (randomNumber > 0) {
    return "I'm " + randomNumber + "% sure it's REAL";
  }
}
