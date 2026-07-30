import os
import json
import time
import re
from urllib.parse import urlparse, urljoin
import pandas as pd
from playwright.sync_api import sync_playwright
from rich.console import Console

console = Console()

class ITViecScraper:
    def __init__(self, user_data_dir="./user_data"):
        self.user_data_dir = os.path.abspath(user_data_dir)
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        # Đảm bảo thư mục dữ liệu người dùng tồn tại
        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)

    def start_browser(self):
        """Khởi động trình duyệt Playwright với User Data Dir để lưu session"""
        console.print("[yellow]Đang khởi động trình duyệt Chromium...[/yellow]")
        self.playwright = sync_playwright().start()
        
        # Sử dụng launch_persistent_context để giữ session (bán tự động)
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=False,  # Bắt buộc False để người dùng có thể tương tác/giải captcha
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ],
            no_viewport=True
        )
        
        # Tạo trang mới
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()
            
        # Thêm một số thuộc tính giả lập người dùng thật
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
        """Cào danh sách công ty từ trang danh sách việc làm ITviec"""
        console.print(f"[blue]Đang truy cập trang danh sách: {url}[/blue]")
        
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            console.print(f"[red]Lỗi khi tải trang: {e}[/red]")
            self.wait_for_user("Lỗi tải trang. Hãy kiểm tra trình duyệt, tải lại trang và nhấn Enter tại đây...")
        
        # Đợi một chút để trang load hoàn toàn các phần tử động
        time.sleep(3)
        
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
                    # Link công ty trên ITviec có thể ở dạng:
                    # - Tiếng Việt: /nha-tuyen-dung/ten-cong-ty
                    # - Tiếng Anh: /companies/ten-cong-ty
                    if "/companies/" in href or "/nha-tuyen-dung/" in href:
                        # Chuyển link tương đối thành tuyệt đối
                        full_url = urljoin("https://itviec.com", href)
                        
                        # Trích xuất loại link và slug
                        match = re.search(r'/(companies|nha-tuyen-dung)/([^/?#]+)', full_url)
                        if match:
                            path_type = match.group(1)
                            slug = match.group(2)
                            
                            # Làm sạch slug (bỏ phần phụ)
                            clean_slug = slug.split('/')[0]
                            clean_url = f"https://itviec.com/{path_type}/{clean_slug}"
                            
                            # Lấy tên công ty từ nội dung thẻ a hoặc thẻ con của nó
                            text = link.inner_text().strip()
                            if not text:
                                text = link.get_attribute("title") or ""
                            
                            # Làm sạch tên công ty (loại bỏ xuống dòng, khoảng trắng thừa)
                            text = re.sub(r'\s+', ' ', text).strip()
                            
                            # Chỉ cập nhật nếu chưa có hoặc tên công ty hiện tại trống
                            if clean_url not in companies or (companies[clean_url] == "" and text != ""):
                                companies[clean_url] = text
            except Exception:
                # Bỏ qua các phần tử bị lỗi DOM trong quá trình duyệt
                continue
                
        # Làm sạch kết quả: loại bỏ các công ty có tên trống hoặc không hợp lệ
        valid_companies = []
        for c_url, c_name in companies.items():
            # Loại bỏ các text menu điều hướng hoặc các nút bấm chung
            ignored_names = ["view all", "xem tất cả", "nhà tuyển dụng", "companies", "công ty", "review"]
            is_ignored = any(ignored in c_name.lower() for ignored in ignored_names)
            
            if c_name and len(c_name) > 1 and not is_ignored:
                valid_companies.append({
                    "name": c_name,
                    "itviec_url": c_url
                })
                
        console.print(f"[green]Tìm thấy {len(valid_companies)} công ty độc nhất trên trang này.[/green]")
        return valid_companies

    def scrape_company_website(self, company_url):
        """Truy cập trang công ty trên ITviec và dùng Regex thông minh trích xuất website chính chủ"""
        console.print(f"[blue]Đang quét thông tin công ty: {company_url}[/blue]")
        
        try:
            self.page.goto(company_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(2)
        except Exception as e:
            console.print(f"[red]Lỗi khi truy cập trang công ty {company_url}: {e}[/red]")
            # Thử lại 1 lần nữa sau khi dừng 3s
            try:
                time.sleep(3)
                self.page.goto(company_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(2)
            except Exception:
                return "N/A (Lỗi tải trang)"
        
        # Kiểm tra xem có Cloudflare hay không
        if "Cloudflare" in self.page.title():
            self.wait_for_user("Bị chặn bởi Cloudflare khi vào trang công ty. Hãy vượt qua CAPTCHA và nhấn Enter...")
            time.sleep(1)

        try:
            # Lấy toàn bộ mã nguồn HTML của trang công ty
            html_content = self.page.content()
            
            # Trích xuất tất cả các liên kết bắt đầu bằng http/https
            urls = re.findall(r'https?://[^\s"\'>]+', html_content)
            unique_urls = list(set(urls))
            
            # Danh sách các domain hệ thống cần bỏ qua
            ignored_patterns = [
                "itviec.com", "facebook.com", "linkedin.com", "twitter.com", "youtube.com", 
                "google.com", "google.com.vn", "google-analytics.com", "googletagmanager.com",
                "clarity.ms", "newrelic.com", "cloudfront.net", "w3.org", "challenges.cloudflare.com", 
                "hotwired", "jspm.io", "rails", "schema.org", "facebook.net", "licdn.com", 
                "cloudflareinsights.com", "nr-data.net", "github.com", "gitlab.com", 
                "instagram.com", "pinterest.com", "zalo.me", "t.me", "doubleclick.net",
                "custom.transaction", "googleapis.com", "gstatic.com"
            ]
            
            potential_websites = []
            for url in unique_urls:
                # Làm sạch URL nếu có ký tự lạ ở cuối do regex bắt nhầm
                url = url.rstrip('),.;/\'"\\')
                
                # Cắt bỏ các tag HTML hoặc ký tự lạ dính ở đuôi nếu regex quét nhầm (ví dụ: </p>, </div>)
                if '<' in url:
                    url = url.split('<')[0]
                url = url.strip()
                
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                
                # Nếu domain hợp lệ và không nằm trong danh sách bỏ qua
                if domain and not any(pattern in domain or pattern in url.lower() for pattern in ignored_patterns):
                    # Loại bỏ các file tĩnh
                    if not url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.css', '.js', '.ico')):
                        potential_websites.append(url)
            
            return potential_websites
        except Exception as e:
            console.print(f"[red]Lỗi khi phân tích website công ty: {e}[/red]")
            return []

    def get_next_page_url(self, current_url):
        """Tự động tính toán URL trang tiếp theo dựa trên URL hiện tại"""
        parsed = urlparse(current_url)
        query = parsed.query
        
        if not query:
            next_query = "page=2"
        elif "page=" in query:
            def repl(match):
                page_num = int(match.group(1))
                return f"page={page_num + 1}"
            next_query = re.sub(r'page=(\d+)', repl, query)
        else:
            next_query = f"{query}&page=2"
            
        next_url = parsed._replace(query=next_query).geturl()
        return next_url
