// header_scroll.js - Estado visual do header ao rolar a página

document.addEventListener("DOMContentLoaded", () => {
    const headers = document.querySelectorAll(".sticky-header");
    if (!headers.length) {
        return;
    }

    const applyState = () => {
        const isScrolled = window.scrollY > 8;
        headers.forEach((header) => {
            header.classList.toggle("scrolled", isScrolled);
        });
    };

    applyState();
    window.addEventListener("scroll", applyState, { passive: true });
});
