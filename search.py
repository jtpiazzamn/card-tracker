import os
import re

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
