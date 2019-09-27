const floating_menu = document.querySelector(".js-floating-menu");
//console.log(file_url);

//& ----encode----> &amp;
//&amp; ----decode----> &
function init() {
    floating_menu.style.backgroundImage = "url(" + decodeHtml(file_url) + ")";
    floating_menu.style.backgroundRepeat = "no-repeat";
    floating_menu.style.backgroundSize = "cover";
}

//출처: https://gomakethings.com/decoding-html-entities-with-vanilla-javascript/
function decodeHtml(html) {
    var txt = document.createElement("textarea");
    txt.innerHTML = html;
    return txt.value;
}

init();
