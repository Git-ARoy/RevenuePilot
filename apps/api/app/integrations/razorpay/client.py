"""
Razorpay Client — HTTP adapter for Razorpay REST API.

Isolates all Razorpay HTTP details, authentication, error mapping,
and retries behind a clean interface.

All methods use async httpx. The orchestration layer never sees
Razorpay HTTP specifics.
"""
import httpx
from typing import Optional, Any
from dataclasses import dataclass

from app.core.config import settings


RAZORPAY_BASE_URL = "https://api.razorpay.com/v1"


@dataclass
class RazorpayError:
    """Normalized Razorpay API error."""
    code: str
    description: str
    status_code: int
    raw: dict


class RazorpayClient:
    """
    Async HTTP client for Razorpay REST API.
    
    Uses Basic Auth with KEY_ID:KEY_SECRET.
    All methods return parsed JSON responses.
    """

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
    ):
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET
        self.base_url = RAZORPAY_BASE_URL

    def _get_client(self) -> httpx.AsyncClient:
        """Create an authenticated httpx client."""
        return httpx.AsyncClient(
            base_url=self.base_url,
            auth=(self.key_id, self.key_secret),
            timeout=30.0,
            headers={
                "Content-Type": "application/json",
            },
        )

    async def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict:
        """Make an authenticated request to Razorpay."""
        async with self._get_client() as client:
            response = await client.request(
                method=method,
                url=path,
                json=json_data,
                params=params,
            )

            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error_info = error_data.get("error", {})
                raise RazorpayAPIError(
                    RazorpayError(
                        code=error_info.get("code", "UNKNOWN_ERROR"),
                        description=error_info.get(
                            "description", response.text
                        ),
                        status_code=response.status_code,
                        raw=error_data,
                    )
                )

            return response.json()

    # --- Orders ---

    async def create_order(
        self,
        amount: int,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[dict] = None,
    ) -> dict:
        """Create a Razorpay order."""
        payload: dict[str, Any] = {
            "amount": amount,
            "currency": currency,
        }
        if receipt:
            payload["receipt"] = receipt
        if notes:
            payload["notes"] = notes
        return await self._request("POST", "/orders", json_data=payload)

    async def get_order(self, order_id: str) -> dict:
        """Fetch a Razorpay order by ID."""
        return await self._request("GET", f"/orders/{order_id}")

    async def get_order_payments(self, order_id: str) -> dict:
        """Get all payments for an order."""
        return await self._request("GET", f"/orders/{order_id}/payments")

    # --- Payments ---

    async def get_payment(self, payment_id: str) -> dict:
        """Fetch a Razorpay payment by ID."""
        return await self._request("GET", f"/payments/{payment_id}")

    async def capture_payment(
        self, payment_id: str, amount: int, currency: str = "INR"
    ) -> dict:
        """Capture an authorized payment. NOT a recovery mechanism."""
        return await self._request(
            "POST",
            f"/payments/{payment_id}/capture",
            json_data={"amount": amount, "currency": currency},
        )

    # --- Payment Links ---

    async def create_payment_link(
        self,
        amount: int,
        currency: str = "INR",
        description: Optional[str] = None,
        customer: Optional[dict] = None,
        notify: Optional[dict] = None,
        reminder_enable: bool = True,
        notes: Optional[dict] = None,
        callback_url: Optional[str] = None,
        callback_method: str = "get",
        expire_by: Optional[int] = None,
    ) -> dict:
        """
        Create a Razorpay Payment Link.
        
        This is the primary recovery action — sends a payment URL
        to the customer for re-payment.
        """
        payload: dict[str, Any] = {
            "amount": amount,
            "currency": currency,
            "reminder_enable": reminder_enable,
        }
        if description:
            payload["description"] = description
        if customer:
            payload["customer"] = customer
        if notify:
            payload["notify"] = notify
        if notes:
            payload["notes"] = notes
        if callback_url:
            payload["callback_url"] = callback_url
            payload["callback_method"] = callback_method
        if expire_by:
            payload["expire_by"] = expire_by

        return await self._request(
            "POST", "/payment_links", json_data=payload
        )

    async def get_payment_link(self, link_id: str) -> dict:
        """Fetch a payment link by ID."""
        return await self._request("GET", f"/payment_links/{link_id}")

    async def resend_payment_link(
        self, link_id: str, medium: str = "sms"
    ) -> dict:
        """Resend a payment link notification."""
        return await self._request(
            "POST",
            f"/payment_links/{link_id}/notify_by/{medium}",
        )

    async def cancel_payment_link(self, link_id: str) -> dict:
        """Cancel a payment link."""
        return await self._request(
            "POST", f"/payment_links/{link_id}/cancel"
        )


class RazorpayAPIError(Exception):
    """Exception for Razorpay API errors."""

    def __init__(self, error: RazorpayError):
        self.error = error
        super().__init__(
            f"Razorpay API Error [{error.status_code}] {error.code}: {error.description}"
        )
