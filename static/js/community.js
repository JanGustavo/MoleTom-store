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

    const voteButtons = document.querySelectorAll(".vote-btn");

    voteButtons.forEach((button) => {
        button.addEventListener("click", async () => {
            const entryId = button.dataset.entryId;
            if (!entryId) {
                return;
            }

            button.disabled = true;
            const originalHtml = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Votando...';

            try {
                const response = await fetch(`/api/comunidade/votar/${entryId}`, {
                    method: "POST",
                    headers: {
                        Accept: "application/json",
                    },
                });

                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || "Não foi possível registrar o voto.");
                }

                const countNode = document.getElementById(`vote-count-${entryId}`);
                if (countNode) {
                    countNode.textContent = `${data.votes_count} votos`;
                }

                button.innerHTML = '<i class="fas fa-check"></i> Voto registrado';
            } catch (error) {
                button.disabled = false;
                button.innerHTML = originalHtml;
                window.alert(error.message || "Erro ao votar.");
            }
        });
    });
});
