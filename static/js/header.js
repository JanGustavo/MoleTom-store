// ============================================================================
// Header Menu Toggle - Componente centralizado para menu mobile responsivo
// ============================================================================

/**
 * Gerencia o estado do scroll quando o menu está aberto
 * Impede scroll do body mantendo a posição visual
 */
function lockScroll() {
  const scrollY = window.scrollY || document.documentElement.scrollTop;
  document.body.style.position = "fixed";
  document.body.style.top = `-${scrollY}px`;
  document.body.style.left = "0";
  document.body.style.right = "0";
  document.body.dataset.scrollY = scrollY;
}

/**
 * Restaura o scroll normal
 */
function unlockScroll() {
  const scrollY = parseInt(document.body.dataset.scrollY) || 0;
  document.body.style.position = "";
  document.body.style.top = "";
  document.body.style.left = "";
  document.body.style.right = "";
  window.scrollTo(0, scrollY);
}

/**
 * Define o estado do menu (aberto ou fechado)
 * @param {boolean} isOpen - true para abrir, false para fechar
 */
function setMenuState(isOpen) {
  const navMenu = document.querySelector(".nav-menu");
  const menuToggle = document.querySelector(".menu-toggle");
  const menuIcon = menuToggle.querySelector("i");

  if (isOpen) {
    navMenu.classList.add("active");
    menuToggle.classList.add("is-open");
    menuIcon.className = "fas fa-xmark";
    lockScroll();
  } else {
    navMenu.classList.remove("active");
    menuToggle.classList.remove("is-open");
    menuIcon.className = "fas fa-bars";
    unlockScroll();
  }
}

/**
 * Inicializa o header menu toggle
 * Deve ser chamado quando o DOM está pronto
 */
function initHeaderMenu() {
  const menuToggle = document.querySelector(".menu-toggle");
  const navMenu = document.querySelector(".nav-menu");

  if (!menuToggle || !navMenu) {
    console.warn("Menu toggle ou nav-menu não encontrados");
    return;
  }

  // Getter para estado atual do menu
  const isMenuOpen = () => navMenu.classList.contains("active");

  // Click no botão toggle
  menuToggle.addEventListener("click", (e) => {
    e.preventDefault();
    setMenuState(!isMenuOpen());
  });

  // Clique em um link do menu fecha o menu
  const navLinks = navMenu.querySelectorAll(".nav-link");
  navLinks.forEach((link) => {
    link.addEventListener("click", () => {
      setMenuState(false);
    });
  });

  // Clique no profile-pill também fecha o menu
  const profilePill = navMenu.querySelector(".profile-pill");
  if (profilePill) {
    profilePill.addEventListener("click", () => {
      setMenuState(false);
    });
  }

  // Esc fecha o menu
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && isMenuOpen()) {
      setMenuState(false);
    }
  });

  // Clique fora do menu fecha o menu
  document.addEventListener("click", (e) => {
    const isClickInsideMenu = navMenu.contains(e.target);
    const isClickOnToggle = menuToggle.contains(e.target);

    if (!isClickInsideMenu && !isClickOnToggle && isMenuOpen()) {
      setMenuState(false);
    }
  });

  // Redimensionar janela fecha o menu
  window.addEventListener("resize", () => {
    if (window.innerWidth >= 992 && isMenuOpen()) {
      setMenuState(false);
    }
  });
}

// Inicializar quando o DOM está pronto
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initHeaderMenu);
} else {
  initHeaderMenu();
}
