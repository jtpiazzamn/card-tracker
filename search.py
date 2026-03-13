import os
import re
import requests

def search_card_price(player_name, year, manufacturer, sport, condition):
    api_key = os.getenv('SERPAPI_KEY')
    if not api_key:
        return None, "No API key found"
    query = f"{year} {manufacturer} {player_name} {sport} card price"
    try:
        from serpapi import GoogleSearch
        # First try eBay sold listings
        params = {
            "engine": "ebay",
            "ebay_domain": "ebay.com",
            "_nkw": f"{year} {manufacturer} {player_name} {sport} card",
            "LH_Sold": "1",
            "LH_Complete": "1",
            "api_key": api_key
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        if "organic_results" in results:
            prices = []
            for item in results["organic_results"][:10]:
                price = item.get("price", {})
                if isinstance(price, dict):
                    raw = price.get("raw", "")
                elif isinstance(price, str):
                    raw = price
                else:
                    raw = ""
                raw = raw.replace("$", "").replace(",", "").strip()
                try:
                    val = float(raw)
                    if val > 0:
                        prices.append(val)
                except:
                    pass
            if prices:
                avg = sum(prices) / len(prices)
                return round(avg, 2), None
        # Fall back to Google Shopping
        params2 = {
            "engine": "google_shopping",
            "q": query,
            "api_key": api_key
        }
        search2 = GoogleSearch(params2)
        results2 = search2.get_dict()
        if "shopping_results" in results2:
            prices = []
            for item in results2["shopping_results"][:8]:
                raw = str(item.get("price", ""))
                raw = raw.replace("$", "").replace(",", "").strip()
                try:
                    val = float(raw)
                    if val > 0:
                        prices.append(val)
                except:
                    pass
            if prices:
                avg = sum(prices) / len(prices)
                return round(avg, 2), None
        # Fall back to regular Google search
        params3 = {
            "engine": "google",
            "q": f"{year} {manufacturer} {player_name} card sold price ebay",
            "api_key": api_key,
            "num": 10
        }
        search3 = GoogleSearch(params3)
        results3 = search3.get_dict()
        if "organic_results" in results3:
            for result in results3["organic_results"][:8]:
                snippet = result.get("snippet", "")
                prices = re.findall(r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', snippet)
                for p in prices:
                    try:
                        val = float(p.replace(",", ""))
                        if val > 0:
                            return round(val, 2), None
                    except:
                        pass
        return None, "No price found in any source"
    except Exception as e:
        return None, str(e)


def search_ebay_sold(player_name, year=None, manufacturer=None, sport=None, condition=None):
    """
    Search eBay sold listings using the eBay Browse API.
    Returns a dict with: average, low, high, count, listings (list of recent sales)
    """
    app_id = os.getenv('EBAY_APP_ID')
    if not app_id:
        return None, "No eBay App ID found"

    # allow sandbox credentials by switching endpoint automatically
    # if the App ID contains "SBX" assume sandbox credentials
    use_sandbox = 'SBX' in app_id.upper()
    
    # helper to choose base url
    if use_sandbox:
        token_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        search_base = "https://api.sandbox.ebay.com"
    else:
        token_url = "https://api.ebay.com/identity/v1/oauth2/token"
        search_base = "https://api.ebay.com"

    # Build search query
    parts = [p for p in [year, manufacturer, player_name, sport, 'card'] if p]
    query = ' '.join(parts)

    try:
        # Get OAuth token using Client Credentials flow
        token_resp = requests.post(
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope"
            },
            auth=(app_id, os.getenv('EBAY_CERT_ID', ''))
        )

        if token_resp.status_code != 200:
            return None, f"eBay auth failed: {token_resp.text}"

        access_token = token_resp.json().get('access_token')

        # Search completed/sold listings
        search_url = f"{search_base}/buy/browse/v1/item_summary/search"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            "Content-Type": "application/json"
        }
        params = {
            "q": query,
            "filter": "buyingOptions:{AUCTION|FIXED_PRICE},conditions:{USED|LIKE_NEW|VERY_GOOD|GOOD|ACCEPTABLE}",
            "sort": "endingSoonest",
            "limit": 10
        }

        resp = requests.get(search_url, headers=headers, params=params)

        if resp.status_code != 200:
            return None, f"eBay search failed: {resp.status_code}"

        data = resp.json()
        items = data.get('itemSummaries', [])

        if not items:
            return None, "No eBay listings found"

        listings = []
        prices = []

        for item in items[:10]:
            price_info = item.get('price', {})
            price_val = float(price_info.get('value', 0))
            if price_val > 0:
                prices.append(price_val)
                listings.append({
                    'title': item.get('title', '')[:60],
                    'price': price_val,
                    'url': item.get('itemWebUrl', ''),
                    'condition': item.get('condition', ''),
                })

        if not prices:
            return None, "No valid prices found"

        return {
            'average': round(sum(prices) / len(prices), 2),
            'low': round(min(prices), 2),
            'high': round(max(prices), 2),
            'count': len(prices),
            'listings': listings
        }, None

    except Exception as e:
        return None, str(e)