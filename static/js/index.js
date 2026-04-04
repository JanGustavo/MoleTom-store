// index.js - Interatividade e Animações MoleTom

document.addEventListener("DOMContentLoaded", () => {
    // 1. Animação de Entrada (Reveal on Scroll)
    const revealOnScroll = (entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("revealed");
                // Adiciona um pequeno delay para itens em grid
                if (entry.target.parentElement.classList.contains("tools-grid") || 
                    entry.target.parentElement.classList.contains("personalization-grid") ||
                    entry.target.parentElement.classList.contains("trust-grid")) {
                    const index = Array.from(entry.target.parentElement.children).indexOf(entry.target);
                    entry.target.style.transitionDelay = `${index * 0.1}s`;
                }
                observer.unobserve(entry.target);
            }
        });
    };

    const observerOptions = {
        root: null,
        threshold: 0.15,
        rootMargin: "0px 0px -50px 0px"
    };

    const observer = new IntersectionObserver(revealOnScroll, observerOptions);

    // Seleciona elementos para animar
    const animateElements = document.querySelectorAll(".glass-card, .hero-content, .hero-mockup, .header-dashboard, .trust-bar-section, .about-us-section, .cta-section");
    animateElements.forEach(el => {
        el.classList.add("reveal-init");
        observer.observe(el);
    });

    // 2. Efeito de Parallax Suave no Hero Mockup
    const heroMockup = document.querySelector(".hero-mockup");
    if (heroMockup) {
        window.addEventListener("mousemove", (e) => {
            const x = (window.innerWidth / 2 - e.pageX) / 50;
            const y = (window.innerHeight / 2 - e.pageY) / 50;
            heroMockup.style.transform = `translate(${x}px, ${y}px)`;
        });
    }

    // 3. Adiciona Estilos de Animação Dinamicamente
    const style = document.createElement("style");
    style.innerHTML = `
        .reveal-init {
            opacity: 0;
            transform: translateY(30px);
            transition: opacity 0.8s cubic-bezier(0.2, 0.8, 0.2, 1), 
                        transform 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
        }
        .revealed {
            opacity: 1;
            transform: translateY(0);
        }
        .hero-content.reveal-init {
            transform: translateX(-30px);
        }
        .hero-content.revealed {
            transform: translateX(0);
        }
        .hero-mockup.reveal-init {
            transform: translateX(30px);
        }
        .hero-mockup.revealed {
            transform: translateX(0);
        }
    `;
    document.head.appendChild(style);

    // 4. Feedback Visual nos Botões de Compra
    const buyButtons = document.querySelectorAll(".buy-button");
    buyButtons.forEach(btn => {
        btn.addEventListener("click", (e) => {
            const originalContent = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';
            btn.style.pointerEvents = "none";
            
            // Simula um delay de processamento antes de redirecionar (opcional)
            setTimeout(() => {
                // O link natural do <a> cuidará do redirecionamento se houver href
            }, 1000);
        });
    });

    // 5. Toggle do Menu Mobile
    const menuToggle = document.querySelector(".menu-toggle");
    const navMenu = document.querySelector(".nav-menu");

    if (menuToggle && navMenu) {
        menuToggle.addEventListener("click", () => {
            navMenu.classList.toggle("active");
            menuToggle.querySelector("i").classList.toggle("fa-bars");
            menuToggle.querySelector("i").classList.toggle("fa-times");
        });
    }
});