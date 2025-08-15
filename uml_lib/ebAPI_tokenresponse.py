from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class eBuilderTokenResponse:
    access_token: str
    token_type: str
    expires_in: int

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "eBuilderTokenResponse":
        required = ("access_token", "token_type", "expires_in")
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"Missing keys in token response: {', '.join(missing)}")

        if not isinstance(data["access_token"], str):
            raise TypeError("access_token must be a string")
        if not isinstance(data["token_type"], str):
            raise TypeError("token_type must be a string")
        if not isinstance(data["expires_in"], int):
            # Some providers return numeric as string; try to coerce
            try:
                expires = int(data["expires_in"])
            except Exception as e:
                raise TypeError("expires_in must be an integer") from e
        else:
            expires = data["expires_in"]

        return eBuilderTokenResponse(
            access_token=data["access_token"],
            token_type=data["token_type"],
            expires_in=expires,
        )