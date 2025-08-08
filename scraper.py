from playwright.async_api import async_playwright, TimeoutError as PWTimeout

AA_URL = "https://www.aa.com/travelInformation/reservationLookupAccess.do"

async def scrape_passenger_info(pnr, first_name, last_name, month, day, year, debug: bool=False):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox","--disable-dev-shm-usage"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
            locale="en-US",
            extra_http_headers={"Accept-Language":"en-US,en;q=0.9"}
        )
        page = await context.new_page()

        await page.goto(AA_URL, wait_until="domcontentloaded")

        # Fill trip info
        await page.fill('input[name="recordLocator"]', pnr)
        await page.fill('input[name="firstName"]', first_name)
        await page.fill('input[name="lastName"]', last_name)
        await page.select_option('select[name="dobMonth"]', month.zfill(2))
        await page.select_option('select[name="dobDay"]', day.zfill(2))
        await page.select_option('select[name="dobYear"]', year)

        await page.click('input[type="submit"]')

        success_candidates = [
            "[data-test-id='trip-summary']",
            "section.trip-summary",
            "h1:has-text('Trip details')",
            "h2:has-text('Itinerary')",
        ]
        error_candidates = [
            "text=We can’t find your trip",
            "text=Please check your information",
            ".error, .errorMessage"
        ]

        try:
            await page.wait_for_function(
                """(s, e) => {
                    const q = sel => document.querySelector(sel);
                    return s.some(q) || e.some(q);
                }""",
                arg=[success_candidates, error_candidates],
                timeout=22000
            )
        except PWTimeout:
            html = await page.content()
            url = page.url
            await browser.close()
            raise RuntimeError(f"Timeout after submit. url={url} html_len={len(html)}")

        # Look for error
        for sel in error_candidates:
            if await page.query_selector(sel):
                msg = (await (await page.query_selector(sel)).inner_text()).strip()
                await browser.close()
                raise RuntimeError(msg or "Reservation not found or inputs invalid")

        # Find segment rows
        row_selectors = [
            "[data-test-id='segment']",
            ".segment-row",
            "li.flight-segment",
            "div[data-component='Segment']",
        ]
        rows = []
        for rs in row_selectors:
            rows = await page.query_selector_all(rs)
            if rows:
                break

        segments = []
        warnings = []
        if not rows:
            warnings.append("Could not find segment rows with current selectors")

        async def safe_text(el):
            try:
                return (await el.inner_text()).strip()
            except:
                return None

        for r in rows:
            flight = await safe_text(await r.query_selector("[data-test-id='flight-number'], .flight-number, .flightNumber, .flight"))
            origin = await safe_text(await r.query_selector("[data-test-id='origin'], .origin, .from .airport-code, .originCode"))
            dest   = await safe_text(await r.query_selector("[data-test-id='destination'], .destination, .to .airport-code, .destinationCode"))
            dep    = await safe_text(await r.query_selector("[data-test-id='departure-time'], .departure-time, .departureTime"))
            arr    = await safe_text(await r.query_selector("[data-test-id='arrival-time'], .arrival-time, .arrivalTime"))
            status = await safe_text(await r.query_selector("[data-test-id='status-badge'], .status, .status-badge, .flightStatus"))
            date_local = await safe_text(await r.query_selector("[data-test-id='segment-date'], .segment-date, .flightDate, time[datetime]"))

            segments.append({
                "flightNumber": flight,
                "dateLocal": date_local,
                "from": origin,
                "to": dest,
                "schedDep": dep,
                "schedArr": arr,
                "status": status
            })

        result = {
            "passengerName": f"{first_name} {last_name}",
            "segments": segments
        }
        if warnings:
            result["warnings"] = warnings
        if debug:
            html = await page.content()
            result["debug"] = {
                "url": page.url,
                "htmlLength": len(html),
                "htmlPreview": html[:1200]
            }

        await browser.close()
        return result
