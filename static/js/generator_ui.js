document.addEventListener("DOMContentLoaded", () => {
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

    // Gerenciamento do Overlay de Carregamento Premium
    const generatorForm = document.querySelector(".generator-form");
    const loadingOverlay = document.getElementById("loading-overlay");

    if (generatorForm && loadingOverlay) {
        generatorForm.addEventListener("submit", () => {
            if (promptInput && promptInput.value.trim() !== "") {
                loadingOverlay.removeAttribute("hidden");

                const step1 = document.getElementById("step-1");
                const step2 = document.getElementById("step-2");
                const step3 = document.getElementById("step-3");

                // Transição Passo 1 -> Passo 2 (2.5s)
                setTimeout(() => {
                    if (step1 && step2) {
                        step1.classList.remove("active");
                        step1.classList.add("done");
                        step2.classList.add("active");
                    }
                }, 2500);

                // Transição Passo 2 -> Passo 3 (5.5s)
                setTimeout(() => {
                    if (step2 && step3) {
                        step2.classList.remove("active");
                        step2.classList.add("done");
                        step3.classList.add("active");
                    }
                }, 5500);
            }
        });
    }
});
