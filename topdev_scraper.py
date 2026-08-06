"""TopDev/Saramin job-list reader with per-job availability verification."""

import os
import re
import time
import unicodedata
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen
import json

from playwright.sync_api import sync_playwright
from rich.console import Console


console = Console()


class TopDevScraper:
    """Read TopDev search pages and verify every result on its detail page.

    TopDev has migrated parts of its site to Saramin. Search snippets and old
    ``/viec-lam/`` routes can therefore still exist after a job has expired.
    This reader treats a job as active only when the current detail page is not
    marked expired and still exposes an apply action.
    """

    JOB_PATH_MARKERS = ("/detail-jobs/", "/viec-lam/")
    EXCLUDED_LINK_TEXT = {
        "apply now", "ung tuyen ngay", "easy apply", "save this job",
        "luu cong viec", "view more jobs", "xem them viec lam",
    }
    INTERNSHIP_MARKERS = ("intern", "internship", "trainee", "co-op", "thuc tap")
    SENIOR_MARKERS = ("senior", "lead", "manager", "head", "director", "architect")

    def __init__(self, user_data_dir="./user_data"):
        self.user_data_dir = os.path.abspath(user_data_dir)
        self.playwright = None
        self.context = None
        self.page = None
        os.makedirs(self.user_data_dir, exist_ok=True)

    def start_browser(self):
        console.print("[yellow]Starting Chromium for TopDev/Saramin...[/yellow]")
        self.playwright = sync_playwright().start()
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
            no_viewport=True,
        )
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        self.page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )

    def close_browser(self):
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()

    def wait_for_user(self, message):
        console.print(f"[bold yellow]{message}[/bold yellow]")
        input("Press Enter to continue...")

    @staticmethod
    def _clean_text(value):
        return re.sub(r"\s+", " ", value or "").strip()

    @classmethod
    def _ascii_fold(cls, value):
        """Make Vietnamese and English status text comparable without accents."""
        value = cls._clean_text(value).replace("đ", "d").replace("Đ", "D")
        return "".join(
            char for char in unicodedata.normalize("NFD", value.lower())
            if unicodedata.category(char) != "Mn"
        )

    @staticmethod
    def _canonical_job_url(url):
        parsed = urlparse(url)
        # Tracking parameters are not needed to read or re-open a job later.
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

    def open_listing(self, listing_url):
        console.print(f"[blue]Opening TopDev listing: {listing_url}[/blue]")
        last_error = None
        for attempt in range(1, 4):
            try:
                self.page.goto(listing_url, wait_until="domcontentloaded", timeout=60000)
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                if attempt < 3:
                    time.sleep(attempt * 2)
        if last_error:
            raise last_error
        time.sleep(4)

    def extract_jobs_from_current_page(self, limit=80):
        """Return job links from the currently rendered results page."""
        jobs = []
        seen_urls = set()
        for link in self.page.locator("a").element_handles():
            try:
                if not link.is_visible():
                    continue
                href = link.get_attribute("href")
                if not href or not any(marker in href for marker in self.JOB_PATH_MARKERS):
                    continue

                full_url = self._canonical_job_url(urljoin(self.page.url, href))
                if "topdev.vn" not in urlparse(full_url).netloc or full_url in seen_urls:
                    continue

                title = self._clean_text(
                    link.inner_text() or link.get_attribute("title") or link.get_attribute("aria-label")
                )
                if len(title) < 5 or title.lower() in self.EXCLUDED_LINK_TEXT:
                    continue

                seen_urls.add(full_url)
                jobs.append({"title": title, "link": full_url})
                if len(jobs) >= limit:
                    break
            except Exception:
                continue

        console.print(f"[green]Collected {len(jobs)} distinct TopDev job links from the visible page.[/green]")
        return jobs

    def extract_jobs_from_list(self, listing_url, limit=80):
        """Backward-compatible one-page reader."""
        self.open_listing(listing_url)
        return self.extract_jobs_from_current_page(limit=limit)

    def _click_next_page(self):
        """Click the actual paginator control instead of guessing a URL scheme."""
        current_links = {job["link"] for job in self.extract_jobs_from_current_page(limit=200)}
        for control in self.page.locator("a, button").element_handles():
            try:
                marker = self._ascii_fold(" ".join(filter(None, [
                    control.inner_text(),
                    control.get_attribute("aria-label"),
                    control.get_attribute("title"),
                    control.get_attribute("class"),
                ])))
                disabled = (
                    control.get_attribute("disabled") is not None
                    or control.get_attribute("aria-disabled") == "true"
                )
                is_next = marker.strip() in {"next", "trang sau", ">"} or "pagination-next" in marker
                if not is_next or disabled:
                    continue
                control.click()
                time.sleep(2)
                self.page.wait_for_load_state("domcontentloaded", timeout=10000)
                time.sleep(2)
                new_links = {job["link"] for job in self.extract_jobs_from_current_page(limit=200)}
                if new_links and new_links != current_links:
                    return True
            except Exception:
                continue
        return False

    def extract_jobs_from_pages(self, listing_url, pages=6, per_page_limit=80):
        """Collect unique job links across pages, preferring TopDev's data API."""
        api_jobs = self.extract_jobs_from_api(listing_url, pages=pages)
        if api_jobs is not None:
            return api_jobs

        # Fallback only: some deployments can block the public API temporarily.
        self.open_listing(listing_url)
        all_jobs = []
        seen_urls = set()
        for page_number in range(1, pages + 1):
            console.print(f"[blue]Reading TopDev page {page_number}/{pages}...[/blue]")
            page_jobs = self.extract_jobs_from_current_page(limit=per_page_limit)
            added = 0
            for job in page_jobs:
                if job["link"] not in seen_urls:
                    seen_urls.add(job["link"])
                    all_jobs.append(job)
                    added += 1
            console.print(f"[green]Added {added} unique jobs; total {len(all_jobs)}.[/green]")
            if page_number == pages or not self._click_next_page():
                break
        return all_jobs

    def extract_jobs_from_api(self, listing_url, pages=6):
        """Read the same paginated jobs data the current TopDev UI consumes.

        The old search route can render stale/promoted cards while its visible
        paginator is disconnected. The public v2 endpoint returns canonical
        job IDs, the total count, and page metadata, so it is used for the
        collection phase; each returned link is still re-opened later for the
        final active/expired verification.
        """
        query = parse_qs(urlparse(listing_url).query)
        categories = query.get("job_categories_ids", [""])[0]
        regions = query.get("region_ids", [""])[0]
        keyword = query.get("keyword", [""])[0]
        params = {
            "locale": "en_US",
            "job_categories_ids": categories,
            "region_ids": regions,
            "keyword": keyword,
            "fields[job]": "id,title,slug,company,job_level,job_levels,expired_at",
        }

        jobs = []
        seen_ids = set()
        self.api_total = None
        self.api_last_page = None
        try:
            for page_number in range(1, pages + 1):
                params["page"] = page_number
                endpoint = "https://api.topdev.vn/td/v2/jobs?" + urlencode(params)
                request = Request(endpoint, headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"})
                with urlopen(request, timeout=30) as response:
                    payload = json.loads(response.read().decode("utf-8"))

                meta = payload.get("meta") or {}
                self.api_total = meta.get("total", self.api_total)
                self.api_last_page = meta.get("last_page", self.api_last_page)
                page_data = payload.get("data") or []
                console.print(
                    f"[blue]Reading TopDev API page {page_number}/{pages}: {len(page_data)} jobs.[/blue]"
                )
                for item in page_data:
                    job_id = item.get("id")
                    slug = item.get("slug")
                    title = self._clean_text(item.get("title"))
                    if not job_id or not slug or job_id in seen_ids or not title:
                        continue
                    seen_ids.add(job_id)
                    company = (item.get("company") or {}).get("display_name", "")
                    jobs.append(
                        {
                            "title": title,
                            "company": company,
                            "link": f"https://topdev.vn/viec-lam/{slug}-{job_id}",
                            "source_page": page_number,
                        }
                    )
                if not page_data or page_number >= (self.api_last_page or page_number):
                    break
            console.print(
                f"[green]Collected {len(jobs)} unique jobs from {min(pages, self.api_last_page or pages)} API pages "
                f"(platform total: {self.api_total if self.api_total is not None else '?'}).[/green]"
            )
            return jobs
        except Exception as exc:
            console.print(f"[yellow]TopDev API collection failed ({type(exc).__name__}); using browser paginator fallback.[/yellow]")
            return None

    @staticmethod
    def _experience_years(text):
        lowered = TopDevScraper._ascii_fold(text)
        ranges = re.findall(r"(\d+)\s*(?:-|–|to)\s*(\d+)\s*(?:years?|nam)\b", lowered)
        if ranges:
            return max(int(end) for _, end in ranges)

        values = re.findall(
            r"(?:from|tu|over|tren|at least|minimum|toi thieu)\s*(\d+)\s*(?:years?|nam)\b",
            lowered,
        )
        return max(map(int, values)) if values else None

    @classmethod
    def _candidate_rule_status(cls, title, detail_text, is_active):
        title_lower = cls._ascii_fold(title)
        experience = cls._experience_years(detail_text)
        is_internship = any(marker in title_lower for marker in cls.INTERNSHIP_MARKERS)
        is_senior = any(marker in title_lower for marker in cls.SENIOR_MARKERS)

        if not is_active:
            return experience, "exclude", "Job is not currently active"
        if is_internship:
            return experience, "exclude", "Intern/Trainee role"
        if is_senior:
            return experience, "exclude", "Senior or management role"
        if experience is not None and experience > 2:
            return experience, "exclude", f"Requires {experience}+ years"
        if experience is None:
            return experience, "review", "Experience requirement was not parsed"
        return experience, "eligible", "Active and within the <=2-year rule"

    def verify_job(self, job):
        """Open a job page and record current availability from the page itself."""
        result = dict(job)
        result.update(
            {
                "platform": "TopDev/Saramin",
                "status": "unknown",
                "is_active": False,
                "days_left": None,
                "experience_years": None,
                "candidate_rule": "review",
                "rule_reason": "Could not verify the job page",
                "verified_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        try:
            self.page.goto(job["link"], wait_until="domcontentloaded", timeout=60000)
            time.sleep(1.5)
            page_title = self._ascii_fold(self.page.title())
            detail_text = self._clean_text(self.page.locator("body").inner_text())
            detail_lower = self._ascii_fold(detail_text)

            expired = bool(re.search(r"\b(expired|het han)\b", page_title))
            if expired:
                status = "expired"
            else:
                has_apply_action = bool(
                    re.search(r"\b(apply now|easy apply|ung tuyen ngay)\b", detail_lower)
                )
                days_match = re.search(r"(\d+)\s+days?\s+left", detail_lower)
                vietnamese_days = re.search(r"(\d+)\s+ngay\s+con", detail_lower)
                if has_apply_action:
                    status = "active"
                elif days_match or vietnamese_days:
                    status = "needs_manual_check"
                else:
                    status = "unknown"

            days_match = re.search(r"(\d+)\s+days?\s+left", detail_lower)
            vietnamese_days = re.search(r"(\d+)\s+ngay\s+con", detail_lower)
            days_left = int((days_match or vietnamese_days).group(1)) if (days_match or vietnamese_days) else None
            is_active = status == "active"
            experience, candidate_rule, rule_reason = self._candidate_rule_status(
                result["title"], detail_text, is_active
            )
            result.update(
                {
                    "link": self._canonical_job_url(self.page.url),
                    "status": status,
                    "is_active": is_active,
                    "days_left": days_left,
                    "experience_years": experience,
                    "candidate_rule": candidate_rule,
                    "rule_reason": rule_reason,
                }
            )
        except Exception as exc:
            result["rule_reason"] = f"Verification failed: {type(exc).__name__}"

        return result

    def verify_jobs(self, jobs):
        verified = []
        for index, job in enumerate(jobs, start=1):
            console.print(f"[blue]Verifying {index}/{len(jobs)}: {job['title'][:70]}[/blue]")
            verified.append(self.verify_job(job))
        return verified
