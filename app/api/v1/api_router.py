from fastapi import APIRouter
from app.api.v1.endpoints import auth, posts, users, images, keycloak_auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(images.router, prefix="/images", tags=["images"])
api_router.include_router(keycloak_auth.router, prefix="/auth", tags=["auth"])
