from abc import ABC, abstractmethod


class PaymentProvider(ABC):
    @abstractmethod
    def create_checkout(self, *, user_id: str, pack_id: str) -> dict:
        pass

    @abstractmethod
    def verify_webhook(self, payload: bytes, headers: dict) -> dict:
        pass
