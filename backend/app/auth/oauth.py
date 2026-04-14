"""OAuth provider support for Google, Apple, and GitHub.

Each provider handler validates the OAuth token/code and returns
the user's email, display name, and provider-specific ID.
"""

import httpx


class OAuthError(Exception):
    pass


async def verify_google_token(id_token: str) -> dict:
    """Verify a Google ID token and return user info."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token},
        )
    if resp.status_code != 200:
        raise OAuthError("Invalid Google token")
    data = resp.json()
    return {
        "email": data["email"],
        "display_name": data.get("name", data["email"]),
        "oauth_id": data["sub"],
        "provider": "google",
    }


async def verify_github_token(access_token: str) -> dict:
    """Verify a GitHub access token and return user info."""
    async with httpx.AsyncClient() as client:
        # Get user profile
        resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code != 200:
            raise OAuthError("Invalid GitHub token")
        user_data = resp.json()

        # Get primary email
        email_resp = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        emails = email_resp.json() if email_resp.status_code == 200 else []
        primary_email = next(
            (e["email"] for e in emails if e.get("primary")),
            user_data.get("email"),
        )

    if not primary_email:
        raise OAuthError("Could not retrieve email from GitHub")

    return {
        "email": primary_email,
        "display_name": user_data.get("name") or user_data["login"],
        "oauth_id": str(user_data["id"]),
        "provider": "github",
    }


async def verify_apple_token(id_token: str) -> dict:
    """Verify an Apple ID token and return user info.

    Apple Sign In uses JWTs signed by Apple's public keys.
    Full implementation requires fetching Apple's JWKS and verifying the token.
    """
    # TODO: Implement full Apple JWT verification (#16)
    # For now, this is a placeholder that will be completed when
    # Apple developer credentials are configured
    raise OAuthError("Apple Sign In not yet configured")


PROVIDERS = {
    "google": verify_google_token,
    "github": verify_github_token,
    "apple": verify_apple_token,
}


async def verify_oauth_token(provider: str, token: str) -> dict:
    handler = PROVIDERS.get(provider)
    if handler is None:
        raise OAuthError(f"Unsupported OAuth provider: {provider}")
    return await handler(token)
