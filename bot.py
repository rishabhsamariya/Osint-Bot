```python
import requests
import json
import time

# ==============================
# Configuration
# ==============================

BOT_TOKEN = "8902390626:AAGEUDv7gUK9_czPE5mPjfMmSEC6aCHL0aI"
EXTERNAL_API_URL = "35952065"

TELEGRAM_API_URL = (
    "https://api.telegram.org/bot"
    + BOT_TOKEN
    + "/"
)

# Dummy HTTPS endpoint example:
# EXTERNAL_API_URL = "https://api.example.com/lookup"


# ==============================
# Telegram API helper
# ==============================

def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    url = TELEGRAM_API_URL + "sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    if parse_mode is not None:
        payload["parse_mode"] = parse_mode

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        return response.json()

    except (requests.RequestException, ValueError):
        print("Failed to send Telegram message.")
        return None


# ==============================
# Reply keyboard
# ==============================

def get_keyboard():
    return {
        "keyboard": [
            [
                {
                    "text": "📱 Phone Lookup"
                }
            ]
        ],
        "resize_keyboard": True,
        "is_persistent": True
    }


# ==============================
# External API lookup
# ==============================

def phone_lookup(mobile_number):
    if not EXTERNAL_API_URL:
        return {
            "error": "External API URL is not configured."
        }

    try:
        # This assumes the authorized API accepts a GET request
        # with a query parameter named "phone".
        response = requests.get(
            EXTERNAL_API_URL,
            params={"phone": mobile_number},
            timeout=15
        )

        response.raise_for_status()

        # Convert the API response into JSON.
        return response.json()

    except requests.RequestException:
        return {
            "error": "The external API request failed."
        }

    except ValueError:
        return {
            "error": "The external API returned invalid JSON."
        }


# ==============================
# Update processing
# ==============================

def process_update(update):
    message = update.get("message")

    if not message:
        return

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    # /start command
    if text == "/start" or text.startswith("/start@"):
        welcome_message = (
            "👋 Welcome to Phone Lookup Bot!\n\n"
            "Press the button below to continue."
        )

        send_message(
            chat_id,
            welcome_message,
            reply_markup=get_keyboard()
        )
        return

    # Phone Lookup button
    if text == "📱 Phone Lookup":
        send_message(
            chat_id,
            "📞 Send 10 digit mobile number:",
            reply_markup=get_keyboard()
        )
        return

    # Validate mobile number
    if text.isdigit() and len(text) == 10:
        send_message(
            chat_id,
            "⏳ Processing your request..."
        )

        result = phone_lookup(text)

        # Pretty-print the API result as JSON.
        formatted_json = json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )

        # Telegram messages have a length limit.
        # Keep the formatted response within a safe limit.
        if len(formatted_json) > 3500:
            formatted_json = formatted_json[:3500] + "\n..."

        send_message(
            chat_id,
            "<pre>" + formatted_json.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;") + "</pre>",
            parse_mode="HTML",
            reply_markup=get_keyboard()
        )
        return

    # Invalid input
    send_message(
        chat_id,
        "❌ Invalid input!\n\n"
        "Please enter exactly 10 digits, using numbers only.",
        reply_markup=get_keyboard()
    )


# ==============================
# Long polling
# ==============================

def main():
    if not BOT_TOKEN:
        print("ERROR: Please set BOT_TOKEN before running the bot.")
        return

    offset = 0

    print("Telegram bot started. Waiting for messages...")

    while True:
        try:
            response = requests.get(
                TELEGRAM_API_URL + "getUpdates",
                params={
                    "offset": offset,
                    "timeout": 30,
                    "allowed_updates": json.dumps(["message"])
                },
                timeout=35
            )

            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                print("Telegram API returned an error.")
                time.sleep(3)
                continue

            for update in data.get("result", []):
                # Advance offset to acknowledge the update.
                offset = update["update_id"] + 1

                try:
                    process_update(update)
                except Exception as error:
                    print("Update processing error:", error)

        except requests.RequestException as error:
            print("Polling error:", error)
            time.sleep(3)

        except KeyboardInterrupt:
            print("\nBot stopped.")
            break


if __name__ == "__main__":
    main()
```
