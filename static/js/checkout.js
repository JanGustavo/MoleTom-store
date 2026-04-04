// checkout.js - ViaCEP e preenchimento automático do checkout

document.addEventListener("DOMContentLoaded", () => {
    const cepInput = document.getElementById("cep");
    const streetInput = document.getElementById("street");
    const districtInput = document.getElementById("district");
    const cityInput = document.getElementById("city");
    const stateInput = document.getElementById("state");
    const statusBox = document.getElementById("cep-status");

    if (!cepInput || !streetInput || !districtInput || !cityInput || !stateInput) {
        return;
    }

    const setStatus = (message, type = "info") => {
        if (!statusBox) {
            return;
        }

        statusBox.textContent = message;
        statusBox.dataset.state = type;
    };

    const clearAddress = () => {
        streetInput.value = "";
        districtInput.value = "";
        cityInput.value = "";
        stateInput.value = "";
    };

    const fillAddress = (data) => {
        streetInput.value = data.logradouro || "";
        districtInput.value = data.bairro || "";
        cityInput.value = data.localidade || "";
        stateInput.value = data.uf || "";
    };

    const lookupCep = async () => {
        const cep = cepInput.value.replace(/\D/g, "");

        if (cep.length !== 8) {
            return;
        }

        setStatus("Consultando endereço na ViaCEP...", "loading");
        clearAddress();

        try {
            const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
            if (!response.ok) {
                throw new Error("Falha ao consultar o CEP.");
            }

            const data = await response.json();
            if (data.erro) {
                clearAddress();
                setStatus("CEP não encontrado. Confira o número informado.", "error");
                return;
            }

            fillAddress(data);
            setStatus(`Endereço preenchido para ${data.localidade}/${data.uf}.`, "success");
        } catch (error) {
            clearAddress();
            setStatus("Não foi possível buscar o CEP agora. Tente novamente.", "error");
        }
    };

    let cepTimer;
    cepInput.addEventListener("input", () => {
        const cepDigits = cepInput.value.replace(/\D/g, "").slice(0, 8);
        cepInput.value = cepDigits.length > 5 ? `${cepDigits.slice(0, 5)}-${cepDigits.slice(5)}` : cepDigits;

        window.clearTimeout(cepTimer);
        if (cepDigits.length < 8) {
            clearAddress();
            setStatus("Digite o CEP completo para preencher o endereço.", "info");
            return;
        }

        cepTimer = window.setTimeout(lookupCep, 350);
    });

    cepInput.addEventListener("blur", lookupCep);

    if (cepInput.value.replace(/\D/g, "").length === 8) {
        lookupCep();
    }
});
