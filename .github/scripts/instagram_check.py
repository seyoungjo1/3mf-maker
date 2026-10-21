"""Read-only Instagram Login connection check; never print API bodies or secrets."""
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request


def check(config, token, opener=urllib.request.urlopen):
    if not token or not token.strip():
        return {"ok": False, "reason": "missing_IG_ACCESS_TOKEN"}
    account = str(config["user_id"])
    version = config["api_version"]
    if not re.fullmatch(r"\d+", account) or not re.fullmatch(r"v\d+\.\d+", version):
        return {"ok": False, "reason": "invalid_config"}
    request = urllib.request.Request(
        f"https://graph.instagram.com/{version}/me?fields=user_id,username",
        headers={"Authorization": "Bearer " + token.strip()},
        method="GET",
    )
    try:
        with opener(request, timeout=30) as response:
            body = json.loads(response.read(65536))
    except urllib.error.HTTPError as exc:
        # Error messages and URLs may contain credentials. Only retain numeric codes.
        result = {"ok": False, "reason": "meta_api_error", "http_status": exc.code}
        try:
            error = json.loads(exc.read(65536)).get("error", {})
            for key in ("code", "error_subcode"):
                if isinstance(error.get(key), int):
                    result[key] = error[key]
        except (ValueError, TypeError, AttributeError):
            pass
        return result
    except Exception:
        return {"ok": False, "reason": "network_or_response_error"}
    if not isinstance(body, dict):
        return {"ok": False, "reason": "invalid_profile_response"}
    actual_id = str(body.get("user_id", ""))
    username = body.get("username", "")
    if actual_id != account:
        return {"ok": False, "reason": "account_id_mismatch"}
    if not isinstance(username, str) or not re.fullmatch(r"[A-Za-z0-9_.]{1,30}", username):
        return {"ok": False, "reason": "invalid_username"}
    expected = config.get("expected_username", "").lstrip("@")
    if expected and username.lower() != expected.lower():
        return {"ok": False, "reason": "username_mismatch"}
    return {"ok": True, "user_id": actual_id, "username": username,
            "api_version": version, "check": "profile_read_only",
            "publishing_permission_verified": False}


if __name__ == "__main__":
    config = json.loads(Path("instagram/config.json").read_text())
    result = check(config, os.environ.get("IG_ACCESS_TOKEN", ""))
    # This file contains only the allowlisted result fields above.
    output = Path("instagram/connection-status.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))
