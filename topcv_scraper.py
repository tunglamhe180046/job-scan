import os
import json
import time
import re
from urllib.parse import urlparse, urljoin
import pandas as pd
from playwright.sync_api import sync_playwright
from rich.console import Console

console = Console()

class TopCVScraper:
    def __init__(self, user_data_dir="./user_data"):
        self.user_data_dir = os.path.abspath(user_data_dir)
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)

    def start_browser(self):
        """Khởi động trình duyệt Playwright với User Data Dir để lưu session"""
        console.print("[yellow]Đang khởi động trình duyệt Chromium...[/yellow]")
        self.playwright = sync_playwright().start()
        
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=False,  # Bắt buộc False để vượt Cloudflare/CAPTCHA nếu cần
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ],
            no_viewport=True
        )
        
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()
            
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        console.print("[green]Trình duyệt đã khởi động thành công![/green]")

    def close_browser(self):
        """Đóng trình duyệt"""
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()
        console.print("[yellow]Trình duyệt đã được đóng.[/yellow]")

    def wait_for_user(self, message="Vui lòng vượt qua Cloudflare/CAPTCHA (nếu có) trên trình duyệt, sau đó nhấn Enter tại đây để tiếp tục..."):
        """Tạm dừng chương trình để người dùng tương tác bằng tay"""
        console.print(f"\n[bold red]⚠️  {message}[/bold red]")
        input("Nhấn Enter để tiếp tục...")

    def extract_companies_from_list(self, url):
        """Cào danh sách công ty từ trang danh sách việc làm TopCV"""
        console.print(f"[blue]Đang truy cập trang danh sách: {url}[/blue]")
        
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            console.print(f"[red]Lỗi khi tải trang: {e}[/red]")
            self.wait_for_user("Lỗi tải trang. Hãy kiểm tra trình duyệt, tải lại trang và nhấn Enter tại đây...")
        
        time.sleep(4) # Chờ load động
        
        # Kiểm tra xem có Cloudflare hay không
        if "Cloudflare" in self.page.title() or self.page.locator("text=Verify you are human").is_visible():
            self.wait_for_user("Phát hiện màn hình bảo mật Cloudflare. Vui lòng giải CAPTCHA trên trình duyệt và nhấn Enter tại đây...")
            time.sleep(2)

        # Lấy tất cả các thẻ liên kết (thẻ a) trên trang
        links = self.page.locator("a").element_handles()
        
        companies = {}
        for link in links:
            try:
                href = link.get_attribute("href")
                if href:
                    # Link công ty trên TopCV có thể ở dạng:
                    # - /cong-ty/tên-công-ty/12345.html
                    # - /brand/tên-công-ty
                    if "/cong-ty/" in href or "/brand/" in href:
                        full_url = urljoin("https://www.topcv.vn", href)
                        
                        # Làm sạch url
                        parsed_url = urlparse(full_url)
                        clean_path = parsed_url.path
                        
                        # Chỉ lấy link chính của công ty (loại bỏ link tin tuyển dụng chi tiết của brand)
                        if "/tuyen-dung/" in clean_path:
                            # Nếu là link dạng brand/tuyen-dung/job-slug, ta trích xuất phần brand trước đó
                            # Ví dụ: /brand/nganhang/tuyen-dung/... -> /brand/nganhang
                            match = re.match(r'(/brand/[^/]+)/tuyen-dung', clean_path)
                            if match:
                                clean_path = match.group(1)
                            else:
                                continue
                        
                        # Bỏ qua các query parameter không cần thiết
                        clean_url = f"https://www.topcv.vn{clean_path}"
                        if parsed_url.query and "id=" in parsed_url.query:
                            # Giữ lại id của brand nếu có
                            q_id = re.search(r'id=\d+', parsed_url.query)
                            if q_id:
                                clean_url = f"{clean_url}?{q_id.group(0)}"
                        
                        # Lấy tên công ty
                        text = link.inner_text().strip()
                        if not text:
                            text = link.get_attribute("title") or ""
                        
                        # Làm sạch tên công ty
                        text = re.sub(r'\s+', ' ', text).strip()
                        
                        if clean_url not in companies or (companies[clean_url] == "" and text != ""):
                            companies[clean_url] = text
            except Exception:
                continue
                
        # Làm sạch danh sách kết quả
        valid_companies = []
        for c_url, c_name in companies.items():
            ignored_names = ["view all", "xem tất cả", "danh sách công ty", "tuyển dụng", "công ty", "brand", "topcv"]
            is_ignored = any(ignored in c_name.lower() for ignored in ignored_names) or len(c_name) < 4
            
            # Loại trừ link chung danh sách công ty của TopCV
            if c_url.endswith("/cong-ty") or c_url.endswith("/cong-ty/"):
                continue
                
            if c_name and not is_ignored:
                valid_companies.append({
                    "name": c_name,
                    "topcv_url": c_url
                })
                
        console.print(f"[green]Tìm thấy {len(valid_companies)} công ty độc nhất trên trang này.[/green]")
        return valid_companies

    def scrape_company_website(self, company_url):
        """Truy cập trang công ty trên TopCV và dùng Regex thông minh trích xuất website chính chủ"""
        console.print(f"[blue]Đang quét thông tin công ty: {company_url}[/blue]")
        
        try:
            self.page.goto(company_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(2.5)
        except Exception as e:
            console.print(f"[red]Lỗi khi truy cập trang công ty {company_url}: {e}[/red]")
            try:
                time.sleep(3)
                self.page.goto(company_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(2.5)
            except Exception:
                return "N/A (Lỗi tải trang)"
        
        if "Cloudflare" in self.page.title():
            self.wait_for_user("Bị chặn bởi Cloudflare khi vào trang công ty. Hãy vượt qua CAPTCHA và nhấn Enter...")
            time.sleep(1)

        try:
            html_content = self.page.content()
            
            # Trích xuất tất cả các liên kết bắt đầu bằng http/https
            urls = re.findall(r'https?://[^\s"\'>]+', html_content)
            unique_urls = list(set(urls))
            
            # Thêm topcv.vn và topcv vào ignored_patterns
            ignored_patterns = [
                "topcv.vn", "topcv", "tophr.vn", "tophr", "happytime.vn", "happytime",
                "testcenter.vn", "testcenter", "itviec.com", "facebook.com", "linkedin.com", "twitter.com", 
                "youtube.com", "google.com", "google.com.vn", "google-analytics.com", "googletagmanager.com",
                "clarity.ms", "newrelic.com", "cloudfront.net", "w3.org", "challenges.cloudflare.com", 
                "hotwired", "jspm.io", "rails", "schema.org", "facebook.net", "licdn.com", 
                "cloudflareinsights.com", "nr-data.net", "github.com", "gitlab.com", 
                "instagram.com", "pinterest.com", "zalo.me", "t.me", "doubleclick.net",
                "custom.transaction", "googleapis.com", "gstatic.com"
            ]
            
            potential_websites = []
            for url in unique_urls:
                url = url.rstrip('),.;/\'"\\')
                if '<' in url:
                    url = url.split('<')[0]
                url = url.strip()
                
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                
                if domain and not any(pattern in domain or pattern in url.lower() for pattern in ignored_patterns):
                    if not url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.css', '.js', '.ico')):
                        potential_websites.append(url)
            
            return potential_websites
        except Exception as e:
            console.print(f"[red]Lỗi khi phân tích website công ty: {e}[/red]")
            return []
