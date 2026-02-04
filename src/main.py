from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from webexapp import routes

app = FastAPI(
    title="UnifyX",
    description="Unified platform for managing CUCM and Webex user configurations, "
                "LDAP updates, license management, and route pattern operations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(routes.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
