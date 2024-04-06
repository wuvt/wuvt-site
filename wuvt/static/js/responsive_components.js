const side = document.querySelector("#side");
const hamburger = document.querySelector("#hamburger");
function toggleMenu() {
    if (side.classList.contains("showMenu")) {
        side.classList.remove("showMenu");
    } else {
        side.classList.add("showMenu");
        }
}
hamburger.addEventListener("click", toggleMenu);
function menuItemsToggleListeners() {
    const sideItems = document.querySelectorAll("#side_primary ul li a"); 
    sideItems.forEach( 
        function(sideItem) { 
            sideItem.addEventListener("click", toggleMenu);
        }
    )
}
menuItemsToggleListeners();
hamburger.addEventListener("click", menuItemsToggleListeners);

function disableButton() {
    const volume_btn = document.getElementById("volume_btn");
    if (window.innerWidth <= 810) {
        volume_btn.disabled = true;
        volume_btn.children.item(0).setAttribute("class", "glyphicon glyphicon-remove");
    }
    else {
        volume_btn.removeAttribute("disabled");
        volume_btn.children.item(0).setAttribute("class", "glyphicon glyphicon-volume-down");
    }
}
window.addEventListener('DOMContentLoaded', function() {
    disableButton();
    window.addEventListener('resize', disableButton);
});
