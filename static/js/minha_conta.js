// minha_conta.js - Lógica do Dashboard

document.addEventListener("DOMContentLoaded", async () => {
    const accountUsername = document.getElementById("account-username");
    const accountEmail = document.getElementById("account-email");
    const accountId = document.getElementById("account-id");
    const totalDesigns = document.getElementById("account-total-designs");
    const recentCount = document.getElementById("account-recent-count");
    const recentDesigns = document.getElementById("recent-designs");
    const errorBox = document.getElementById("account-error");

    const showError = (message) => {
        errorBox.hidden = false;
        errorBox.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`;
        errorBox.style.display = 'flex'; // Alinha ícone com texto
    };

    try {
        const response = await fetch("/api/minha-conta", {
            headers: {
                "Accept": "application/json"
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = "/login?next=/minha-conta";
                return;
            }
            throw new Error("Não foi possível carregar os dados da conta.");
        }

        const data = await response.json();

        accountUsername.textContent = data.user?.username || "Sem usuário";
        accountEmail.textContent = data.user?.email || "Sem e-mail";
        accountId.textContent = data.user?.id ?? "-";
        totalDesigns.textContent = data.stats?.total_designs ?? 0;
        recentCount.textContent = data.stats?.recent_designs_count ?? 0;

        const designs = data.recent_designs || [];
        if (designs.length === 0) {
            recentDesigns.innerHTML = `
                <div style="text-align: center; padding: 40px 20px; width: 100%; grid-column: 1 / -1; border: 1px dashed rgba(255,255,255,0.2); border-radius: 12px;">
                    <i class="fas fa-ghost" style="font-size: 2.5rem; color: rgba(255,255,255,0.2); margin-bottom: 15px;"></i>
                    <p style="color: rgba(255,255,255,0.6);">Nenhuma estampa criada ainda. A tela em branco aguarda sua ideia!</p>
                </div>
            `;
            return;
        }

        // Renderiza os cards da galeria
        recentDesigns.innerHTML = designs
            .map((design) => {
                const prompt = design.prompt || "Sem prompt";
                const color = design.color || "Preto";
                
                return `
                    <a class="account-list-item" href="/preview/${design.id}">
                        <img src="${design.image_url}" alt="Design ${design.id}" loading="lazy" />
                        <div>
                            <strong>Arte #${design.id}</strong>
                            <p title="${prompt}">"${prompt}"</p>
                            <span class="item-badge"><i class="fas fa-tshirt"></i> ${color}</span>
                        </div>
                        <i class="fas fa-chevron-right" style="color: rgba(255,255,255,0.2); margin-left: auto;"></i>
                    </a>
                `;
            })
            .join("");
            
    } catch (error) {
        recentDesigns.innerHTML = ""; // Limpa o loader se der erro
        showError(error.message || "Erro inesperado ao carregar sua conta.");
    }
});