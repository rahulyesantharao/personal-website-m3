function toggleClass(s,e){var a,l=document.getElementById(s);l.classList?l.classList.toggle(e):(0<=(s=(a=l.className.split(" ")).indexOf(e))?a.splice(s,1):a.push(e),l.className=a.join(" "))}function toggleMenu(){toggleClass("navbar-menu-drawer","is-active"),toggleClass("navbar-burger","is-active"),toggleClass("sidenav-overlay","is-active")}