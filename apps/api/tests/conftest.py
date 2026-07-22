"""Runs before any test module imports the app: pin DATABASE_URL to a fresh
throwaway SQLite file so tests can never touch a real database."""
import os
import tempfile

_tmpdir = tempfile.mkdtemp(prefix="auburn-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"
os.environ["UPLOAD_DIR"] = f"{_tmpdir}/uploads"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["ADMIN_API_KEY"] = "test-admin"
