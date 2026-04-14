# 👕 MoleTom Store — E-commerce com IA Generativa & PIX Nativo

O **MoleTom Store** é uma plataforma de e-commerce *print-on-demand* inovadora, onde os usuários podem criar estampas personalizadas para moletons utilizando Inteligência Artificial Generativa. O projeto resolve desafios complexos de engenharia, como integração de APIs de IA, processamento de imagens no servidor e fluxos de pagamento dinâmicos.

🚀 **Acesse o projeto:** [moletom-store.render.com](https://moletom-store.render.com) 

---

## 🛠️ Stack Tecnológica

*   **Backend:** Python / Flask (Arquitetura RESTful)
*   **Banco de Dados:** PostgreSQL (via Supabase BaaS)
*   **IA Generativa:** Modelo FLUX (via API externa)
*   **Processamento de Imagem:** Pillow (Composição de estampas sobre mockups reais)
*   **Pagamentos:** Integração PIX (Geração dinâmica de BR Code/EMV + CRC-16)
*   **E-mail:** SMTP (Fluxos de recuperação de senha e confirmação)
*   **Hospedagem:** Render (Deploy contínuo)

---

## ✨ Funcionalidades Principais

*   **Criação via IA:** O usuário descreve a arte desejada, a IA gera a imagem e o sistema a aplica automaticamente sobre o moletom.
*   **Galeria da Comunidade:** Sistema de votação e exibição de designs criados por outros usuários.
*   **Autenticação Completa:** Gestão de usuários com criptografia de senha e recuperação via e-mail.
*   **Checkout Dinâmico:** Geração de cobrança PIX em tempo real com validação de dados.
*   **Dashboard Administrativo:** Gestão de pedidos e designs (se aplicável).

---

## 🏗️ Arquitetura e Boas Práticas

O projeto segue princípios de **Clean Code** e separação de responsabilidades:
*   `app.py`: Ponto de entrada e rotas da aplicação.
*   `ai_generator.py`: Lógica de integração com modelos de IA Generativa.
*   `payment.py`: Implementação da lógica de geração de QR Code PIX.
*   `models.py`: Definição de esquemas de dados e integração com Supabase.

---

## 📂 Estrutura do Repositório

```bash
├── static/              # Ativos (CSS, JS, Imagens de Mockup)
├── templates/           # Páginas HTML (Jinja2)
├── ai_generator.py      # Módulo de integração com IA
├── payment.py           # Módulo de pagamentos PIX
├── requirements.txt     # Dependências do projeto
└── app.py               # Servidor Flask principal
```

---

## 🚀 Como Executar o Projeto

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/JanGustavo/moletom-store.git
    ```
2.  **Crie um ambiente virtual e instale as dependências:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    pip install -r requirements.txt
    ```
3.  **Configure as variáveis de ambiente (`.env`):**
    ```env
    SUPABASE_URL=sua_url
    SUPABASE_KEY=sua_chave
    AI_API_KEY=sua_chave_ia
    ```
4.  **Inicie o servidor:**
    ```bash
    python app.py
    ```

---

## 🤝 Contato

*   **LinkedIn:** [linkedin.com/in/janderson-gustavo](https://linkedin.com/in/janderson-gustavo)
*   **GitHub:** [github.com/JanGustavo](https://github.com/JanGustavo)

---
*Desenvolvido por Jan Gustavo — Transformando ideias em produtos reais com IA.*
