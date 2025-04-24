from flask import Flask, render_template, request, jsonify
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

QUICKNODE_URL = "https://proud-aged-flower.solana-mainnet.quiknode.pro/6c4369466a2cfc21c12af4a500501aa9b0093340/"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/close_accounts', methods=['POST'])
def close_accounts():
    try:
        wallet = request.form['wallet'].strip()
        if not (32 <= len(wallet) <= 44):
            return jsonify({"error": "Invalid address"}), 400

        headers = {"Content-Type": "application/json"}
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                wallet,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed", "commitment": "confirmed"}
            ]
        }

        response = requests.post(QUICKNODE_URL, json=data, headers=headers)
        response.raise_for_status()
        
        accounts = response.json()["result"]["value"]
        empty_accounts = []

        for acc in accounts:
            try:
                info = acc["account"]["data"]["parsed"]["info"]
                amount = info["tokenAmount"]["uiAmount"]
                if amount == 0:
                    empty_accounts.append(acc["pubkey"])
            except Exception as e:
                logging.warning(f"Error processing account: {e}")
                continue

        if not empty_accounts:
            return jsonify({"error": "No empty accounts found to close"}), 400

        return jsonify({
            "success": True,
            "message": f"Found {len(empty_accounts)} accounts to close",
            "accounts": empty_accounts,
            "estimated_sol": f"{len(empty_accounts) * 0.002:.3f} SOL"
        })
    except Exception as e:
        logging.error(f"Close accounts error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/check_wallet', methods=['POST'])
def check_wallet():
    try:
        wallet = request.form['wallet'].strip()
        if not (32 <= len(wallet) <= 44):
            return jsonify({"error": "Invalid address"}), 400

        headers = {"Content-Type": "application/json"}
        data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                wallet,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed"}
            ]
        }

        response = requests.post(QUICKNODE_URL, json=data, headers=headers)
        response.raise_for_status()

        result = response.json()
        accounts = result["result"]["value"]

        token_accounts = 0
        nft_accounts = 0
        cleanup_accounts = 0
        total_rent = 0

        for acc in accounts:
            try:
                info = acc["account"]["data"]["parsed"]["info"]
                amount = info["tokenAmount"]["uiAmount"]
                decimals = info["tokenAmount"]["decimals"]

                if amount == 0:
                    token_accounts += 1
                elif decimals == 0 and amount == 1:
                    nft_accounts += 1
                else:
                    cleanup_accounts += 1

                total_rent += 0.00203928
            except Exception as e:
                logging.warning(f"Error processing account: {e}")
                continue

        real_value = total_rent
        sol_value = round(real_value, 6)
        short_wallet = wallet[:4] + "..." + wallet[-4:]

        return jsonify({
            "wallet": short_wallet,
            "sol_value": sol_value,
            "token_accounts": token_accounts,
            "nft_accounts": nft_accounts,
            "cleanup_accounts": cleanup_accounts
        })
    except Exception as e:
        logging.error(f"Wallet handler error: {e}")
        return jsonify({"error": "Error connecting to the network"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
