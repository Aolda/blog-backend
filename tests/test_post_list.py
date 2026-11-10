import os
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

with patch.dict(os.environ, {
    "DATABASE_URL": "sqlite://",
    "SESSION_SECRET_KEY": "test",
    "JWT_SECRET_KEY": "test",
    "GOOGLE_CLIENT_ID": "test",
    "GOOGLE_CLIENT_SECRET": "test",
    "KEYCLOAK_ISSUER_URI": "https://example.invalid",
    "KEYCLOAK_CLIENT_ID": "test",
    "KEYCLOAK_CLIENT_SECRET": "test",
}):
    from app.api.v1.endpoints.posts import get_db, router
    from app.core.security import create_access_token
    from app.db.database import Base
    from app.db.models import Post, User


class PostListTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
        )
        self.addCleanup(engine.dispose)
        Base.metadata.create_all(engine)
        db = Session(engine)
        self.addCleanup(db.close)
        self.user = User(id=1, username="writer", email="writer@example.com", hashed_password="test")
        other = User(id=2, username="other", email="other@example.com", hashed_password="test")
        db.add_all([self.user, other])
        db.flush()
        db.add_all([
            Post(id=1, author_id=1),
            Post(id=2, author_id=2, users=[self.user, other]),
            Post(id=3, author_id=1, users=[self.user, other], is_published=True),
            Post(id=4, author_id=2, users=[other]),
            Post(id=5, author_id=2, users=[other], is_published=True),
        ])
        db.commit()
        app = FastAPI()
        app.include_router(router, prefix="/posts")
        app.dependency_overrides[get_db] = lambda: db
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        token = create_access_token({"sub": self.user.username})
        self.client.headers["Authorization"] = f"Bearer {token}"

    def test_editable_list_includes_owned_and_shared_drafts_without_duplicates(self):
        response = self.client.get("/posts?limit=2")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual([post["id"] for post in data["items"]], [3, 2])
        self.assertEqual(data["total"], 3)
        self.assertTrue(all(post["can_edit"] for post in data["items"]))
        self.assertFalse(data["items"][1]["is_published"])
        second = self.client.get("/posts?limit=2&page=2").json()
        self.assertEqual([post["id"] for post in second["items"]], [1])
        self.assertEqual((second["page"], second["limit"], second["total"]), (2, 2, 3))

    def test_editable_list_requires_login(self):
        del self.client.headers["Authorization"]
        self.assertEqual(self.client.get("/posts").status_code, 403)

    def test_invalid_token_is_rejected(self):
        self.client.headers["Authorization"] = "Bearer invalid"
        self.assertEqual(self.client.get("/posts").status_code, 401)
