"""
eBay Finding API service for sports card market price lookup.
Uses the findCompletedItems operation to search sold listings.
No OAuth required — only EBAY_APP_ID is needed.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

FINDING_API_URL = 'https://svcs.ebay.com/services/search/FindingService/v1'


def get_ebay_market_price(player_name, sport=None, year=None):
    """
    Search eBay completed/sold listings for a card and return the average sale price.

    Args:
        player_name: Player name to search for (required)
        sport: Sport name to narrow results (optional)
        year: Card year to narrow results (optional)

    Returns:
        (average_price, error_message) tuple.
        average_price is a float on success, None on failure.
        error_message is None on success, a string on failure.
    """
    app_id = os.getenv('EBAY_APP_ID')
    if not app_id:
        return None, 'EBAY_APP_ID not configured'

    # Build keyword string: "Patrick Mahomes 2020 Football card"
    parts = [player_name]
    if year:
        parts.append(str(year))
    if sport:
        parts.append(sport)
    parts.append('card')
    keywords = ' '.join(parts)

    params = {
        'OPERATION-NAME': 'findCompletedItems',
        'SERVICE-VERSION': '1.0.0',
        'SECURITY-APPNAME': app_id,
        'RESPONSE-DATA-FORMAT': 'JSON',
        'REST-PAYLOAD': '',
        'keywords': keywords,
        'itemFilter(0).name': 'SoldItemsOnly',
        'itemFilter(0).value': 'true',
        'sortOrder': 'EndTimeSoonest',
        'paginationInput.entriesPerPage': '10',
    }

    try:
        resp = requests.get(FINDING_API_URL, params=params, timeout=10)
    except requests.exceptions.Timeout:
        return None, 'Could not refresh price at this time, please try again later'
    except requests.exceptions.RequestException:
        return None, 'Could not refresh price at this time, please try again later'

    # Check HTTP status before attempting to parse — eBay may return HTML on 5xx
    if resp.status_code >= 500:
        return None, 'Could not refresh price at this time, please try again later'
    if resp.status_code >= 400:
        return None, 'Could not refresh price at this time, please try again later'

    try:
        data = resp.json()
    except Exception:
        return None, 'Could not refresh price at this time, please try again later'

    try:
        wrapper = data.get('findCompletedItemsResponse', [{}])[0]
        ack = wrapper.get('ack', ['Failure'])[0]

        if ack not in ('Success', 'Warning'):
            return None, 'Could not refresh price at this time, please try again later'

        items = wrapper.get('searchResult', [{}])[0].get('item', [])
        if not items:
            return None, 'No sold listings found on eBay'

        prices = []
        for item in items:
            try:
                price_str = item['sellingStatus'][0]['currentPrice'][0]['__value__']
                price = float(price_str)
                if price > 0:
                    prices.append(price)
            except (KeyError, IndexError, ValueError, TypeError):
                continue

        if not prices:
            return None, 'No sold listings found on eBay'

        average = round(sum(prices) / len(prices), 2)
        return average, None

    except Exception:
        return None, 'Could not refresh price at this time, please try again later'
