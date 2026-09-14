import requests
import json
import time


# ============================================================
# CONFIGURATION
# ============================================================

BOT_TOKEN = "8693885966:AAEyBKi9_Q9dp1uYWPFO06X86xp3b046q9M"
EXTERNAL_API_URL = "num_live_0LmtWHMMNXgiuBl6OcDBOu4jaJXhUhYvIeXxflEd"


# Telegram Bot API base URL
TELEGRAM_API_URL = "https://api.telegram.org/bot" + BOT_TOKEN


# ============================================================
# TELEGRAM API FUNCTIONS
# ============================================================

def send_message(chat_id, text, reply_markup=None):
    """Send a message to a Telegram chat."""

    url = TELEGRAM_API_URL + "/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_markup is not None:
        data["reply_markup"] = json.dumps(reply_markup)

    try:
        response = requests.post(url, data=data, timeout=30)
        response.raise_for_status()

        result = response.json()

        if not result.get("ok"):
            print("Telegram API error:", result)

        return result

    except requests.RequestException as error:
        print("Error sending Telegram message:", error)
        return None


def get_updates(offset=None):
    """Get new updates from Telegram using long polling."""

    url = TELEGRAM_API_URL + "/getUpdates"

    params = {
        "timeout": 30
    }

    if offset is not None:
        params["offset"] = offset

    try:
        response = requests.get(
            url,
            params=params,
            timeout=35
        )

        response.raise_for_status()

        result = response.json()

        if result.get("ok"):
            return result.get("result", [])

        print("Telegram getUpdates error:", result)

    except requests.RequestException as error:
        print("Error getting Telegram updates:", error)

    return []


# ============================================================
# KEYBOARD
# ============================================================

def get_main_keyboard():
    """Return the custom reply keyboard."""

    keyboard = {
        "keyboard": [
            [
                {
                    "text": "📱 Phone Lookup"
                }
            ]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

    return keyboard


# ============================================================
# EXTERNAL API
# ============================================================

def lookup_phone(mobile_number):
    """
    Call the external API and convert its response to JSON.

    Change the parameter name below if your external API expects
    something other than ?phone=XXXXXXXXXX.
    """

    if not EXTERNAL_API_URL:
        return {
            "error": "External API URL is not configured."
        }

    try:
        response = requests.get(
            EXTERNAL_API_URL,
            params={
                "phone": mobile_number
            },
            timeout=30
        )

        response.raise_for_status()

        # Convert API response into JSON
        api_data = response.json()

        return api_data

    except requests.RequestException as error:
        return {
            "error": "External API request failed.",
            "details": str(error)
        }

    except ValueError:
        return {
            "error": "External API did not return valid JSON."
        }


# ============================================================
# HTML SAFETY FOR <pre>
# ============================================================

def escape_html(text):
    """
    Escape characters that could interfere with Telegram HTML.
    This avoids importing the html module.
    """

    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")

    return text


# ============================================================
# MESSAGE HANDLER
# ============================================================

def handle_message(message):
    """Process one Telegram message."""

    chat = message.get("chat", {})
    chat_id = chat.get("id")

    text = message.get("text", "")

    if chat_id is None:
        return

    # --------------------------------------------------------
    # /start command
    # --------------------------------------------------------

    if text == "/start":
        welcome_message = (
            "👋 Welcome!\n\n"
            "Use the button below to perform a phone lookup."
        )

        send_message(
            chat_id,
            welcome_message,
            get_main_keyboard()
        )

        return

    # --------------------------------------------------------
    # Phone Lookup button
    # --------------------------------------------------------

    if text == "📱 Phone Lookup":
        send_message(
            chat_id,
            "📞 Send 10 digit mobile number:"
        )

        return

    # --------------------------------------------------------
    # Validate mobile number
    # --------------------------------------------------------

    if text.isdigit() and len(text) == 10:
        mobile_number = text

        # Tell the user that the request is being processed.
        send_message(
            chat_id,
            "🔎 Looking up the number..."
        )

        # Call external API.
        api_result = lookup_phone(mobile_number)

        # Convert the result to formatted JSON.
        try:
            formatted_json = json.dumps(
                api_result,
                indent=2,
                ensure_ascii=False
            )

        except (TypeError, ValueError):
            formatted_json = json.dumps(
                {
                    "error": "Could not convert API response to JSON."
                },
                indent=2
            )

        # Escape HTML characters before putting JSON inside <pre>.
        safe_json = escape_html(formatted_json)

        response_message = "<pre>" + safe_json + "</pre>"

        send_message(
            chat_id,
            response_message,
            get_main_keyboard()
        )

        return

    # --------------------------------------------------------
    # Invalid input
    # --------------------------------------------------------

    if text:
        send_message(
            chat_id,
            "❌ Invalid input.\n\n"
            "Please send exactly 10 numeric digits.\n"
            "Example: 9876543210",
            get_main_keyboard()
        )


# ============================================================
# MAIN BOT LOOP
# ============================================================

def main():
    """Start the Telegram bot."""

    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN is empty.")
        print("Add your Telegram bot token to BOT_TOKEN.")
        return

    print("Bot started.")
    print("Waiting for messages...")

    offset = None

    while True:
        updates = get_updates(offset)

        for update in updates:
            # Advance offset so the same update is not processed again.
            update_id = update.get("update_id")

            if update_id is not None:
                offset = update_id + 1

            message = update.get("message")

            if message is not None:
                handle_message(message)

        # Small delay to prevent a tight loop if an error occurs.
        time.sleep(1)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
