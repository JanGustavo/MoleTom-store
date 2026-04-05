// redefinir_senha.js - Gerenciamento de validação de senha em tempo real

document.addEventListener('DOMContentLoaded', () => {
    const resetForm = document.getElementById('reset-form');
    const passwordInput = document.getElementById('password');
    const confirmInput = document.getElementById('confirm_password');
    const submitBtn = document.getElementById('submit-btn');
    const togglePassword = document.getElementById('toggle-password');
    const toggleConfirm = document.getElementById('toggle-confirm');
    const strengthFill = document.getElementById('strength-fill');
    const strengthText = document.getElementById('strength-text');
    const matchIndicator = document.getElementById('match-indicator');
    const matchError = document.getElementById('match-error');
    const card = document.getElementById('reset-card');

    // Estados
    const states = {
        form: document.getElementById('state-form'),
        success: document.getElementById('state-success')
    };

    /**
     * Calcula força da senha (0-100)
     */
    function calculateStrength(password) {
        let strength = 0;

        if (!password) return 0;

        // Comprimento
        if (password.length >= 8) strength += 20;
        if (password.length >= 12) strength += 10;
        if (password.length >= 16) strength += 10;

        // Maiúsculas
        if (/[A-Z]/.test(password)) strength += 15;

        // Minúsculas
        if (/[a-z]/.test(password)) strength += 15;

        // Números
        if (/[0-9]/.test(password)) strength += 15;

        // Caracteres especiais
        if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) strength += 15;

        return Math.min(strength, 100);
    }

    /**
     * Atualiza o indicador visual de força
     */
    function updateStrengthIndicator(password) {
        const strength = calculateStrength(password);
        const fill = strengthFill;
        const text = strengthText;

        fill.style.width = strength + '%';

        // Define cor e texto
        if (strength === 0) {
            text.textContent = 'Força da senha';
            text.className = 'strength-text';
        } else if (strength < 30) {
            fill.style.background = 'linear-gradient(90deg, #ef4444, #ef4444)';
            text.textContent = 'Muito fraca';
            text.className = 'strength-text weak';
        } else if (strength < 50) {
            fill.style.background = 'linear-gradient(90deg, #f97316, #f97316)';
            text.textContent = 'Fraca';
            text.className = 'strength-text fair';
        } else if (strength < 75) {
            fill.style.background = 'linear-gradient(90deg, #eab308, #eab308)';
            text.textContent = 'Boa';
            text.className = 'strength-text good';
        } else {
            fill.style.background = 'linear-gradient(90deg, #22c55e, #22c55e)';
            text.textContent = 'Forte';
            text.className = 'strength-text strong';
        }
    }

    /**
     * Atualiza requisitos
     */
    function updateRequirements(password) {
        const requirements = {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            number: /[0-9]/.test(password),
            special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)
        };

        // Atualiza visual dos requisitos
        document.querySelectorAll('.requirement').forEach(req => {
            const reqType = req.dataset.req;
            const isMet = requirements[reqType];
            const isOptional = reqType === 'number' || reqType === 'special';

            req.classList.remove('met', 'optional');

            if (isOptional) {
                req.classList.add('optional');
                if (isMet) {
                    req.classList.add('met');
                }
            } else {
                if (isMet) {
                    req.classList.add('met');
                }
            }
        });

        return requirements;
    }

    /**
     * Valida correspondência de senhas
     */
    function validateMatch() {
        const password = passwordInput.value;
        const confirm = confirmInput.value;

        if (!confirm) {
            matchIndicator.setAttribute('hidden', '');
            matchError.setAttribute('hidden', '');
            return false;
        }

        if (password === confirm && password) {
            matchIndicator.removeAttribute('hidden');
            matchError.setAttribute('hidden', '');
            return true;
        } else {
            matchIndicator.setAttribute('hidden', '');
            matchError.removeAttribute('hidden');
            return false;
        }
    }

    /**
     * Alterna visibilidade da senha
     */
    function togglePasswordVisibility(input, button) {
        return () => {
            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';
            button.innerHTML = isPassword
                ? '<i class="fas fa-eye-slash"></i>'
                : '<i class="fas fa-eye"></i>';
        };
    }

    /**
     * Muda para um estado específico
     */
    function changeState(newState) {
        Object.keys(states).forEach(key => {
            if (key === newState) {
                states[key].removeAttribute('hidden');
            } else {
                states[key].setAttribute('hidden', '');
            }
        });

        if (window.innerWidth < 768) {
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    /**
     * Mostra spinner no botão
     */
    function showSpinner(show = true) {
        const btnText = submitBtn.querySelector('.btn-text');
        const btnSpinner = submitBtn.querySelector('.btn-spinner');

        if (show) {
            submitBtn.disabled = true;
            btnText.setAttribute('hidden', '');
            btnSpinner.removeAttribute('hidden');
        } else {
            submitBtn.disabled = false;
            btnText.removeAttribute('hidden');
            btnSpinner.setAttribute('hidden', '');
        }
    }

    /**
     * Event listeners
     */
    passwordInput.addEventListener('input', () => {
        updateStrengthIndicator(passwordInput.value);
        updateRequirements(passwordInput.value);
        validateMatch();
    });

    confirmInput.addEventListener('input', validateMatch);

    togglePassword.addEventListener('click', (e) => {
        e.preventDefault();
        togglePasswordVisibility(passwordInput, togglePassword)();
    });

    toggleConfirm.addEventListener('click', (e) => {
        e.preventDefault();
        togglePasswordVisibility(confirmInput, toggleConfirm)();
    });

    /**
     * Validação no envio do formulário
     */
    resetForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const password = passwordInput.value;
        const confirm = confirmInput.value;

        // Validações básicas
        if (!password || !confirm) {
            showError('Preencha todos os campos de senha.');
            return;
        }

        if (password !== confirm) {
            showError('Senhas não coincidem.');
            return;
        }

        if (password.length < 8) {
            showError('Senha deve ter pelo menos 8 caracteres.');
            return;
        }

        if (!/[A-Z]/.test(password)) {
            showError('Senha deve conter pelo menos uma letra maiúscula.');
            return;
        }

        // Envia o formulário
        showSpinner(true);

        try {
            const response = await fetch(resetForm.action || window.location.pathname, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams(new FormData(resetForm))
            });

            const text = await response.text();

            if (response.ok) {
                // Sucesso - mostra estado de sucesso
                changeState('success');
            } else {
                // Erro
                showError('Erro ao atualizar senha. Tente novamente.');
                showSpinner(false);
            }
        } catch (error) {
            console.error('Erro na requisição:', error);
            showError('Erro de conexão. Verifique sua internet.');
            showSpinner(false);
        }
    });

    /**
     * Exibe mensagem de erro
     */
    function showError(message) {
        let errorEl = document.getElementById('error-msg');

        if (!errorEl) {
            errorEl = document.createElement('p');
            errorEl.className = 'form-error';
            errorEl.id = 'error-msg';
            document.querySelector('.reset-header').after(errorEl);
        }

        errorEl.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>${message}</span>
        `;

        errorEl.style.animation = 'fadeIn 0.3s ease-out';
    }

    /**
     * Inicialização
     */
    function init() {
        // Auto-focus no primeiro campo
        setTimeout(() => {
            passwordInput.focus();
        }, 300);

        // Valida estado inicial se houver erro server-side
        const errorEl = document.querySelector('.form-error');
        if (errorEl && errorEl.textContent) {
            // Erro já exibido do servidor
        }
    }

    init();
});
