function toggleClass(element_id, class_name) {
    var element = document.getElementById(element_id);
    if(element.classList) {
        element.classList.toggle(class_name);
    } else { // IE9
        var classes = element.className.split(" ");
        var i = classes.indexOf(class_name);

        if(i >= 0) classes.splice(i, 1);
        else classes.push(class_name);

        element.className = classes.join(" ");
    }
}

function toggleMenu() {
    toggleClass("navbar-menu-drawer", "is-active");
    toggleClass("navbar-burger", "is-active");
}