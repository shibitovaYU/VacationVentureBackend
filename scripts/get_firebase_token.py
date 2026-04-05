import argparse
import json
import os
import sys

import requests


FIREBASE_SIGN_IN_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Get Firebase ID token for Postman using email/password auth."
    )
    parser.add_argument("--email", required=True, help="Firebase user email")
    parser.add_argument("--password", required=True, help="Firebase user password")
    parser.add_argument(
        "--api-key",
        default=os.getenv("FIREBASE_WEB_API_KEY"),
        help="Firebase Web API key. Defaults to FIREBASE_WEB_API_KEY",
    )
    parser.add_argument(
        "--show-response",
        action="store_true",
        help="Print the full Firebase response as JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.api_key:
        print(
            "Missing Firebase Web API key. "
            "Pass --api-key or set FIREBASE_WEB_API_KEY.",
            file=sys.stderr,
        )
        return 1

    response = requests.post(
        FIREBASE_SIGN_IN_URL,
        params={"key": args.api_key},
        json={
            "email": args.email,
            "password": args.password,
            "returnSecureToken": True,
        },
        timeout=30,
    )

    if response.status_code != 200:
        print("Firebase sign-in failed.", file=sys.stderr)
        try:
            error_payload = response.json()
        except ValueError:
            print(response.text, file=sys.stderr)
            return 1

        print(json.dumps(error_payload, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    payload = response.json()
    if args.show_response:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    id_token = payload.get("idToken")
    if not id_token:
        print("Firebase response does not contain idToken.", file=sys.stderr)
        return 1

    print(id_token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
