"""Amazon Creators API の最小クライアント（標準ライブラリのみ）。

認証情報は環境変数から読む:
  CREATORS_CREDENTIAL_ID / CREATORS_CREDENTIAL_SECRET / CREATORS_CREDENTIAL_VERSION
  PARTNER_TAG（例: xxxx-22）
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

API_BASE = "https://creatorsapi.amazon/catalog/v1"
MARKETPLACE = "www.amazon.co.jp"

# v3.x は Login with Amazon（地域ごと）。日本は FE = 3.3。
LWA_TOKEN_ENDPOINTS = {
    "3.1": "https://api.amazon.com/auth/o2/token",
    "3.2": "https://api.amazon.co.uk/auth/o2/token",
    "3.3": "https://api.amazon.co.jp/auth/o2/token",
}
# v2.x（旧形式）は Cognito。地域ごとのURLが異なる場合は環境変数で上書きする。
COGNITO_TOKEN_ENDPOINT = os.environ.get(
    "CREATORS_COGNITO_ENDPOINT",
    "https://creatorsapi.auth.us-west-2.amazoncognito.com/oauth2/token",
)

OFFER_RESOURCES = [
    "itemInfo.title",
    "images.primary.medium",
    "offersV2.listings.availability",
    "offersV2.listings.condition",
    "offersV2.listings.isBuyBoxWinner",
    "offersV2.listings.merchantInfo",
    "offersV2.listings.price",
    "offersV2.listings.loyaltyPoints",
]


class CreatorsAPIError(RuntimeError):
    pass


class CreatorsClient:
    def __init__(self) -> None:
        self.cred_id = os.environ["CREATORS_CREDENTIAL_ID"]
        self.cred_secret = os.environ["CREATORS_CREDENTIAL_SECRET"]
        self.version = os.environ.get("CREATORS_CREDENTIAL_VERSION", "3.3")
        self.partner_tag = os.environ["PARTNER_TAG"]
        self._token: str | None = None
        self._token_exp = 0.0
        self._last_call = 0.0

    # ---- 認証 ----
    def _fetch_token(self) -> None:
        if self.version.startswith("3."):
            url = LWA_TOKEN_ENDPOINTS.get(self.version)
            if not url:
                raise CreatorsAPIError(f"未対応の認証バージョン: {self.version}")
            body = json.dumps({
                "grant_type": "client_credentials",
                "client_id": self.cred_id,
                "client_secret": self.cred_secret,
                "scope": "creatorsapi::default",
            }).encode()
            headers = {"Content-Type": "application/json"}
        else:
            from urllib.parse import urlencode
            body = urlencode({
                "grant_type": "client_credentials",
                "client_id": self.cred_id,
                "client_secret": self.cred_secret,
                "scope": "creatorsapi/default",
            }).encode()
            url = COGNITO_TOKEN_ENDPOINT
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = self._http(url, body, headers)
        self._token = data["access_token"]
        self._token_exp = time.time() + int(data.get("expires_in", 3600)) - 120

    def _auth_header(self) -> str:
        if not self._token or time.time() > self._token_exp:
            self._fetch_token()
        if self.version.startswith("2."):
            return f"Bearer {self._token}, Version {self.version}"
        return f"Bearer {self._token}"

    # ---- HTTP ----
    @staticmethod
    def _http(url: str, body: bytes, headers: dict) -> dict:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            raise CreatorsAPIError(f"HTTP {e.code} {url}: {detail}") from None

    def _call(self, operation: str, payload: dict) -> dict:
        # 1秒1回（初期上限）を守る
        wait = 1.05 - (time.time() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.time()
        payload = {"partnerTag": self.partner_tag, "marketplace": MARKETPLACE, **payload}
        headers = {
            "Authorization": self._auth_header(),
            "Content-Type": "application/json",
            "x-marketplace": MARKETPLACE,
        }
        return self._http(f"{API_BASE}/{operation}", json.dumps(payload).encode(), headers)

    # ---- 操作 ----
    def get_items(self, asins: list[str]) -> list[dict]:
        """ASINを10件ずつ照会して item のリストを返す。"""
        items: list[dict] = []
        for i in range(0, len(asins), 10):
            chunk = asins[i:i + 10]
            data = self._call("getItems", {
                "itemIds": chunk,
                "itemIdType": "ASIN",
                "languagesOfPreference": ["ja_JP"],
                "resources": OFFER_RESOURCES,
            })
            items.extend(_find_items(data))
        return items

    def search_items(self, keywords: str, page: int = 1, **filters) -> list[dict]:
        data = self._call("searchItems", {
            "keywords": keywords,
            "itemPage": page,
            "itemCount": 10,
            "languagesOfPreference": ["ja_JP"],
            "resources": ["itemInfo.title", "itemInfo.byLineInfo"],
            **filters,
        })
        return _find_items(data)


def _find_items(data: dict) -> list[dict]:
    """レスポンスの入れ物名の揺れ（itemsResult / ItemsResult など）に耐える。"""
    for key in ("itemsResult", "ItemsResult", "searchResult", "SearchResult"):
        block = data.get(key)
        if isinstance(block, dict):
            return block.get("items") or block.get("Items") or []
    return data.get("items", [])
