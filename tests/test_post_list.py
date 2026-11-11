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
    from app.api.v1.endpoints.users import router as users_router
    from app.core.config import settings
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

    def test_public_list_includes_linked_and_unlinked_published_posts(self):
        db = self.client.app.dependency_overrides[get_db]()
        self.user.keycloak_sub = "writer-sub"
        db.get(Post, 2).published_slug = "private-post"
        db.get(Post, 3).published_slug = "docker-volume"
        unlinked_post = db.get(Post, 5)
        unlinked_post.users.append(self.user)
        db.commit()
        self.client.app.include_router(users_router, prefix="/users")
        del self.client.headers["Authorization"]

        for path in ("/users/keycloak/writer-sub/posts", "/users/writer/posts"):
            with self.subTest(path=path), patch.object(settings, "FRONTEND_URL", "https://blog.example.com/"):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertEqual(data["total"], 2)
                urls = {post["id"]: post["url"] for post in data["items"]}
                self.assertEqual(urls, {3: "https://blog.example.com/blog/docker-volume/", 5: None})

    def test_update_preserves_omitted_slug_and_clears_explicit_null(self):
        path = "/posts/3"
        for fields, expected in (
            ({"published_slug": "docker-volume"}, "docker-volume"),
            ({}, "docker-volume"),
            ({"published_slug": None}, None),
        ):
            with self.subTest(fields=fields):
                response = self.client.put(path, json={"content": "Test", **fields})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["published_slug"], expected)

    def test_update_rejects_non_slug_links(self):
        for invalid in ("https://other.example/post", "../other", "post?x=1", ""):
            with self.subTest(invalid=invalid):
                response = self.client.put("/posts/3", json={"content": "Test", "published_slug": invalid})
                self.assertEqual(response.status_code, 422)
