import hashlib
import mimetypes
import os
import re
from functools import wraps
from dotenv import load_dotenv

from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    render_template_string,
    request,
    session,
    url_for,
)
from flask_mail import Mail, Message
from sqlalchemy import inspect
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError

from ai_generator import generate_design
from models import CommunityDesign, CommunityVote, Design, Pedido, User, db
from payment import gerar_qr_pix, get_valores_sugeridos

load_dotenv()

raw_database_url = os.environ.get("DATABASE_URL", "sqlite:///database.db")
if raw_database_url.startswith("postgres://"):
    raw_database_url = raw_database_url.replace("postgres://", "postgresql://", 1)

is_sqlite_database = raw_database_url.startswith("sqlite")

# Bootstrap principal da aplicacao.
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.secret_key = app.config["SECRET_KEY"]

app.config["SQLALCHEMY_DATABASE_URI"] = raw_database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}

# Config de e-mail para recuperacao de conta (Gmail padrao).
# Configuracao comprovada: Port 587 (TLS) com TLS=True, SSL=False.
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "true").lower() in {"1", "true", "yes"}
app.config["MAIL_USE_SSL"] = os.environ.get("MAIL_USE_SSL", "false").lower() in {"1", "true", "yes"}
app.config["MAIL_USERNAME"] = os.getenv("EMAIL_USER")
app.config["MAIL_PASSWORD"] = os.getenv("EMAIL_PASS")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get(
    "MAIL_DEFAULT_SENDER", app.config["MAIL_USERNAME"] or "no-reply@moletom.store"
)

db.init_app(app)
mail = Mail(app)
reset_serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
RESET_TOKEN_MAX_AGE_SECONDS = int(os.environ.get("RESET_TOKEN_MAX_AGE_SECONDS", 1800))
auto_create_schema = os.environ.get("AUTO_CREATE_SCHEMA", "false").lower() in {"1", "true", "yes"}

if is_sqlite_database or auto_create_schema:
    with app.app_context():
        db.create_all()


def _bootstrap_database_schema() -> None:
    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = set(inspector.get_table_names())
        expected_tables = {"user", "design", "community_design", "community_vote", "pedido"}

        if not expected_tables.issubset(existing_tables):
            db.create_all()


# Compatibilidade de schema para bancos locais sem migracao formal.
def _ensure_user_schema():
    if not is_sqlite_database:
        return

    # Compatibilidade para banco SQLite existente sem migracoes.
    existing_cols = {
        row[1] for row in db.session.execute(text("PRAGMA table_info(user)")).fetchall()
    }

    if "full_name" not in existing_cols:
        db.session.execute(text("ALTER TABLE user ADD COLUMN full_name VARCHAR(120)"))
    if "username" not in existing_cols:
        db.session.execute(text("ALTER TABLE user ADD COLUMN username VARCHAR(80)"))
    if "phone" not in existing_cols:
        db.session.execute(text("ALTER TABLE user ADD COLUMN phone VARCHAR(30)"))

    db.session.execute(
        text("CREATE UNIQUE INDEX IF NOT EXISTS ux_user_username ON user(username)")
    )
    db.session.commit()


def _ensure_design_schema():
    if not is_sqlite_database:
        return

    # Compatibilidade para banco SQLite existente sem migracoes.
    existing_cols = {
        row[1] for row in db.session.execute(text("PRAGMA table_info(design)")).fetchall()
    }

    if "user_id" not in existing_cols:
        db.session.execute(text("ALTER TABLE design ADD COLUMN user_id INTEGER"))

    db.session.execute(
        text("CREATE INDEX IF NOT EXISTS ix_design_user_id ON design(user_id)")
    )
    db.session.commit()


with app.app_context():
    _ensure_user_schema()
    _ensure_design_schema()


# Helpers de permissao, sessao e identidade visual.
def _is_curator(user: User | None) -> bool:
    if user is None:
        return False

    raw = os.environ.get("MOLETOM_CURATORS", "admin,curadoria,moderador")
    curators = {item.strip().lower() for item in raw.split(",") if item.strip()}
    return user.id in {1, 3} or (user.username or "").lower() in curators


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


def _avatar_initials(value: str) -> str:
    clean = (value or "").strip()
    if not clean:
        return "MT"

    local = clean.split("@")[0]
    parts = [p for p in local.replace("_", " ").replace("-", " ").split() if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    if len(parts) == 1 and len(parts[0]) >= 2:
        return parts[0][:2].upper()
    if len(parts) == 1:
        return parts[0][0].upper() + "T"
    return "MT"


def _build_password_reset_token(user: User) -> str:
    return reset_serializer.dumps(user.email, salt="email-confirm")


def _resolve_user_from_reset_token(token: str) -> User | None:
    try:
        email = reset_serializer.loads(
            token,
            salt="email-confirm",
            max_age=RESET_TOKEN_MAX_AGE_SECONDS,
        )
    except (SignatureExpired, BadSignature):
        return None

    return User.query.filter_by(email=email).first()


def _send_password_reset_email(user: User) -> bool:
    reset_link = url_for("reset_password", token=_build_password_reset_token(user), _external=True)
    message = Message(
        subject="MOLETOM | Recuperacao de conta",
        recipients=[user.email],
    )

    logo_cid = None
    logo_path = os.path.join(app.root_path, "static", "img", "logo2.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as logo_file:
            logo_bytes = logo_file.read()
        logo_content_type = mimetypes.guess_type(logo_path)[0] or "image/png"
        logo_cid = "moletom-logo"
        message.attach(
            filename="logo2.png",
            content_type=logo_content_type,
            data=logo_bytes,
            disposition="inline",
            headers={"Content-ID": f"<{logo_cid}>", "X-Attachment-Id": logo_cid},
        )

    # HTML do email com layout profissional e botão
    html_body = render_template(
        "email/reset_password.html",
        reset_link=reset_link,
        logo_cid=logo_cid,
        logo_url=url_for("static", filename="img/logo2.png", _external=True),
    )

    # Fallback para plain text
    message.body = (
        "Recebemos um pedido para redefinir sua senha.\n\n"
        f"Acesse este link para continuar: {reset_link}\n\n"
        f"Esse link expira em {RESET_TOKEN_MAX_AGE_SECONDS // 60} minutos.\n"
        "Se voce nao solicitou, ignore este e-mail."
    )

    message.html = html_body

    try:
        mail.send(message)
        return True
    except Exception as e:
        print(f"Erro ao enviar email: {e}", flush=True)
        return False


def send_reset_email(user_email: str) -> bool:
    user = User.query.filter_by(email=user_email).first()
    if user is None:
        return False
    return _send_password_reset_email(user)


# Rotas publicas de navegacao.
@app.route("/api/avatar")
def api_avatar():
    source = request.args.get("name", "").strip() or session.get("username") or "MoleTom"
    initials = _avatar_initials(source)

    palette = [
        ("#0ea5e9", "#2563eb"),
        ("#22c55e", "#0891b2"),
        ("#f97316", "#ef4444"),
        ("#8b5cf6", "#ec4899"),
        ("#14b8a6", "#3b82f6"),
    ]
    start, end = palette[int(hashlib.md5(source.encode("utf-8")).hexdigest(), 16) % len(palette)]

    svg = f"""
<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120' viewBox='0 0 120 120' role='img' aria-label='Avatar'>
  <defs>
    <linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0%' stop-color='{start}' />
      <stop offset='100%' stop-color='{end}' />
    </linearGradient>
  </defs>
  <rect width='120' height='120' rx='24' fill='url(#g)' />
  <text x='60' y='74' text-anchor='middle' font-family='Arial, Helvetica, sans-serif' font-size='44' font-weight='700' fill='white'>{initials}</text>
</svg>
""".strip()

    return Response(svg, mimetype="image/svg+xml")

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/comunidade")
def comunidade():
    user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    can_moderate = _is_curator(user)

    entries = (
        db.session.query(CommunityDesign, Design, User)
        .join(Design, Design.id == CommunityDesign.design_id)
        .join(User, User.id == CommunityDesign.user_id)
        .filter(CommunityDesign.status == "approved")
        .order_by(CommunityDesign.votes_count.desc(), CommunityDesign.approved_at.desc(), CommunityDesign.created_at.desc())
        .limit(60)
        .all()
    )

    return render_template("comunidade.html", entries=entries, can_moderate=can_moderate)


@app.route("/comunidade/design/<int:community_design_id>")
def comunidade_design(community_design_id):
    user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    can_moderate = _is_curator(user)

    entry = (
        db.session.query(CommunityDesign, Design, User)
        .join(Design, Design.id == CommunityDesign.design_id)
        .join(User, User.id == CommunityDesign.user_id)
        .filter(CommunityDesign.id == community_design_id, CommunityDesign.status == "approved")
        .first_or_404()
    )
    return render_template("comunidade_design.html", entry=entry, can_moderate=can_moderate)


@app.route("/comunidade/design/<int:community_design_id>/checkout")
@login_required
def comunidade_design_checkout(community_design_id):
    user = db.session.get(User, session.get("user_id"))
    if user is None:
        session.clear()
        return redirect(url_for("login", next=request.path))

    entry = (
        db.session.query(CommunityDesign, Design)
        .join(Design, Design.id == CommunityDesign.design_id)
        .filter(CommunityDesign.id == community_design_id, CommunityDesign.status == "approved")
        .first_or_404()
    )

    source_design = entry[1]
    design = Design(
        user_id=user.id,
        prompt=source_design.prompt,
        image_url=source_design.image_url,
        color=source_design.color,
    )
    db.session.add(design)
    db.session.commit()

    return redirect(url_for("checkout", design_id=design.id))


# Fluxos de autenticacao e ciclo de conta.
@app.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.args.get("next") or request.form.get("next") or url_for("generator")

    if session.get("user_id"):
        return redirect(next_url if next_url.startswith("/") else url_for("generator"))

    error_message = None
    email_value = ""

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        email_value = email

        if not email or not password:
            error_message = "Informe e-mail e senha."

        else:

            user = User.query.filter_by(email=email).first()

            if not user or not user.check_password(password):

                error_message = "E-mail ou senha inválidos."

            else:

                session["user_id"] = user.id
                session["user_email"] = user.email
                session["username"] = user.username

                return redirect(next_url if next_url.startswith("/") else url_for("generator"))

    return render_template(
        "login.html",
        next_url=next_url,
        error_message=error_message,
        email_value=email_value,
    )


@app.route("/recuperar-conta", methods=["GET", "POST"])
def recuperar_conta():
    notice = None
    error_message = None
    email_value = ""

    if request.method == "POST":
        email_value = request.form.get("email", "").strip().lower()
        if not email_value:
            error_message = "Informe seu e-mail para continuar."
        else:
            send_reset_email(email_value)
            # Mensagem neutra evita enumeracao de contas.
            notice = "Se o e-mail informado existir, enviamos um link para redefinir sua senha."

    return render_template(
        "recuperar_conta.html",
        notice=notice,
        error_message=error_message,
        email_value=email_value,
    )


@app.route("/reset/<token>", methods=["GET", "POST"])
@app.route("/redefinir-senha/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = _resolve_user_from_reset_token(token)
    if user is None:
        return render_template_string(
            """
            <h1 style='text-align: center; margin-top: 50px; color: #fff;'>
                O link expirou ou é inválido!
            </h1>
            <p style='text-align: center; color: #999;'>
                <a href='{{ url_for("recuperar_conta") }}' style='color: #00bcd4;'>
                    Solicitar novo link de recuperação
                </a>
            </p>
            """,
            recuperar_conta=recuperar_conta
        )

    error_message = None
    success_message = None

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not password or not confirm_password:
            error_message = "Preencha os dois campos de senha."
        elif password != confirm_password:
            error_message = "Senha e confirmacao de senha nao conferem."
        elif len(password) < 8:
            error_message = "A senha deve ter pelo menos 8 caracteres."
        elif not re.search(r"[A-Z]", password):
            error_message = "A senha deve conter pelo menos uma letra maiuscula."
        elif user.username and user.username.lower() in password.lower():
            error_message = "A senha nao pode conter seu nome de usuario."
        else:
            user.set_password(password)
            db.session.commit()
            success_message = "Senha atualizada com sucesso. Voce ja pode entrar na sua conta."

    return render_template(
        "redefinir_senha.html",
        error_message=error_message,
        success_message=success_message,
    )


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if session.get("user_id"):
        return redirect(url_for("minha_conta"))

    error_message = None
    form_values = {
        "full_name": "",
        "username": "",
        "phone": "",
        "email": "",
    }

    if request.method == "POST":
        try:
            _bootstrap_database_schema()
        except OperationalError:
            error_message = "Banco de dados indisponivel no momento. Tente novamente em instantes."
            return render_template(
                "cadastro.html",
                error_message=error_message,
                form_values=form_values,
            )

        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        form_values = {
            "full_name": full_name,
            "username": username,
            "phone": phone,
            "email": email,
        }

        if not full_name or not username or not phone or not email or not password or not confirm_password:
            error_message = "Preencha todos os campos."
        elif not re.fullmatch(r"[a-z0-9_.-]{3,30}", username):
            error_message = "Usuario deve ter 3 a 30 caracteres (letras, numeros, ., _ ou -)."
        elif len(re.sub(r"\D", "", phone)) < 8:
            error_message = "Informe um numero valido com DDD."
        elif password != confirm_password:
            error_message = "Senha e confirmacao de senha nao conferem."
        elif len(password) < 8:
            error_message = "A senha deve ter pelo menos 8 caracteres."
        elif not re.search(r"[A-Z]", password):
            error_message = "A senha deve conter pelo menos uma letra maiuscula."
        elif username and username.lower() in password.lower():
            error_message = "A senha nao pode conter seu nome de usuario."
        elif User.query.filter_by(email=email).first():
            error_message = "Este e-mail ja esta cadastrado."
        elif User.query.filter_by(username=username).first():
            error_message = "Este usuario ja existe."
        else:
            user = User(
                full_name=full_name,
                username=username,
                phone=phone,
                email=email,
            )
            user.set_password(password)
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                error_message = "Nao foi possivel concluir cadastro. Verifique os dados e tente novamente."
            else:
                session["user_id"] = user.id
                session["user_email"] = user.email
                session["username"] = user.username
                return redirect(url_for("generator"))

    return render_template(
        "cadastro.html",
        error_message=error_message,
        form_values=form_values,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/minha-conta")
@login_required
def minha_conta():
    delete_error = request.args.get("delete_error", "")
    delete_error_message = None
    if delete_error == "senha_invalida":
        delete_error_message = "Senha atual incorreta. A conta nao foi excluida."
    return render_template("minha_conta.html", delete_error_message=delete_error_message)


@app.route("/minha-conta/excluir", methods=["POST"])
@login_required
def excluir_conta():
    user = db.session.get(User, session.get("user_id"))
    if user is None:
        session.clear()
        return redirect(url_for("home"))

    current_password = request.form.get("current_password", "")
    if not current_password or not user.check_password(current_password):
        return redirect(url_for("minha_conta", delete_error="senha_invalida"))

    try:
        # Remove votos realizados por este usuario.
        CommunityVote.query.filter_by(user_id=user.id).delete(synchronize_session=False)

        # Coleta todos os ids de designs do usuario para limpar dependencias.
        user_design_ids = [
            design_id for (design_id,) in db.session.query(Design.id).filter_by(user_id=user.id).all()
        ]

        if user_design_ids:
            community_design_ids = [
                community_id
                for (community_id,) in db.session.query(CommunityDesign.id)
                .filter(CommunityDesign.design_id.in_(user_design_ids))
                .all()
            ]

            if community_design_ids:
                CommunityVote.query.filter(
                    CommunityVote.community_design_id.in_(community_design_ids)
                ).delete(synchronize_session=False)

            CommunityDesign.query.filter(
                CommunityDesign.design_id.in_(user_design_ids)
            ).delete(synchronize_session=False)

            Pedido.query.filter(Pedido.design_id.in_(user_design_ids)).delete(
                synchronize_session=False
            )

            Design.query.filter(Design.id.in_(user_design_ids)).delete(
                synchronize_session=False
            )

        # Garante limpeza extra de submissions associadas ao autor, caso existam.
        CommunityDesign.query.filter_by(user_id=user.id).delete(synchronize_session=False)

        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return redirect(url_for("minha_conta"))

    session.clear()
    return redirect(url_for("home"))


@app.route("/api/minha-conta")
def api_minha_conta():
    if not session.get("user_id"):
        return jsonify({"error": "Nao autenticado"}), 401

    user = db.session.get(User, session.get("user_id"))
    if user is None:
        session.clear()
        return jsonify({"error": "Sessao invalida"}), 401

    user_designs_query = Design.query.filter_by(user_id=user.id)
    recent_designs = user_designs_query.order_by(Design.created_at.desc()).limit(6).all()
    community_entries = (
        CommunityDesign.query.filter_by(user_id=user.id)
        .order_by(CommunityDesign.created_at.desc())
        .limit(6)
        .all()
    )

    return jsonify(
        {
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "username": user.username,
                "phone": user.phone,
                "email": user.email,
            },
            "stats": {
                "total_designs": user_designs_query.count(),
                "recent_designs_count": len(recent_designs),
            },
            "recent_designs": [
                {
                    "id": design.id,
                    "prompt": design.prompt,
                    "color": design.color,
                    "image_url": design.image_url,
                    "created_at": design.created_at.isoformat() if design.created_at else None,
                }
                for design in recent_designs
            ],
            "community_submissions": [
                {
                    "id": entry.id,
                    "design_id": entry.design_id,
                    "title": entry.title,
                    "status": entry.status,
                    "votes_count": entry.votes_count,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                }
                for entry in community_entries
            ],
        }
    )


@app.route("/api/comunidade/enviar", methods=["POST"])
@login_required
def api_comunidade_enviar():
    data = request.get_json(silent=True) or {}
    design_id = data.get("design_id")
    title = (data.get("title") or "").strip()
    caption = (data.get("caption") or "").strip()

    if not design_id:
        return jsonify({"error": "Design invalido."}), 400

    design = Design.query.filter_by(id=design_id, user_id=session.get("user_id")).first()
    if design is None:
        return jsonify({"error": "Design nao encontrado para este usuario."}), 404

    existing = CommunityDesign.query.filter_by(design_id=design.id).first()
    if existing:
        return jsonify(
            {
                "message": "Este design ja foi enviado para a comunidade.",
                "community_design_id": existing.id,
                "status": existing.status,
            }
        )

    safe_title = title[:120] if title else f"Arte #{design.id}"
    safe_caption = caption[:280] if caption else None

    entry = CommunityDesign(
        design_id=design.id,
        user_id=session.get("user_id"),
        title=safe_title,
        caption=safe_caption,
        status="pending",
    )

    db.session.add(entry)
    db.session.commit()

    return jsonify(
        {
            "message": "Design enviado para curadoria com sucesso.",
            "community_design_id": entry.id,
            "status": entry.status,
        }
    )


@app.route("/api/comunidade/votar/<int:community_design_id>", methods=["POST"])
@login_required
def api_comunidade_votar(community_design_id):
    entry = CommunityDesign.query.filter_by(id=community_design_id, status="approved").first()
    if entry is None:
        return jsonify({"error": "Design da comunidade nao encontrado."}), 404

    user_id = session.get("user_id")
    existing_vote = CommunityVote.query.filter_by(community_design_id=entry.id, user_id=user_id).first()
    if existing_vote:
        return jsonify({"error": "Voce ja votou neste design."}), 409

    vote = CommunityVote(community_design_id=entry.id, user_id=user_id)
    entry.votes_count += 1
    db.session.add(vote)
    db.session.commit()

    return jsonify({"message": "Voto contabilizado.", "votes_count": entry.votes_count})


@app.route("/curadoria/comunidade", methods=["GET", "POST"])
@login_required
def curadoria_comunidade():
    user = db.session.get(User, session.get("user_id"))
    if not _is_curator(user):
        return redirect(url_for("comunidade"))

    feedback = None

    if request.method == "POST":
        entry_id = request.form.get("entry_id", type=int)
        action = (request.form.get("action") or "").strip()
        note = (request.form.get("note") or "").strip()[:280]

        entry = CommunityDesign.query.filter_by(id=entry_id, status="pending").first()
        if entry is None:
            feedback = "Registro nao encontrado ou ja moderado."
        else:
            if action == "approve":
                from datetime import datetime, timezone

                entry.status = "approved"
                entry.approved_at = datetime.now(timezone.utc)
                entry.curator_note = note or None
                feedback = "Design aprovado e publicado na galeria."
                db.session.commit()
            elif action == "reject":
                entry.status = "rejected"
                entry.curator_note = note or None
                feedback = "Design reprovado na curadoria."
                db.session.commit()
            else:
                feedback = "Acao invalida."

    pending_entries = (
        db.session.query(CommunityDesign, Design, User)
        .join(Design, Design.id == CommunityDesign.design_id)
        .join(User, User.id == CommunityDesign.user_id)
        .filter(CommunityDesign.status == "pending")
        .order_by(CommunityDesign.created_at.asc())
        .all()
    )

    return render_template("curadoria_comunidade.html", pending_entries=pending_entries, feedback=feedback)

@app.route("/generator", methods=["GET", "POST"])
def generator():
    selected_color = request.args.get("color", "preto")
    prompt_value = ""
    error_message = None

    if request.method == "POST":
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))

        prompt = request.form["prompt"]
        color = request.form.get("color", "preto")
        prompt_value = prompt
        selected_color = color

        try:
            image_url = generate_design(prompt, color)
        except RuntimeError as exc:
            error_message = str(exc)
            return render_template(
                "generator.html",
                selected_color=selected_color,
                prompt_value=prompt_value,
                error_message=error_message,
            )

        design = Design(
            user_id=session.get("user_id"),
            prompt=prompt,
            image_url=image_url,
            color=color
        )

        db.session.add(design)
        db.session.commit()

        return redirect(url_for("preview", design_id=design.id))

    return render_template(
        "generator.html",
        selected_color=selected_color,
        prompt_value=prompt_value,
        error_message=error_message,
    )

@app.route("/preview/<int:design_id>")
@login_required
def preview(design_id):
    design = Design.query.filter_by(id=design_id, user_id=session.get("user_id")).first_or_404()
    community_entry = CommunityDesign.query.filter_by(design_id=design.id).first()

    return render_template("preview.html", design=design, community_entry=community_entry)


@app.route("/checkout/<int:design_id>", methods=["GET", "POST"])
@login_required
def checkout(design_id):
    design = Design.query.filter_by(id=design_id, user_id=session.get("user_id")).first_or_404()
    user = db.session.get(User, session.get("user_id"))

    if user is None:
        session.clear()
        return redirect(url_for("login", next=url_for("checkout", design_id=design_id)))

    checkout_data = {
        "full_name": user.full_name or user.username or session.get("username", "Usuário"),
        "email": user.email or session.get("user_email", ""),
        "phone": user.phone or "",
        "cep": "",
        "street": "",
        "number": "",
        "complement": "",
        "district": "",
        "city": "",
        "state": "",
        "reference": "",
        "payment_method": "pix",
    }
    error_message = None
    order_success = False

    if request.method == "POST":
        for key in checkout_data:
            checkout_data[key] = request.form.get(key, "").strip()

        required_fields = ["full_name", "email", "cep", "street", "number", "district", "city", "state"]
        if any(not checkout_data[field] for field in required_fields):
            error_message = "Preencha os campos obrigatórios e complete o endereço com o CEP."
        else:
            order_success = True

    return render_template(
        "checkout.html",
        design=design,
        user=user,
        checkout_data=checkout_data,
        error_message=error_message,
        order_success=order_success,
    )
    
@app.route("/pix/qr")
def pix_qr():
    """Endpoint que gera o QR Code PIX e retorna base64."""
    valor = request.args.get("valor", "1.00")
    
    # Garante que o valor é um dos permitidos (segurança)
    valores_permitidos = {"0.50", "1.00", "2.00"}
    if valor not in valores_permitidos:
        valor = "1.00"
    
    try:
        qr_b64 = gerar_qr_pix(valor)
        return jsonify({"qr_b64": qr_b64, "valor": valor})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/pix/valores")
def pix_valores():
    """Retorna os valores sugeridos para o modal PIX."""
    return jsonify({"valores": get_valores_sugeridos(), "default": "1.00"})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
    # app.run(debug=True)