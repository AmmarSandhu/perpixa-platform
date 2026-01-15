class LemonSqueezyProvider:
    def create_checkout(self, *, user_id: str, pack_id: str) -> dict:
        # v1: return hosted checkout URL created on LemonSqueezy dashboard
        return {
            "checkout_url": f"https://lemonsqueezy.com/checkout/{pack_id}"
        }

    def verify_webhook(self, payload: bytes, headers: dict) -> dict:
        # v1: validate signature (we’ll wire real validation next)
        return {"status": "paid"}
