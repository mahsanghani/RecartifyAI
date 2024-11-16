import os
import requests
import json
from datetime import datetime, timedelta
import time
from typing import List, Dict
import shopify
import retell  # You'll need to install the Retell SDK


class ShopifyRetellIntegration:
    def __init__(self,
                 shopify_api_key: str,
                 shopify_password: str,
                 shop_url: str,
                 retell_api_key: str,
                 voice_id: str):
        """Initialize the integration with your API credentials."""
        self.shop_url = shop_url
        self.retell_api_key = retell_api_key
        self.voice_id = voice_id

        # Initialize Shopify session
        shopify.Session.setup(api_key=shopify_api_key, secret=shopify_password)
        shop_url = f"https://{shop_url}.myshopify.com"
        self.session = shopify.Session(shop_url, '2024-01', shopify_api_key)
        shopify.ShopifyResource.activate_session(self.session)

        # Initialize Retell client
        self.retell_client = retell.Client(api_key=retell_api_key)

    def get_abandoned_checkouts(self, hours_ago: int = 24) -> List[Dict]:
        """Fetch abandoned checkouts from Shopify within the specified timeframe."""
        since_date = datetime.now() - timedelta(hours=hours_ago)

        abandoned_checkouts = shopify.Checkout.find(
            created_at_min=since_date.isoformat(),
            status='open'
        )

        return [checkout.to_dict() for checkout in abandoned_checkouts
                if checkout.phone and not checkout.completed_at]

    def prepare_call_script(self, checkout: Dict) -> str:
        """Prepare the AI call script based on checkout data."""
        items = ", ".join([item['title'] for item in checkout['line_items']])
        total_price = sum(float(item['price']) * item['quantity']
                          for item in checkout['line_items'])

        script = f"""Hello, this is {self.shop_url}'s virtual assistant. 
        I noticed you left some items in your cart - {items}. 
        The total value is ${total_price:.2f}. 
        Would you like to complete your purchase? 
        I can help you with any questions or concerns you might have."""

        return script

    def make_call(self, phone_number: str, script: str) -> Dict:
        """Initiate a call using Retell's API."""
        try:
            call = self.retell_client.calls.create(
                phone_number=phone_number,
                voice_id=self.voice_id,
                text=script,
                webhook_url="https://your-webhook-url.com/handle-call-status"
            )
            return call
        except Exception as e:
            print(f"Error making call to {phone_number}: {str(e)}")
            return None

    def process_abandoned_carts(self):
        """Main function to process all abandoned carts and make calls."""
        checkouts = self.get_abandoned_checkouts()

        for checkout in checkouts:
            phone = checkout.get('phone')
            if not phone:
                continue

            script = self.prepare_call_script(checkout)
            call_result = self.make_call(phone, script)

            if call_result:
                print(f"Successfully initiated call for order {checkout['id']}")

            # Rate limiting - wait 2 seconds between calls
            time.sleep(2)

    def start(self):
        """Start the integration and process carts."""
        print("Starting Shopify-Retell Integration...")
        while True:
            try:
                self.process_abandoned_carts()
                # Wait 30 minutes before checking for new abandoned carts
                time.sleep(1800)
            except Exception as e:
                print(f"Error in main loop: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    integration = ShopifyRetellIntegration(
        shopify_api_key=os.getenv('SHOPIFY_API_KEY'),
        shopify_password=os.getenv('SHOPIFY_PASSWORD'),
        shop_url=os.getenv('SHOP_URL'),
        retell_api_key=os.getenv('RETELL_API_KEY'),
        voice_id=os.getenv('RETELL_VOICE_ID')
    )

    integration.start()
