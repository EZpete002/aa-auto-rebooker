# scraper.py
import asyncio
from typing import Any, Dict, List
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

AA_URL = "https://www.aa.com/reservation/viewReservationsAccess.do?anchorEvent=false&from=comp_nav"

# Helper to read text from a locator or return None
async def safe_text(el):
    try:
        return (await el.inner_text()).strip()
    except Exception:
        return None

async def scrape_passenger_info(pnr: str, first_name: str, last_name: str, month: str, day: str, year: str) -> Dict[str, Any]:
    """
    Returns:
      {
        "passengerName": "First Last",
        "segments": [
          {"flightNumber":"AA123","dateLocal":"2025-08-08","from":"DFW","to":"MIA","schedDep":"13:00","schedArr":"17:00","status":"MISSED"}
        ],
        "warnings": ["text..."]    # optional
      }
    Raises:
      RuntimeError with a clear message string on known failures
    """
    async with async_playwright() as p:
        # These args help in many container envs
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--no-sandbox"]
        )
        context = await browser.new_context()
        page = await context.new_page()

        # 1) Load page
        await page.goto(AA_URL, wait_until="domcontentloaded")

        # 2) Fill the form
        await page.fill('input[name="recordLocator"]', pnr)
        await page.fill('input[name="firstName"]', first_name)
        await page.fill('input[name="lastName"]', last_name)
        await page.select_option('select[name="dobMonth"]', month.zfill(2))
        await page.select_option('select[name="dobDay"]', day.zfill(2))
        await page.select_option('select[name="dobYear"]', year)

        # 3) Submit
        await page.click('input[type="submit"]')

        # 4) Wait for either a success signal or an error message
        # Adjust these selectors after a dry run with headless=False locally
        success_candidates = [
            # pick something that appears only on the itinerary page
            "[data-test-id='trip-summary']",
            ".tripSummary",
            "text=Itinerary",
            "text=Trip details",
        ]
        error_candidates = [
            "text=We can’t find your trip",
            "text=Please check your information",
            ".error, .errorMessage"
        ]

        try:
            # race: success or error
            await page.wait_for_function(
                """() => {
                    const successSel = [%s];
                    const errorSel = [%s];
                    const has = sel => document.querySelector(sel);
                    return successSel.some(has) || errorSel.some(has);
                }""" % (
                    ",".join([f"`{s}`" for s in success_candidates]),
                    ",".join([f"`{s}`" for s in error_candidates]),
                ),
                timeout=20000
            )
        except PWTimeout:
            await browser.close()
            raise RuntimeError("Timeout waiting for itinerary or error page")

        # Check for error text
        for sel in error_candidates:
            err = await page.query_selector(sel)
            if err:
                msg = await safe_text(err)
                await browser.close()
                raise RuntimeError(msg or "Reservation not found or inputs invalid")

        # 5) Extract segments
        segments: List[Dict[str, Any]] = []
        warnings: List[str] = []

        # Try a few patterns for segment rows. Update these once you inspect the real DOM.
        row_selectors = [
            "[data-test-id='segment']",
            ".segmentRow",
            ".flight-segment",
        ]
        rows = []
        for rs in row_selectors:
            rows = await page.query_selector_all(rs)
            if rows:
                break

        # Fallback: if we still could not find rows, capture a screenshot to debug selectors.
        if not rows:
            warnings.append("Could not find segment rows with current selectors")
            # Uncomment for debugging screenshots locally:
            # await page.screenshot(path="debug_no_rows.png", full_page=True)

        for r in rows:
            # Try multiple locator options for each field
            flight = await safe_text(await r.query_selector("[data-test-id='flight-number'], .flightNumber, .flight"))
            o = await safe_text(await r.query_selector("[data-test-id='origin'], .originCode, .from, .origin"))
            d = await safe_text(await r.query_selector("[data-test-id='destination'], .destinationCode, .to, .destination"))
            dep = await safe_text(await r.query_selector("[data-test-id='departure-time'], .departureTime, .dep"))
            arr = await safe_text(await r.query_selector("[data-test-id='arrival-time'], .arrivalTime, .arr"))
            status = await safe_text(await r.query_selector("[data-test-id='status-badge'], .status, .flightStatus"))
            date_local = await safe_text(await r.query_selector("[data-test-id='segment-date'], .date, .flightDate"))

            segments.append({
                "flightNumber": flight,
                "dateLocal": date_local,
                "from": o,
                "to": d,
                "schedDep": dep,
                "schedArr": arr,
                "status": status
            })

        result: Dict[str, Any] = {
            "passengerName": f"{first_name} {last_name}",
            "segments": segments,
        }
        if warnings:
            result["warnings"] = warnings

        await browser.close()
        return result

# Local debug sample:
# asyncio.run(scrape_passenger_info("IDIMHA", "Pedro", "Feitosa", "09", "16", "2002"))
