const floating_menu = document.querySelector(".js-floating-menu");
//console.log(file_name);
function init() {
    floating_menu.style.backgroundImage = "url(" + file_name + ")";
    floating_menu.style.backgroundRepeat = "no-repeat";
    floating_menu.style.backgroundSize = "cover";
}

init();
