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
});
