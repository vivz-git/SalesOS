from typing import Any, Literal, cast

import httpx
from pydantic import BaseModel

HUBSPOT_OAUTH_TOKEN_URL = "https://api.hubapi.com/oauth/v3/token"
HUBSPOT_API_BASE = "https://api.hubapi.com"


class HubSpotTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


class HubSpotAssociationType(BaseModel):
    category: str = "HUBSPOT_DEFINED"
    type_id: int = 1
    label: str | None = None


class HubSpotCRMAdapter:
    """Production adapter for HubSpot OAuth v3 and CRM v3/v4 APIs."""

    def __init__(self, http_client: httpx.Client | None = None) -> None:
        self._http = http_client or httpx.Client(timeout=15.0)

    def exchange_code(
        self, code: str, redirect_uri: str, client_id: str, client_secret: str
    ) -> HubSpotTokenResponse:
        """Exchanges OAuth authorization code for access and refresh tokens using v3 API."""
        payload = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        }
        res = self._http.post(HUBSPOT_OAUTH_TOKEN_URL, data=payload)
        res.raise_for_status()
        data = res.json()
        return HubSpotTokenResponse(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_in=data["expires_in"],
            token_type=data.get("token_type", "bearer"),
        )

    def refresh_access_token(
        self, refresh_token: str, client_id: str, client_secret: str
    ) -> HubSpotTokenResponse:
        """Refreshes expired access token using OAuth v3 token API."""
        payload = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        }
        res = self._http.post(HUBSPOT_OAUTH_TOKEN_URL, data=payload)
        res.raise_for_status()
        data = res.json()
        return HubSpotTokenResponse(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", refresh_token),
            expires_in=data["expires_in"],
            token_type=data.get("token_type", "bearer"),
        )

    def resolve_association_type(
        self, access_token: str, from_type: str, to_type: str
    ) -> HubSpotAssociationType:
        """Dynamically resolves the valid association category and typeId via GET /crm/v4/associations/{fromType}/{toType}/labels."""
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{HUBSPOT_API_BASE}/crm/v4/associations/{from_type}/{to_type}/labels"
        try:
            res = self._http.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                results = data.get("results", [])
                if results:
                    first = results[0]
                    return HubSpotAssociationType(
                        category=first.get("category", "HUBSPOT_DEFINED"),
                        type_id=int(first.get("typeId", 1)),
                        label=first.get("label"),
                    )
        except Exception:
            pass
        return HubSpotAssociationType(category="HUBSPOT_DEFINED", type_id=1)

    def create_or_update_contact(
        self,
        access_token: str,
        email: str,
        first_name: str | None = None,
        last_name: str | None = None,
        job_title: str | None = None,
        existing_hubspot_id: str | None = None,
    ) -> dict[str, Any]:
        """Creates or updates a HubSpot Contact via v3 API."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        props: dict[str, Any] = {"email": email}
        if first_name:
            props["firstname"] = first_name
        if last_name:
            props["lastname"] = last_name
        if job_title:
            props["jobtitle"] = job_title

        if existing_hubspot_id:
            url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{existing_hubspot_id}"
            res = self._http.patch(url, headers=headers, json={"properties": props})
            if res.status_code == 200:
                return cast(dict[str, Any], res.json())

        url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts"
        res = self._http.post(url, headers=headers, json={"properties": props})
        res.raise_for_status()
        return cast(dict[str, Any], res.json())

    def create_or_update_company(
        self,
        access_token: str,
        domain: str,
        name: str,
        industry: str | None = None,
        existing_hubspot_id: str | None = None,
    ) -> dict[str, Any]:
        """Creates or updates a HubSpot Company via v3 API."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        props: dict[str, Any] = {"domain": domain, "name": name}
        if industry:
            props["industry"] = industry

        if existing_hubspot_id:
            url = f"{HUBSPOT_API_BASE}/crm/v3/objects/companies/{existing_hubspot_id}"
            res = self._http.patch(url, headers=headers, json={"properties": props})
            if res.status_code == 200:
                return cast(dict[str, Any], res.json())

        url = f"{HUBSPOT_API_BASE}/crm/v3/objects/companies"
        res = self._http.post(url, headers=headers, json={"properties": props})
        res.raise_for_status()
        return cast(dict[str, Any], res.json())

    def create_sales_email_activity(
        self,
        access_token: str,
        subject: str,
        body: str,
        direction: Literal["EMAIL", "INBOUND_EMAIL"] = "EMAIL",
        status: str = "SENT",
    ) -> dict[str, Any]:
        """Creates a Sales Email Activity Engagement in HubSpot v3."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        url = f"{HUBSPOT_API_BASE}/crm/v3/objects/emails"
        payload = {
            "properties": {
                "hs_email_direction": direction,
                "hs_email_status": status,
                "hs_email_subject": subject,
                "hs_email_text": body,
            }
        }
        res = self._http.post(url, headers=headers, json=payload)
        res.raise_for_status()
        return cast(dict[str, Any], res.json())

    def associate_objects(
        self,
        access_token: str,
        from_type: str,
        from_id: str,
        to_type: str,
        to_id: str,
        assoc_type: HubSpotAssociationType | None = None,
    ) -> bool:
        """Associates two HubSpot objects using dynamically resolved v4 association labels."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        resolved = assoc_type or self.resolve_association_type(access_token, from_type, to_type)
        url = f"{HUBSPOT_API_BASE}/crm/v3/objects/{from_type}/{from_id}/associations/{to_type}/{to_id}/{resolved.category}/{resolved.type_id}"
        res = self._http.put(url, headers=headers)
        return res.status_code in (200, 201, 204)
