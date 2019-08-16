// Get the modal
console.log(num);
const modal = document.getElementById("js-delete-modal"+num);

// Get the button that opens the modal
const btn = document.querySelectorAll(".js-post-delete-button");

// Get the yes/no button
const btn_yes = document.getElementsByClassName("js-modal-button-yes")[0];
const btn_no = document.getElementsByClassName("js-modal-button-no")[0];

// Get the (x) element that closes the modal
const btn_close = document.getElementsByClassName("js-modal-close")[0];

// When the user clicks the button, open the modal 
btn[1].onclick = function() {
  modal.style.display = "block";
}

// Close the modal -------------------------------------------------------
// When the user clicks on (no), close the modal
btn_no.onclick = function() {
  modal.style.display = "none";
}

// When the user clicks on (x), close the modal
btn_close.onclick = function() {
  modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
}
