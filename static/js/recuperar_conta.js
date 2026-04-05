// recuperar_conta.js - Gerenciamento de estados e UX do card de recuperação

document.addEventListener('DOMContentLoaded', () => {
    const recoveryForm = document.getElementById('recovery-form');
    const submitBtn = document.getElementById('submit-btn');
    const submitOverlay = document.getElementById('submit-overlay');
    const emailInput = document.getElementById('email-input');
    const tryAgainBtn = document.getElementById('try-again-btn');
    const retryBtn = document.getElementById('retry-btn');
    const card = document.getElementById('recovery-card');

    // Estados do card
    const states = {
        form: document.getElementById('state-form'),
        success: document.getElementById('state-success'),
        error: document.getElementById('state-error')
    };

    /**
     * Muda para um estado específico com transição suave
     */
    function changeState(newState) {
        Object.keys(states).forEach(key => {
            if (key === newState) {
                states[key].removeAttribute('hidden');
            } else {
                states[key].setAttribute('hidden', '');
            }
        });

        // Scroll suave para o topo do card se em mobile
        if (window.innerWidth < 768) {
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    /**
     * Mostra spinner no botão durante o envio
     */
    function showSpinner(show = true) {
        const btnText = submitBtn.querySelector('.btn-text');
        const btnSpinner = submitBtn.querySelector('.btn-spinner');

        if (show) {
            submitBtn.disabled = true;
            submitOverlay.removeAttribute('hidden');
            btnText.setAttribute('hidden', '');
            btnSpinner.removeAttribute('hidden');
        } else {
            submitBtn.disabled = false;
            submitOverlay.setAttribute('hidden', '');
            btnText.removeAttribute('hidden');
            btnSpinner.setAttribute('hidden', '');
        }
    }

    /**
     * Exibe mensagem de erro na forma
     */
    function showFormError(message) {
        let errorEl = document.getElementById('error-msg');

        if (!errorEl) {
            errorEl = document.createElement('p');
            errorEl.className = 'form-error';
            errorEl.id = 'error-msg';
            states.form.querySelector('.recovery-header').after(errorEl);
        }

        errorEl.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>${message}</span>
        `;

        // Anima entrada
        errorEl.style.animation = 'fadeIn 0.3s ease-out';
    }

    /**
     * Limpa mensagens de erro da forma
     */
    function clearFormError() {
        const errorEl = document.getElementById('error-msg');
        if (errorEl) {
            errorEl.remove();
        }
    }

    /**
     * Submete o formulário com validação
     */
    recoveryForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = emailInput.value.trim().toLowerCase();

        // Validação básica
        if (!email) {
            showFormError('Informe seu e-mail para continuar.');
            return;
        }

        if (!isValidEmail(email)) {
            showFormError('E-mail inválido. Verifique e tente novamente.');
            return;
        }

        clearFormError();
        showSpinner(true);

        try {
            const response = await fetch(recoveryForm.action || window.location.pathname, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams(new FormData(recoveryForm))
            });

            await response.text();

            // Se recebeu sucesso (redirecionamento ou resposta bem-sucedida)
            if (response.ok) {
                // Atualiza email no estado de sucesso
                document.getElementById('success-email').textContent = email;
                showSpinner(false);
                changeState('success');
            } else {
                // Mostra erro genérico
                showFormError('Erro ao processar sua solicitação. Tente novamente.');
                showSpinner(false);
            }
        } catch (error) {
            console.error('Erro na requisição:', error);
            showFormError('Erro de conexão. Verifique sua internet e tente novamente.');
            showSpinner(false);
        }
    });

    /**
     * Botão "Tentar outro e-mail" (volta para o form)
     */
    if (tryAgainBtn) {
        tryAgainBtn.addEventListener('click', () => {
            emailInput.value = '';
            emailInput.focus();
            showSpinner(false);
            changeState('form');
        });
    }

    /**
     * Botão "Tentar novamente" (volta para o form)
     */
    if (retryBtn) {
        retryBtn.addEventListener('click', () => {
            emailInput.value = '';
            emailInput.focus();
            changeState('form');
        });
    }

    /**
     * Validação simples de email
     */
    function isValidEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    }

    /**
     * Validação em tempo real do input
     */
    emailInput.addEventListener('input', () => {
        clearFormError();
    });

    /**
     * Enter key para submeter
     */
    emailInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            recoveryForm.dispatchEvent(new Event('submit'));
        }
    });

    /**
     * Detecta se o servidor respondeu com sucesso ou erro
     * (Para quando a página foi carregada com success/error message)
     */
    function checkInitialState() {
        const notice = document.querySelector('.form-notice');
        const error = document.querySelector('.form-error');

        if (notice) {
            // Sucesso
            changeState('success');
        } else if (error && error.textContent.includes('Informe')) {
            // Erro específico
            showFormError(error.textContent);
        }
    }

    // Verifica estado inicial
    // checkInitialState(); // Descomente se necessário

    // Animação de entrada suave
    const reveal = card.classList.contains('reveal-init');
    if (reveal) {
        card.style.animation = 'fadeIn 0.5s ease-out';
    }

    // Acessibilidade: Foco automático no input email
    setTimeout(() => {
        emailInput.focus();
    }, 300);
});
