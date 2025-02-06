import asyncio
import aiohttp

# Hardcoded credentials and job details
ACCESS_TOKEN = 'hardcoded_access_token'
JOB_ID = 'hardcoded_jobid'
# You will need to adjust these for your Salesforce instance and API version.
INSTANCE_URL = 'https://yourInstance.salesforce.com'
API_VERSION = 'v52.0'
# Base URL for the Bulk API 2.0 query results
BASE_URL = f"{INSTANCE_URL}/services/data/{API_VERSION}/jobs/query/{JOB_ID}/results"


async def fetch_page(session: aiohttp.ClientSession, url: str, page_number: int) -> list:
    """
    Fetch one page of results. As soon as the headers are available,
    if the 'sforce-locator' header is present, schedule the next page to be downloaded.
    
    Returns:
        A list of tuples (page_number, csv_text) for this page and any subsequent pages.
    """
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }
    async with session.get(url, headers=headers) as response:
        # As soon as we have the response headers, check for the locator.
        locator = response.headers.get('sforce-locator')
        next_task = None

        if locator:
            # Build the URL for the next page. Note: the next request must use the same base URL plus the locator query.
            next_url = f"{BASE_URL}?locator={locator}"
            # Start downloading the next page concurrently.
            next_task = asyncio.create_task(fetch_page(session, next_url, page_number + 1))

        # Meanwhile, read the CSV data from the current response.
        csv_text = await response.text()

        # If a next page was scheduled, wait for it to finish and combine results.
        if next_task:
            subsequent_pages = await next_task
            # Prepend the current page to the list of pages from subsequent calls.
            return [(page_number, csv_text)] + subsequent_pages
        else:
            return [(page_number, csv_text)]


async def main():
    # Create an aiohttp session (you can adjust connector limits if needed).
    async with aiohttp.ClientSession() as session:
        # Start with the base URL and page 0.
        pages = await fetch_page(session, BASE_URL, 0)

        # Sort pages by page number to ensure they are in the original order.
        pages.sort(key=lambda tup: tup[0])

        # Write the combined CSV text to results.csv.
        with open("results.csv", "w", encoding="utf-8") as outfile:
            for _, csv_text in pages:
                outfile.write(csv_text)

    print("Download completed.")


if __name__ == '__main__':
    asyncio.run(main())
