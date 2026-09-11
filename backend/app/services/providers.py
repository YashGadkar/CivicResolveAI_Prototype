from dataclasses import dataclass
from typing import Protocol


class OtpProvider(Protocol):
    def send_code(self, destination: str, code: str) -> None: ...


class NotificationProvider(Protocol):
    def send(self, destination: str, message: str) -> None: ...


class EvidenceStorageProvider(Protocol):
    def put(self, object_name: str, content: bytes, content_type: str) -> str: ...


class ImageAnalysisProvider(Protocol):
    def describe_civic_evidence(self, content: bytes, content_type: str) -> str: ...


@dataclass(frozen=True)
class ProviderUnavailable(RuntimeError):
    capability: str

    def __str__(self) -> str:
        return f"{self.capability} provider is not configured for this deployment."


class DisabledOtpProvider:
    def send_code(self, destination: str, code: str) -> None:
        raise ProviderUnavailable("OTP")


class DisabledNotificationProvider:
    def send(self, destination: str, message: str) -> None:
        raise ProviderUnavailable("Notification")


class DisabledImageAnalysisProvider:
    def describe_civic_evidence(self, content: bytes, content_type: str) -> str:
        raise ProviderUnavailable("Image analysis")


# These contracts deliberately keep provider-specific SDKs out of civic domain logic.
# Production deployments can implement adapters for an approved email/SMS service,
# WhatsApp Business provider, object storage service and image-analysis provider while
# the local hackathon build stays runnable without secrets or falsely claiming delivery.
