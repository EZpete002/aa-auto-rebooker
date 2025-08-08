import asyncio
from typing import Any, Dict, List
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

AA_URL = "https://www.aa.com/reservation/viewReservationsAccess.do?anchorEvent=false&from=comp_nav"

async def safe_text(locator):
    try:
        if locator is None:
            return None
        txt = await locator.inner_text()
        return txt.strip() if txt else None
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
        "warnings": ["optional notes"]
      }
    Raises:
      RuntimeError on known failures
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context()
        page = await context.new_page()

        # 1) Load
        await page.goto(AA_URL, wait_until="domcontentloaded")

        # 2) Fill
        await page.fill('input[name="recordLocator"]', pnr)
        await page.fill('input[name="firstName"]', first_name)
        await page.fill('input[name="lastName"]', last_name)
        await page.select_option('select[name="dobMonth"]', month.zfill(2))
        await page.select_option('select[name="dobDay"]', day.zfill(2))
        await page.select_option('select[name="dobYear"]', year)

        # 3) Submit
        await page.click('input[type="submit"]')

        # 4) Wait for success or error
        success_candidates = [
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
            await page.wait_for_function(
                """() => {
                    const s = %s;
                    const e = %s;
                    const q = sel => document.querySelector(sel);
                    return s.some(q) || e.some(q);
                }""" % (
                    str(success_candidates),
                    str(error_candidates),
                ),
                timeout=20000
            )
        except PWTimeout:
            await browser.close()
            raise RuntimeError("Timeout waiting for itinerary or error page")

        # Error detection
        for sel in error_candidates:
            err = await page.query_selector(sel)
            if err:
                msg = await safe_text(err)
                await browser.close()
                raise RuntimeError(msg or "Reservation not found or inputs invalid")

        # 5) Extract segments
        segments: List[Dict[str, Any]] = []
        warnings: List[str] = []

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

        if not rows:
            warnings.append("Could not find segment rows with current selectors")

        for r in rows:
            flight = await safe_text(await r.query_selector("[data-test-id='flight-number'], .flightNumber, .flight"))
            origin = await safe_text(await r.query_selector("[data-test-id='origin'], .originCode, .from, .origin"))
            dest = await safe_text(await r.query_selector("[data-test-id='destination'], .destinationCode, .to, .destination"))
            dep = await safe_text(await r.query_selector("[data-test-id='departure-time'], .departureTime, .dep"))
            arr = await safe_text(await r.query_selector("[data-test-id='arrival-time'], .arrivalTime, .arr"))
            status = await safe_text(await r.query_selector("[data-test-id='status-badge'], .status, .flightStatus"))
            date_local = await safe_text(await r.query_selector("[data-test-id='segment-date'], .date, .flightDate"))

            segments.append({
                "flightNumber": flight,
                "dateLocal": date_local,
                "from": origin,
                "to": dest,
                "schedDep": dep,
                "schedArr": arr,
                "status": status
            })

        result: Dict[str, Any] = {
            "passengerName": f"{first_name} {last_name}",
            "segments": segments
        }
        if warnings:
            result["warnings"] = warnings

        await browser.close()
        return result

# Local debug example:
# asyncio.run(scrape_passenger_info("IDIMHA", "Pedro", "Feitosa", "09", "16", "2002"))
