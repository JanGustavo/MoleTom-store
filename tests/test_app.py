import os
import tempfile
import unittest
from unittest.mock import patch

# Configura ambiente de teste antes de importar o app
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("AUTO_CREATE_SCHEMA", "true")

from app import app, db, User, Design  # noqa: E402


class AppRoutesTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
        )

        with app.app_context():
            db.drop_all()
            db.create_all()

    def setUp(self):
        self.client = app.test_client()

    def tearDown(self):
        with self.client.session_transaction() as sess:
            sess.clear()

    def test_home_page_returns_200(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_api_avatar_returns_svg(self):
        response = self.client.get("/api/avatar?name=moletom")
        self.assertEqual(response.status_code, 200)
        self.assertIn("image/svg+xml", response.content_type)
        self.assertIn("<svg", response.get_data(as_text=True))

    def test_minha_conta_requires_login(self):
        response = self.client.get("/minha-conta", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers.get("Location", ""))

    def test_recuperar_conta_empty_email_shows_error(self):
        response = self.client.post(
            "/recuperar-conta",
            data={"email": ""},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Informe seu e-mail para continuar.", response.get_data(as_text=True))

    def test_generator_post_logged_user_creates_design(self):
        with app.app_context():
            user = User(
                full_name="Teste User",
                username="testeuser",
                phone="83999999999",
                email="teste@example.com",
            )
            user.set_password("SenhaForte123")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        with self.client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["user_email"] = "teste@example.com"
            sess["username"] = "testeuser"

        with patch("app.generate_design", return_value="https://i.ibb.co/fake/design.png"):
            response = self.client.post(
                "/generator",
                data={"prompt": "estampa teste", "color": "preto"},
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/preview/", response.headers.get("Location", ""))

        with app.app_context():
            created_design = Design.query.filter_by(user_id=user_id).order_by(Design.id.desc()).first()
            self.assertIsNotNone(created_design)
            self.assertEqual(created_design.image_url, "https://i.ibb.co/fake/design.png")


if __name__ == "__main__":
    unittest.main(verbosity=2)
