document.addEventListener("DOMContentLoaded", () => {
    const menuToggle = document.querySelector(".menu-toggle");
    const navMenu = document.querySelector(".nav-menu");

    if (menuToggle && navMenu) {
        const menuIcon = menuToggle.querySelector("i");
        const menuLinks = navMenu.querySelectorAll("a");
        let lockedScrollY = 0;

        const lockScroll = () => {
            lockedScrollY = window.scrollY || window.pageYOffset || 0;
            document.body.classList.add("menu-open");
            document.documentElement.classList.add("menu-open");
            document.body.style.position = "fixed";
            document.body.style.top = `-${lockedScrollY}px`;
            document.body.style.left = "0";
            document.body.style.right = "0";
            document.body.style.width = "100%";
        };

        const unlockScroll = () => {
            document.body.classList.remove("menu-open");
            document.documentElement.classList.remove("menu-open");
            document.body.style.position = "";
            document.body.style.top = "";
            document.body.style.left = "";
            document.body.style.right = "";
            document.body.style.width = "";
            window.scrollTo(0, lockedScrollY);
        };

        const setMenuState = (isOpen) => {
            navMenu.classList.toggle("active", isOpen);

            if (menuIcon) {
                menuIcon.classList.toggle("fa-bars", !isOpen);
                menuIcon.classList.toggle("fa-xmark", isOpen);
            }

            menuToggle.classList.toggle("is-open", isOpen);
            menuToggle.setAttribute("aria-label", isOpen ? "Fechar menu" : "Abrir menu");
            menuToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");

            if (isOpen) {
                lockScroll();
            } else {
                unlockScroll();
            }
        };

        menuToggle.addEventListener("click", () => {
            const isOpen = !navMenu.classList.contains("active");
            setMenuState(isOpen);
        });

        menuLinks.forEach(link => {
            link.addEventListener("click", () => {
                if (navMenu.classList.contains("active")) {
                    setMenuState(false);
                }
            });
        });

        window.addEventListener("resize", () => {
            if (window.innerWidth > 992 && navMenu.classList.contains("active")) {
                setMenuState(false);
            }
        });
    }

    const promptInput = document.getElementById("prompt-input");
    const suggestionButtons = document.querySelectorAll(".suggestion-chip[data-prompt]");

    suggestionButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const prompt = button.dataset.prompt || "";
            if (promptInput) {
                promptInput.value = prompt;
                promptInput.focus();
            }
        });
    });

    const swatch = document.getElementById("color-preview-swatch");
    const nameNode = document.getElementById("color-preview-name");
    const colorInputs = document.querySelectorAll('input[name="color"]');

    const colorMap = {
        preto: { name: "Preto", value: "#111827" },
        branco: { name: "Branco", value: "#f8fafc" },
        vinho: { name: "Vinho", value: "#6d1830" },
    };

    const renderColorPreview = () => {
        const selected = document.querySelector('input[name="color"]:checked');
        const selectedValue = selected ? selected.value : "preto";
        const colorData = colorMap[selectedValue] || colorMap.preto;

        if (swatch) {
            swatch.style.background = colorData.value;
            swatch.style.boxShadow = selectedValue === "branco"
                ? "inset 0 0 0 1px rgba(17,24,39,0.25)"
                : "inset 0 0 0 1px rgba(255,255,255,0.2)";
        }

        if (nameNode) {
            nameNode.textContent = colorData.name;
        }
    };

    colorInputs.forEach((input) => {
        input.addEventListener("change", renderColorPreview);
    });

    renderColorPreview();
});
