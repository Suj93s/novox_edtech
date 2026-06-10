from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.health import router as health_router
from api.chat import router as chat_router
from api.webhook import router as webhook_router
from api.documents import router as documents_router

app = FastAPI(
    title="Novox Mentor AI Backend",
    description="Backend for the Student Learning Chatbot",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(webhook_router, prefix="/api")
app.include_router(documents_router, prefix="/api")



# Vercel requires the app variable to be available here, which it is.
