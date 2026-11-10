import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jose import jwt
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
    from app.api.deps import get_current_user, get_optional_current_user
    from app.api.v1.endpoints.auth import router
    from app.core.config import settings
    from app.core.security import create_access_token, create_refresh_token
    from app.db.database import Base, get_db
    from app.db.models import User


class TokenTypesTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
        )
        self.addCleanup(engine.dispose)
        Base.metadata.create_all(engine)
        db = Session(engine)
        self.addCleanup(db.close)
        db.add(User(
            username="writer", keycloak_sub="test-sub",
            email="writer@example.com", hashed_password="test",
        ))
        db.commit()

        app = FastAPI()
        app.include_router(router, prefix="/auth")
        app.dependency_overrides[get_db] = lambda: db

        @app.get("/required")
        def required(user=Depends(get_current_user)):
            return {"username": user.username}

        @app.get("/optional")
        def optional(user=Depends(get_optional_current_user)):
            return {"username": user.username if user else None}

        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def encode(self, **claims):
        return jwt.encode(
            {"sub": "writer", "exp": datetime.now(timezone.utc) + timedelta(minutes=5), **claims},
            settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM,
        )

    def test_generated_tokens_have_fixed_types(self):
        for factory, expected in [(create_access_token, "access"), (create_refresh_token, "refresh")]:
            with self.subTest(expected=expected):
                token = factory({"sub": "writer", "token_type": "wrong"})
                claims = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
                self.assertEqual(claims["token_type"], expected)

    def test_access_authenticates_username_and_keycloak_subject(self):
        for subject in ["writer", "test-sub"]:
            with self.subTest(subject=subject):
                token = create_access_token({"sub": subject})
                for path in ["/required", "/optional"]:
                    response = self.client.get(path, headers={"Authorization": f"Bearer {token}"})
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json()["username"], "writer")

    def test_refresh_cannot_authenticate(self):
        token = create_refresh_token({"sub": "writer"})
        headers = {"Authorization": f"Bearer {token}"}
        self.assertEqual(self.client.get("/required", headers=headers).status_code, 401)
        self.assertIsNone(self.client.get("/optional", headers=headers).json()["username"])

    def test_access_cannot_refresh(self):
        response = self.client.post("/auth/refresh", json={
            "refresh_token": create_access_token({"sub": "writer"}),
        })
        self.assertEqual(response.status_code, 401)

    def test_refresh_returns_usable_access_token(self):
        for subject in ["writer", "test-sub"]:
            with self.subTest(subject=subject):
                refresh = create_refresh_token({"sub": subject})
                response = self.client.post("/auth/refresh", json={"refresh_token": refresh})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["refresh_token"], refresh)
                access = response.json()["access_token"]
                headers = {"Authorization": f"Bearer {access}"}
                self.assertEqual(self.client.get("/required", headers=headers).status_code, 200)
                self.assertEqual(self.client.post("/auth/refresh", json={"refresh_token": access}).status_code, 401)

    def test_legacy_and_unknown_types_are_rejected(self):
        for claims in [{}, {"token_type": "unknown"}]:
            with self.subTest(claims=claims):
                token = self.encode(**claims)
                headers = {"Authorization": f"Bearer {token}"}
                self.assertEqual(self.client.get("/required", headers=headers).status_code, 401)
                self.assertIsNone(self.client.get("/optional", headers=headers).json()["username"])
                self.assertEqual(self.client.post("/auth/refresh", json={"refresh_token": token}).status_code, 401)

    def test_expired_tokens_are_rejected(self):
        for factory in [create_access_token, create_refresh_token]:
            with self.subTest(factory=factory.__name__):
                token = factory({"sub": "writer"}, expires_delta=timedelta(seconds=-1))
                self.assertEqual(self.client.get("/required", headers={"Authorization": f"Bearer {token}"}).status_code, 401)
                self.assertEqual(self.client.post("/auth/refresh", json={"refresh_token": token}).status_code, 401)

    def test_invalid_subjects_are_rejected(self):
        for subject in [None, "", "missing-user", 123]:
            with self.subTest(subject=subject):
                access = create_access_token({"sub": subject})
                refresh = create_refresh_token({"sub": subject})
                headers = {"Authorization": f"Bearer {access}"}
                self.assertEqual(self.client.get("/required", headers=headers).status_code, 401)
                self.assertIsNone(self.client.get("/optional", headers=headers).json()["username"])
                self.assertEqual(self.client.post("/auth/refresh", json={"refresh_token": refresh}).status_code, 401)
