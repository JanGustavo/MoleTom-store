document.addEventListener("DOMContentLoaded", () => {
    const copyBtn = document.getElementById("copy-community-link");
    const submitBtn = document.getElementById("submit-community-design");
    const feedback = document.getElementById("community-feedback");

    const showFeedback = (message, isError = false) => {
        if (!feedback) {
            return;
        }
        feedback.hidden = false;
        feedback.textContent = message;
        feedback.style.borderColor = isError ? "rgba(255, 82, 82, 0.22)" : "rgba(0, 188, 212, 0.2)";
        feedback.style.background = isError ? "rgba(255, 82, 82, 0.08)" : "rgba(0, 188, 212, 0.08)";
    };

    if (copyBtn) {
        copyBtn.addEventListener("click", async () => {
            const url = copyBtn.dataset.url || window.location.href;
            try {
                await navigator.clipboard.writeText(url);
                showFeedback("Link da comunidade copiado para a área de transferência.");
            } catch (_) {
                showFeedback("Não foi possível copiar automaticamente. Copie manualmente: " + url, true);
            }
        });
    }

    if (submitBtn) {
        submitBtn.addEventListener("click", async () => {
            const designId = Number(submitBtn.dataset.designId || 0);
            const titleInput = document.getElementById("community-title");
            const captionInput = document.getElementById("community-caption");
            const title = (titleInput?.value || "").trim();
            const caption = (captionInput?.value || "").trim();

            if (!designId) {
                showFeedback("Design inválido para envio.", true);
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';

            try {
                const response = await fetch("/api/comunidade/enviar", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    body: JSON.stringify({
                        design_id: designId,
                        title,
                        caption,
                    }),
                });

                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || "Falha ao enviar para curadoria.");
                }

                showFeedback(data.message || "Enviado para curadoria com sucesso.");
                setTimeout(() => window.location.reload(), 900);
            } catch (error) {
                showFeedback(error.message || "Erro ao enviar para comunidade.", true);
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Enviar para Curadoria';
            }
        });
    }
});
