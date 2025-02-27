import os
import time
import requests
import base64
from datetime import datetime, timedelta

KHAN_USERNAME = "usernamebich"
KHAN_PASSWORD = "passwordbich"
DEVICE_ID = "DEVICEID-1234-4567-8901-DEVICEIDBICH"
KHAN_ACCOUNT = "5041409848"

# Constants
HOST = "api.khanbank.com:9003"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
    "Accept-Language": "mn-MN",
    "Device-id": DEVICE_ID,
    "Content-Type": "application/x-www-form-urlencoded",
    "Secure": "yes",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*"
}

class KhanBankAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.token_object = {
            "access_token": "",
            "access_token_expires_in": int(time.time()),
            "refresh_token": "",
            "refresh_token_status": "approved",
            "refresh_token_expires_in": int(time.time()),
            "first_name": "",
            "last_name": "",
        }

    def get_now(self):
        return int(time.time())

    def date_to_iso(self, date=None):
        if date is None:
            date = datetime.utcnow()
        elif isinstance(date, int):
            date = datetime.fromtimestamp(date)
        elif isinstance(date, str):
            date = datetime.fromisoformat(date)  # Convert ISO string to datetime
        return date.isoformat()[:19]

    def stringify_params(self, params):
        if not params:
            return ""
        return "&".join(f"{key}={value}" for key, value in params.items())

    def get_token(self):
        payload = {
            "grant_type": "password",
            "username": KHAN_USERNAME,
            "password": base64.b64encode(KHAN_PASSWORD.encode()).decode(),
            "channelId": "I",
            "languageId": "003",
        }
        response = self.session.post(
            f"https://{HOST}/v1/cfrm/auth/token?grant_type=password",
            json=payload,
            headers={
                **HEADERS,
                "Authorization": "Basic Vm00eHFtV1BaQks3Vm5UYjNRRXJZbjlJZkxoWmF6enI6dElJQkFsU09pVXIwclV5cA=="
            }
        )
        if response.status_code in {200, 201, 202}:
            data = response.json()
            self.token_object.update({
                "access_token": data["access_token"],
                "access_token_expires_in": self.get_now() + int(data["access_token_expires_in"]),  # Ensure integer
                "refresh_token": data["refresh_token"],
                "refresh_token_expires_in": self.get_now() + int(data["refresh_token_expires_in"]),  # Ensure integer
                "refresh_token_status": data["refresh_token_status"],
                "first_name": data["first_name"],
                "last_name": data["last_name"],
            })
            return data["access_token"]
        raise Exception(f"Failed to get token: {response.text}")

    def refresh_token(self):
        response = self.session.post(
            f"https://{HOST}/v1/cfrm/auth/token?grant_type=refresh_token&refresh_token={self.token_object['refresh_token']}",
            json={},
            headers={
                **HEADERS,
                "Authorization": "Basic Vm00eHFtV1BaQks3Vm5UYjNRRXJZbjlJZkxoWmF6enI6dElJQkFsU09pVXIwclV5cA=="
            }
        )
        if response.status_code in {200, 201, 202}:
            data = response.json()
            self.token_object.update({
                "access_token": data["access_token"],
                "access_token_expires_in": self.get_now() + int(data["access_token_expires_in"]),  # Ensure integer
                "refresh_token": data["refresh_token"],
                "refresh_token_expires_in": self.get_now() + int(data["refresh_token_expires_in"]),  # Ensure integer
                "refresh_token_status": data["refresh_token_status"],
            })
            return data["access_token"]
        raise Exception(f"Failed to refresh token: {response.text}")


    def check_token(self):
        if self.token_object["access_token"] and self.get_now() < self.token_object["access_token_expires_in"]:
            return self.token_object["access_token"]
        if self.token_object["refresh_token"] and self.get_now() < self.token_object["refresh_token_expires_in"]:
            return self.refresh_token()
        return self.get_token()

    def get_transactions(self, account, start_date=None, end_date=None):
        if not account:
            account = KHAN_ACCOUNT
        if not start_date:
            start_date = self.get_now() - 86400
        if not end_date:
            end_date = self.get_now()

        params = {
            "transactionValue": 0,
            "transactionDate": f'{{"lt":"{self.date_to_iso(start_date)}","gt":"{self.date_to_iso(end_date)}"}}',
            "amount": '{"lt":"0","gt":"0"}',
            # "amountType": "04",
            "transactionCurrency": "MNT",
            "branchCode": account[:4] if len(account) > 4 else account,
        }
        url = f"https://{HOST}/v1/omni/user/custom/operativeaccounts/{account}/transactions?{self.stringify_params(params)}"
        headers = {
            "Authorization": f"Bearer {self.check_token()}",
            "Content-Type": "application/json"
        }
        response = self.session.get(url, headers=headers)
        if response.status_code in {200, 201, 202}:
            return response.json()
        raise Exception(f"Failed to fetch transactions: {response.text}")
    
    def get_last10(self, account):
        if not account:
            account = KHAN_ACCOUNT

        params = {
            "account": f'{account}',
        }
        url = f"https://{HOST}/v1/omni/user/custom/recentTransactions?account={account}"
        headers = {
            "Authorization": f"Bearer {self.check_token()}",
            "Content-Type": "application/json"
        }
        response = self.session.get(url, headers=headers)
        if response.status_code in {200, 201, 202}:
            return response.json()
        raise Exception(f"Failed to fetch last 10 transactions: {response.text}")


if __name__ == "__main__":
    try:
        api = KhanBankAPI()
        last10_txn = api.get_last10(KHAN_ACCOUNT)
        print("Last 10:", last10_txn)
        actual_balance = last10_txn[0].get('balance')
        print(f"\nJSON:{json.dumps(last10_txn, indent=4, ensure_ascii=False)}")
        print(f"\nULDEGDEL: {str(actual_balance)}\n")
    except Exception as e:
        print("Error:", e)
