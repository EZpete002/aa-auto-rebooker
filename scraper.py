
import asyncio
from playwright.async_api import async_playwright

async def scrape_passenger_info(pnr, first_name, last_name, month, day, year):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Go to the AA reservation lookup page
        await page.goto("https://www.aa.com/reservation/viewReservationsAccess.do?anchorEvent=false&from=comp_nav")

        # Fill in the form fields
        await page.fill('input[name="recordLocator"]', pnr)
        await page.fill('input[name="firstName"]', first_name)
        await page.fill('input[name="lastName"]', last_name)
        await page.select_option('select[name="dobMonth"]', month)
        await page.select_option('select[name="dobDay"]', day)
        await page.select_option('select[name="dobYear"]', year)

        # Submit the form
        await page.click('input[type="submit"]')

        # Wait for the results page to load (may need better targeting)
        await page.wait_for_timeout(5000)

        # Extract visible trip summary data
        content = await page.content()
        await browser.close()
        return content  # You can extract more specific fields from this with BeautifulSoup if needed

# Example usage (for local testing):
# asyncio.run(scrape_passenger_info("ABC123", "Pedro", "Feitosa", "09", "16", "2002"))
