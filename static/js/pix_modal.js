/**
 * pix_modal.js — Lógica do modal de contribuição PIX MoleTom
 * 
 * Requer: endpoint Flask /pix/qr?valor=X.XX (retorna { qr_b64: "data:image/png;base64,..." })
 */

const pixModal = (() => {
  let currentValor = '1.00';
  let valoresLoaded = false;

  const fallbackValores = [
    { label: '☕ Café', valor: '0.50' },
    { label: '🍕 Apoio', valor: '1.00' },
    { label: '🚀 Top', valor: '2.00' },
  ];

  // ─── Inicializa o som de agradecimento ───────────────────────────────────
  function _initAudio() {
    // Usa Web Audio API para gerar um som de "sucesso" sem arquivo externo
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    
    function playNote(freq, start, duration, gain = 0.3) {
      const osc = ctx.createOscillator();
      const gainNode = ctx.createGain();
      osc.connect(gainNode);
      gainNode.connect(ctx.destination);
      osc.frequency.setValueAtTime(freq, ctx.currentTime + start);
      gainNode.gain.setValueAtTime(0, ctx.currentTime + start);
      gainNode.gain.linearRampToValueAtTime(gain, ctx.currentTime + start + 0.05);
      gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + start + duration);
      osc.type = 'sine';
      osc.start(ctx.currentTime + start);
      osc.stop(ctx.currentTime + start + duration);
    }

    // Acorde de vitória: Dó-Mi-Sol-Dó (arpejo)
    playNote(523.25, 0.0,  0.3);  // C5
    playNote(659.25, 0.12, 0.3);  // E5
    playNote(783.99, 0.24, 0.3);  // G5
    playNote(1046.5, 0.36, 0.6);  // C6
  }

  // ─── Partículas de fundo ─────────────────────────────────────────────────
  function _createParticles() {
    const wrap = document.getElementById('pix-particles');
    if (!wrap) return;
    wrap.innerHTML = '';
    const colors = ['#6200EE', '#9c42f5', '#c084fc', '#818cf8', '#00BCD4'];
    for (let i = 0; i < 18; i++) {
      const p = document.createElement('div');
      p.className = 'pix-particle';
      p.style.cssText = `
        left: ${Math.random() * 100}%;
        background: ${colors[Math.floor(Math.random() * colors.length)]};
        animation-duration: ${4 + Math.random() * 6}s;
        animation-delay: ${Math.random() * 4}s;
        width: ${4 + Math.random() * 6}px;
        height: ${4 + Math.random() * 6}px;
      `;
      wrap.appendChild(p);
    }
  }

  function _renderAmounts(valores) {
    const wrap = document.getElementById('pix-amounts');
    if (!wrap) return;

    wrap.innerHTML = '';

    valores.forEach((item, index) => {
      const rawLabel = (item.label || 'Apoio').trim();
      const labelParts = rawLabel.split(/\s+/);
      const hasExplicitEmoji = Boolean(item.emoji);
      const emoji = item.emoji || (labelParts.length > 1 ? labelParts[0] : '✨');
      const labelText = hasExplicitEmoji ? rawLabel : (labelParts.length > 1 ? labelParts.slice(1).join(' ') : rawLabel);

      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'pix-amount-btn';
      button.dataset.value = item.valor;
      if (item.valor === currentValor || (!currentValor && index === 1)) {
        button.classList.add('pix-amount-selected');
      }

      const valueText = Number.parseFloat(item.valor || '0').toLocaleString('pt-BR', {
        style: 'currency',
        currency: 'BRL',
      });

      button.innerHTML = `
        <span class="pix-amount-emoji">${emoji}</span>
        <span class="pix-amount-label">${labelText}</span>
        <span class="pix-amount-value">${valueText}</span>
      `;
      button.addEventListener('click', () => selectAmount(button, item.valor));
      wrap.appendChild(button);
    });
  }

  async function _loadValores() {
    if (valoresLoaded) return;
    valoresLoaded = true;

    try {
      const response = await fetch('/pix/valores');
      if (!response.ok) throw new Error('Falha ao carregar valores');
      const data = await response.json();
      currentValor = data.default || currentValor;
      _renderAmounts(Array.isArray(data.valores) && data.valores.length ? data.valores : fallbackValores);
    } catch (error) {
      _renderAmounts(fallbackValores);
      console.error(error);
    }
  }

  // ─── Confetti ─────────────────────────────────────────────────────────────
  function _launchConfetti() {
    const wrap = document.getElementById('pix-confetti');
    if (!wrap) return;
    wrap.innerHTML = '';
    const colors = ['#6200EE','#9c42f5','#c084fc','#f472b6','#facc15','#34d399','#60a5fa'];
    for (let i = 0; i < 60; i++) {
      const p = document.createElement('div');
      p.className = 'pix-confetti-piece';
      p.style.cssText = `
        left: ${Math.random() * 100}%;
        top: ${-10 - Math.random() * 20}px;
        background: ${colors[Math.floor(Math.random() * colors.length)]};
        width: ${6 + Math.random() * 8}px;
        height: ${6 + Math.random() * 8}px;
        border-radius: ${Math.random() > 0.5 ? '50%' : '2px'};
        animation-duration: ${1.2 + Math.random() * 1.5}s;
        animation-delay: ${Math.random() * 0.8}s;
      `;
      wrap.appendChild(p);
    }
  }

  // ─── Carregar QR Code via fetch ───────────────────────────────────────────
  async function _loadQR(valor) {
    const loader = document.getElementById('pix-loader');
    const img    = document.getElementById('pix-qr-img');
    if (!loader || !img) return;

    loader.style.display = 'flex';
    img.style.display = 'none';

    try {
      const res = await fetch(`/pix/qr?valor=${valor}`);
      if (!res.ok) throw new Error('Erro ao gerar QR');
      const data = await res.json();
      img.src = data.qr_b64;
      img.style.display = 'block';
      loader.style.display = 'none';
    } catch (err) {
      loader.innerHTML = '<span style="color:#ff6b6b">Erro ao gerar QR Code. Tente novamente.</span>';
      console.error(err);
    }
  }

  // ─── API pública ──────────────────────────────────────────────────────────
  function open(valor = '1.00') {
    currentValor = valor;
    _createParticles();
    _loadValores();

    const overlay = document.getElementById('pix-modal-overlay');
    const thanks  = document.getElementById('pix-thanks');
    const modal   = overlay?.querySelector('.pix-modal');

    if (!overlay) return;
    thanks.style.display = 'none';
    if (modal) modal.style.display = 'block';

    overlay.classList.add('pix-open');
    document.body.style.overflow = 'hidden';

    // Seleciona o botão correto
    document.querySelectorAll('.pix-amount-btn').forEach(btn => {
      btn.classList.toggle('pix-amount-selected', btn.dataset.value === valor);
    });

    _loadQR(valor);
  }

  function close() {
    const overlay = document.getElementById('pix-modal-overlay');
    if (!overlay) return;
    overlay.classList.remove('pix-open');
    document.body.style.overflow = '';
  }

  function selectAmount(btn, valor) {
    document.querySelectorAll('.pix-amount-btn').forEach(b => b.classList.remove('pix-amount-selected'));
    btn.classList.add('pix-amount-selected');
    currentValor = valor;
    _loadQR(valor);
  }

  function confirmPayment() {
    const overlay = document.getElementById('pix-modal-overlay');
    const thanks  = document.getElementById('pix-thanks');
    const modal   = overlay?.querySelector('.pix-modal');

    if (!overlay) return;

    // Esconde modal principal, mostra agradecimento
    if (modal) modal.style.display = 'none';
    thanks.style.display = 'flex';
    _launchConfetti();
    _initAudio();

    // Animação do emoji
    const emoji = document.getElementById('pix-thanks-emoji');
    if (emoji) {
      const emojis = ['🎉','💜','🚀','✨','🙏'];
      let i = 0;
      const interval = setInterval(() => {
        emoji.textContent = emojis[i % emojis.length];
        i++;
        if (i >= emojis.length * 2) clearInterval(interval);
      }, 300);
    }
  }

  // Fecha ao clicar fora
  document.addEventListener('DOMContentLoaded', () => {
    const overlay = document.getElementById('pix-modal-overlay');
    overlay?.addEventListener('click', (e) => {
      if (e.target === overlay) close();
    });
    // ESC fecha
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') close();
    });
  });

  return { open, close, selectAmount, confirmPayment };
})();