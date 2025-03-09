from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .user.views import router as auth_router
from .middleware.auth_middleware import CognitoAuthMiddleware

app = FastAPI(title="Social Sports App")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Cognito authentication middleware
app.add_middleware(CognitoAuthMiddleware)

# Include routers
app.include_router(auth_router, prefix="/v1")


@app.get("/")
def read_root():
    return {"message": "Welcome to Social Sports App API"}