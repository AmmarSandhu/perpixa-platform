import os

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

VIDEO_JOB_COST = 10  # v1 flat pricing

ENABLE_MOCK_PAYMENTS = True


CREDIT_PACKS = {
    "starter": {"usd": 10, "credits": 100},
    "pro": {"usd": 25, "credits": 300},
    "power": {"usd": 50, "credits": 700},
}
