/* Rewrite this mess in a React format: Each event handler as part of a React component */
const sidebarDismiss = document.querySelector("#dismiss")
const sidebar = document.querySelector("#sidebar")
const overlay = document.querySelector(".overlay")
const sidebarExpand = document.querySelector("#sidebarExpand")

document.addEventListener("DOMContentLoaded", function() {
    /* -- Adding this to body breaks overlay scroll-through feature. Find a way to fix?
    OverlayScrollbars(document.querySelectorAll("body"), { });
    -- */

    /* Sidebar scrollbar needs to be shifted left */
    OverlayScrollbars(document.querySelector("#sidebar"), { });
    
    sidebarDismiss.addEventListener('click', function () {
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
    });
    overlay.addEventListener('click', function () {
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
    })
    sidebarExpand.addEventListener("click", function () {
        sidebar.classList.add('active');
        overlay.classList.add('active');
    });
});