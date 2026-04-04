document.addEventListener("DOMContentLoaded", () => {
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
