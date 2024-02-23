document.getElementById("plus-btn").onclick = function() {
    var menu = document.getElementById("menu-content");
    if (menu.style.display === "block") {
        menu.style.display = "none";
    } else {
        menu.style.display = "block";
    }
}