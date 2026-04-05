import os
import unittest
from uuid import uuid4

from sqlalchemy import inspect, text

# Usa o banco real apenas quando a URL de integracao estiver configurada.
SUPABASE_DATABASE_URL = os.environ.get("SUPABASE_DATABASE_URL") or os.environ.get("DATABASE_URL", "")

if SUPABASE_DATABASE_URL.startswith("postgres://"):
    SUPABASE_DATABASE_URL = SUPABASE_DATABASE_URL.replace("postgres://", "postgresql://", 1)


def integration_enabled() -> bool:
    return SUPABASE_DATABASE_URL.startswith("postgresql://") and "supabase.co" in SUPABASE_DATABASE_URL


os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", SUPABASE_DATABASE_URL or "sqlite:///:memory:")
os.environ.setdefault("AUTO_CREATE_SCHEMA", "false")

from app import app, db, User, _build_password_reset_token  # noqa: E402


@unittest.skipUnless(integration_enabled(), "Teste de integracao com Supabase desativado")
class SupabaseIntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
        )

    def setUp(self):
        self.client = app.test_client()

    def _unique_suffix(self) -> str:
        return uuid4().hex[:10]

    def _delete_user_by_email(self, email: str) -> None:
        with app.app_context():
            user = User.query.filter_by(email=email).first()
            if user is not None:
                db.session.delete(user)
                db.session.commit()

    def _create_user(self, email: str, username: str, password: str = "SenhaForte123") -> int:
        with app.app_context():
            user = User(
                full_name="Integration Test",
                username=username,
                phone="83999999999",
                email=email,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return user.id

    def test_supabase_connection_and_schema(self):
        with app.app_context():
            tables = set(inspect(db.engine).get_table_names())
            self.assertIn("user", tables)
            self.assertIn("design", tables)

            result = db.session.execute(text("SELECT 1")).scalar()
            self.assertEqual(result, 1)

    def test_create_and_cleanup_user_in_supabase(self):
        suffix = self._unique_suffix()
        email = f"integration-{suffix}@example.com"
        username = f"integ{suffix}"
        self.addCleanup(self._delete_user_by_email, email)

        created_id = self._create_user(email, username)

        with app.app_context():
            fetched = User.query.filter_by(id=created_id).first()
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.email, email)
            self.assertTrue(fetched.check_password("SenhaForte123"))
            db.session.delete(fetched)
            db.session.commit()

            removed = User.query.filter_by(id=created_id).first()
            self.assertIsNone(removed)

    def test_cadastro_route_can_persist_to_supabase(self):
        suffix = self._unique_suffix()
        email = f"route-{suffix}@example.com"
        username = f"route{suffix}"
        self.addCleanup(self._delete_user_by_email, email)

        response = self.client.post(
            "/cadastro",
            data={
                "full_name": "Route Integration",
                "username": username,
                "phone": "83999999999",
                "email": email,
                "password": "SenhaForte123",
                "confirm_password": "SenhaForte123",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)

        with app.app_context():
            created_user = User.query.filter_by(email=email).first()
            self.assertIsNotNone(created_user)
            self.assertEqual(created_user.username, username)

    def test_login_route_authenticates_user_in_supabase(self):
        suffix = self._unique_suffix()
        email = f"login-{suffix}@example.com"
        username = f"login{suffix}"
        self.addCleanup(self._delete_user_by_email, email)
        self._create_user(email, username)

        response = self.client.post(
            "/login",
            data={
                "email": email,
                "password": "SenhaForte123",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/generator", response.headers.get("Location", ""))

        with self.client.session_transaction() as sess:
            self.assertIsNotNone(sess.get("user_id"))
            self.assertEqual(sess.get("user_email"), email)
            self.assertEqual(sess.get("username"), username)

    def test_recovery_token_updates_password_in_supabase(self):
        suffix = self._unique_suffix()
        email = f"recover-{suffix}@example.com"
        username = f"recover{suffix}"
        self.addCleanup(self._delete_user_by_email, email)
        user_id = self._create_user(email, username)

        with app.app_context():
            user = User.query.filter_by(id=user_id).first()
            self.assertIsNotNone(user)
            token = _build_password_reset_token(user)

        response = self.client.post(
            f"/reset/{token}",
            data={
                "password": "NovaSenhaForte123",
                "confirm_password": "NovaSenhaForte123",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Senha atualizada com sucesso", body)

        with app.app_context():
            updated_user = User.query.filter_by(id=user_id).first()
            self.assertIsNotNone(updated_user)
            self.assertTrue(updated_user.check_password("NovaSenhaForte123"))

    def test_excluir_conta_removes_user_from_supabase(self):
        suffix = self._unique_suffix()
        email = f"delete-{suffix}@example.com"
        username = f"delete{suffix}"
        user_id = self._create_user(email, username)

        with self.client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["user_email"] = email
            sess["username"] = username

        response = self.client.post(
            "/minha-conta/excluir",
            data={"current_password": "SenhaForte123"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/", response.headers.get("Location", ""))

        with app.app_context():
            deleted_user = User.query.filter_by(id=user_id).first()
            self.assertIsNone(deleted_user)

        with self.client.session_transaction() as sess:
            self.assertFalse(sess)


if __name__ == "__main__":
    unittest.main(verbosity=2)