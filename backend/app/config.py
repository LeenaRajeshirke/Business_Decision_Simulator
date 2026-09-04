import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/decision_simulator"
    )
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "none")  # "none" | "anthropic" | "openai" | ...
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "")

    SIMULATION_ITERATIONS: int = int(os.getenv("SIMULATION_ITERATIONS", "10000"))

    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    def validate(self):
        if not self.JWT_SECRET:
            raise RuntimeError(
                "JWT_SECRET is not set. Set it in your .env file — never hardcode it."
            )


settings = Settings()
