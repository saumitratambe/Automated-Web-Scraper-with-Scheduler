import logging
import time

from .base import BaseScraper, ScrapedItem

logger = logging.getLogger(__name__)


class SeleniumScraper(BaseScraper):
    def __init__(
        self,
        name: str,
        url: str,
        selectors: dict,
        headless: bool = True,
        timeout: int = 15,
        wait_seconds: float = 2.0,
    ):
        super().__init__(name, url)
        self.selectors = selectors
        self.headless = headless
        self.timeout = timeout
        self.wait_seconds = wait_seconds

    # ------------------------------------------------------------------
    def _get_driver(self):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        opts = Options()
        if self.headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service

            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), options=opts
            )
        except ImportError:
            # Fall back to PATH-installed chromedriver
            driver = webdriver.Chrome(options=opts)

        driver.set_page_load_timeout(self.timeout)
        return driver

    # ------------------------------------------------------------------
    def scrape(self) -> list[ScrapedItem]:
        driver = None
        try:
            driver = self._get_driver()
            driver.get(self.url)
            time.sleep(self.wait_seconds)  # let JS render
            return self._parse(driver)
        except Exception as exc:
            self.logger.error(f"Selenium scrape failed [{self.url}]: {exc}")
            return []
        finally:
            if driver:
                driver.quit()

    def _parse(self, driver) -> list[ScrapedItem]:
        from selenium.webdriver.common.by import By

        container_sel = self.selectors.get("items")
        if not container_sel:
            raw = driver.find_element(By.TAG_NAME, "body").text
            return [self._make_item({"raw_text": raw[:1000]})]

        items: list[ScrapedItem] = []
        for el in driver.find_elements(By.CSS_SELECTOR, container_sel):
            data = {}
            for key, sel in self.selectors.items():
                if key == "items" or sel is None:
                    continue
                found = el.find_elements(By.CSS_SELECTOR, sel)
                if len(found) == 1:
                    data[key] = found[0].text.strip()
                elif found:
                    data[key] = [f.text.strip() for f in found]
                else:
                    data[key] = None
            if any(v for v in data.values()):
                items.append(self._make_item(data))
        return items
