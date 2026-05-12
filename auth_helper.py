import os
import json
import hashlib
import base64
import secrets
import webbrowser
from urllib.parse import urlencode
import requests
from dotenv import load_dotenv

load_dotenv()

# ================== CONFIG ==================
CLIENT_ID = os.getenv("ETSY_CLIENT_ID")
REDIRECT_URI = os.getenv("ETSY_REDIRECT_URI", "http://localhost:3000/oauth/redirect")

# Scopes - add/remove as needed
SCOPES = [
    "listings_r", "listings_w",     # Read + Write listings
    "transactions_r",               # Read orders & sales data
    "shops_r",                      # Shop information
    # "email_r",                    # Your email (if needed)
]

TOKEN_FILE = "etsy_tokens.json"
# ===========================================


class EtsyAuthHelper:
    """Helper class to handle Etsy OAuth 2.0 with PKCE"""

    def __init__(self):
        self.client_id = CLIENT_ID
        self.redirect_uri = REDIRECT_URI
        self.scopes = " ".join(SCOPES)

    @staticmethod
    def generate_pkce_pair():
        """Generate code_verifier and code_challenge for PKCE"""
        code_verifier = secrets.token_urlsafe(64)  # 43-128 chars
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).rstrip(b'=').decode('utf-8')
        
        return code_verifier, code_challenge

    def get_authorization_url(self):
        """Step 1: Generate URL to open in browser"""
        code_verifier, code_challenge = self.generate_pkce_pair()
        
        # Save verifier temporarily (you can improve this with a session store later)
        with open("pkce_temp.json", "w") as f:
            json.dump({"code_verifier": code_verifier}, f)

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scopes,
            "state": secrets.token_urlsafe(16),
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }

        auth_url = f"https://www.etsy.com/oauth/connect?{urlencode(params)}"
        print("🔗 Opening Etsy Authorization Page...")
        webbrowser.open(auth_url)
        print(f"\nIf browser didn't open, go here manually:\n{auth_url}\n")
        return auth_url

    def exchange_code_for_token(self, auth_code: str):
        """Step 2: Exchange authorization code for access token"""
        try:
            with open("pkce_temp.json", "r") as f:
                data = json.load(f)
                code_verifier = data["code_verifier"]
        except FileNotFoundError:
            print("❌ pkce_temp.json not found. Run get_authorization_url() first.")
            return None

        token_url = "https://api.etsy.com/v3/public/oauth/token"

        payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code": auth_code,
            "code_verifier": code_verifier
        }

        response = requests.post(token_url, data=payload)

        if response.status_code == 200:
            token_data = response.json()
            print("✅ Authorization successful! Token received.")
            
            # Save tokens
            with open(TOKEN_FILE, "w") as f:
                json.dump(token_data, f, indent=2)
            
            print(f"Tokens saved to {TOKEN_FILE}")
            return token_data
        else:
            print("❌ Failed to get token:")
            print(response.text)
            return None


def load_token():
    """Load saved token"""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return None


def test_connection(access_token: str):
    """Test API call - get your shop info"""
    headers = {
        "x-api-key": CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(
        "https://api.etsy.com/v3/application/shops/__SELF__",
        headers=headers
    )

    if response.status_code == 200:
        print("✅ API connection successful!")
        print(json.dumps(response.json(), indent=2))
    else:
        print("❌ API test failed:", response.text)


# ================== USAGE EXAMPLE ==================
if __name__ == "__main__":
    helper = EtsyAuthHelper()
    
    print("🚀 Etsy API Authentication Helper")
    choice = input("1. Start new authorization\n2. Test existing token\nChoose (1/2): ")
    
    if choice == "1":
        helper.get_authorization_url()
        print("\nAfter approving in browser, copy the 'code' from the redirect URL")
        auth_code = input("Paste the authorization code here: ").strip()
        helper.exchange_code_for_token(auth_code)
    
    elif choice == "2":
        token_data = load_token()
        if token_data and "access_token" in token_data:
            test_connection(token_data["access_token"])
        else:
            print("No valid token found. Run authorization first.")
