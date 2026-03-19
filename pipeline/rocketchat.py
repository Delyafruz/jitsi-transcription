import os
import logging
import requests
 
logger = logging.getLogger(__name__)
 
ROCKETCHAT_URL = os.getenv("ROCKETCHAT_URL", "http://rocketchat:3000")
ROCKETCHAT_USER = os.getenv("ROCKETCHAT_USER", "transcription-bot")
ROCKETCHAT_PASSWORD = os.getenv("ROCKETCHAT_PASSWORD", "")
ROCKETCHAT_TOKEN = os.getenv("ROCKETCHAT_TOKEN", "")   # personal access token (альтернатива)
ROCKETCHAT_USER_ID = os.getenv("ROCKETCHAT_USER_ID", "")
ROCKETCHAT_CHANNEL = os.getenv("ROCKETCHAT_CHANNEL", "#general")
 
_auth_token = None
_auth_user_id = None
 
 
def _login() -> tuple[str, str]:
    """Login to Rocket.Chat and get auth token."""
    global _auth_token, _auth_user_id
 
    if _auth_token and _auth_user_id:
        return _auth_token, _auth_user_id
 
    # Use personal access token if provided
    if ROCKETCHAT_TOKEN and ROCKETCHAT_USER_ID:
        _auth_token = ROCKETCHAT_TOKEN
        _auth_user_id = ROCKETCHAT_USER_ID
        return _auth_token, _auth_user_id
 
    # Otherwise login with username/password
    response = requests.post(
        f"{ROCKETCHAT_URL}/api/v1/login",
        json={"user": ROCKETCHAT_USER, "password": ROCKETCHAT_PASSWORD},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
 
    if data.get("status") != "success":
        raise ValueError(f"Rocket.Chat login failed: {data.get('message')}")
 
    _auth_token = data["data"]["authToken"]
    _auth_user_id = data["data"]["userId"]
    logger.info("Logged in to Rocket.Chat successfully")
    return _auth_token, _auth_user_id
 
 
def send_to_rocketchat(message: str) -> bool:
    """Send message to Rocket.Chat channel."""
    if not ROCKETCHAT_URL or not ROCKETCHAT_CHANNEL:
        logger.warning("Rocket.Chat not configured, skipping send")
        return False
 
    try:
        token, user_id = _login()
 
        response = requests.post(
            f"{ROCKETCHAT_URL}/api/v1/chat.postMessage",
            headers={
                "X-Auth-Token": token,
                "X-User-Id": user_id,
                "Content-Type": "application/json",
            },
            json={
                "channel": ROCKETCHAT_CHANNEL,
                "text": message,
                "parseUrls": False,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
 
        if data.get("success"):
            logger.info(f"Message sent to {ROCKETCHAT_CHANNEL}")
            return True
        else:
            logger.error(f"Rocket.Chat send failed: {data}")
            return False
 
    except Exception as e:
        logger.error(f"Failed to send to Rocket.Chat: {e}")
        return False