from authlib.integrations.starlette_client import OAuth

from app.config import settings

oauth = OAuth()


def register_oauth_clients() -> None:
    if settings.google_client_id and settings.google_client_secret:
        oauth.register(
            name="google",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    if settings.facebook_app_id and settings.facebook_app_secret:
        oauth.register(
            name="facebook",
            client_id=settings.facebook_app_id,
            client_secret=settings.facebook_app_secret,
            authorize_url="https://www.facebook.com/v18.0/dialog/oauth",
            access_token_url="https://graph.facebook.com/v18.0/oauth/access_token",
            api_base_url="https://graph.facebook.com/v18.0/",
            client_kwargs={"scope": "email"},
        )


register_oauth_clients()
