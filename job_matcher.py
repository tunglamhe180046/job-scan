import os
import time
import re
from urllib.parse import urlparse, urljoin
import pandas as pd
from playwright.sync_api import sync_playwright
from rich.console import Console

console = Console()

class JobMatcher:
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
            headless=False,  # Bắt buộc False để người dùng hỗ trợ tương tác/giải captcha
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

    def wait_for_user(self, message="Vui lòng tương tác và nhấn Enter..."):
        """Tạm dừng để người dùng tương tác"""
        console.print(f"\n[bold red]⚠️  {message}[/bold red]")
        input("Nhấn Enter để tiếp tục...")

    def find_careers_page(self, base_url, company_name):
        """Tự động tìm kiếm trang tuyển dụng từ trang chủ của công ty"""
        console.print(f"[blue]Đang mở trang chủ: {base_url}[/blue]")
        
        try:
            self.page.goto(base_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(3)
        except Exception as e:
            console.print(f"[red]Không thể truy cập trang chủ {base_url}: {e}[/red]")
            self.wait_for_user(f"Không thể tải trang chủ của {company_name}.\nVui lòng nhập URL thủ công trên trình duyệt (hoặc vượt CAPTCHA) rồi nhấn Enter...")
        
        career_keywords = [
            "tuyen-dung", "tuyen dung", "tuyển dụng", "careers", "jobs", 
            "career", "job", "join-us", "join us", "joinus", "recruitment", 
            "work-with-us", "work with us", "co-hoi-nghe-nghiep", "viec-lam"
        ]
        
        try:
            links = self.page.locator("a").element_handles()
            for link in links:
                try:
                    href = link.get_attribute("href")
                    text = link.inner_text().strip().lower()
                    
                    if href:
                        href_lower = href.lower()
                        is_match = any(kw in text or kw in href_lower for kw in career_keywords)
                        is_valid_link = not any(x in href_lower for x in ["facebook.com", "linkedin.com", "twitter.com", "google.com"])
                        
                        if is_match and is_valid_link:
                            target_url = urljoin(base_url, href)
                            console.print(f"[green]✓ Tự động tìm thấy link tuyển dụng: {target_url} (Text: '{text}')[/green]")
                            return target_url
                except Exception:
                    continue
        except Exception as e:
            console.print(f"[yellow]Lỗi quét link tự động: {e}[/yellow]")
            
        console.print(f"\n[bold yellow]⚠️  Hệ thống không tự động tìm thấy trang tuyển dụng của: {company_name}[/bold yellow]")
        console.print(f"👉  Website đang mở: [cyan]{self.page.url}[/cyan]")
        self.wait_for_user(
            f"Vui lòng click vào mục 'Tuyển dụng' hoặc 'Careers' trên trình duyệt của {company_name},\n"
            f"đảm bảo trang đã hiển thị danh sách công việc, sau đó nhấn Enter tại đây..."
        )
        
        current_url = self.page.url
        console.print(f"[green]✓ Đã nhận diện trang tuyển dụng thủ công: {current_url}[/green]")
        return current_url

    def extract_jobs_from_page(self, careers_url):
        """Bóc tách toàn bộ tin tuyển dụng thô trên trang tuyển dụng của Website riêng"""
        console.print("[blue]Đang phân tích danh sách công việc trên trang...[/blue]")
        time.sleep(2)
        
        jobs = []
        try:
            elements = self.page.locator("h1, h2, h3, h4, a, li, div").all_inner_texts()
            
            links_handles = self.page.locator("a").element_handles()
            link_map = {}
            for handle in links_handles:
                try:
                    text = handle.inner_text().strip()
                    href = handle.get_attribute("href")
                    if text and href and len(text) > 4:
                        link_map[text.lower()] = urljoin(careers_url, href)
                except Exception:
                    continue
            
            tech_keywords = [
                "developer", "engineer", "lập trình viên", "chuyên viên", "kỹ sư", 
                "intern", "fresher", "junior", "senior", "lead", "principal", "manager",
                "java", "react", ".net", "c#", "ai", "machine learning", "apm", "product", 
                "unity", "flutter", "android", "ios", "mobile", "php", "python", "devops", 
                "tester", "qa", "qc", "tiếng nhật", "japanese"
            ]
            
            seen_titles = set()
            for text in elements:
                text_clean = re.sub(r'\s+', ' ', text).strip()
                if 10 < len(text_clean) < 100:
                    text_lower = text_clean.lower()
                    has_tech = any(kw in text_lower for kw in tech_keywords)
                    is_ignored = any(x in text_lower for x in ["chính sách", "điều khoản", "liên hệ", "giới thiệu", "sản phẩm", "dịch vụ", "tin tức", "blogs", "about us"])
                    
                    if has_tech and not is_ignored:
                        title = text_clean.split('\n')[0].strip()
                        if title.lower() not in seen_titles and len(title) > 8:
                            seen_titles.add(title.lower())
                            
                            job_link = careers_url
                            for t_key, l_val in link_map.items():
                                if t_key in title.lower() or title.lower() in t_key:
                                    job_link = l_val
                                    break
                                    
                            jobs.append({
                                "title": title,
                                "link": job_link
                            })
                            
        except Exception as e:
            console.print(f"[red]Lỗi bóc tách job: {e}[/red]")
            
        console.print(f"[green]✓ Thu thập được {len(jobs)} tin tuyển dụng thô từ website riêng.[/green]")
        return jobs

    def extract_jobs_from_profiles(self, itviec_url, topcv_url):
        """Cào tự động 100% tin tuyển dụng từ trang hồ sơ công ty trên ITviec hoặc TopCV"""
        jobs = []
        
        # 1. Thử cào từ hồ sơ ITviec trước
        if isinstance(itviec_url, str) and itviec_url.startswith("http"):
            console.print(f"[blue]Đang cào tự động từ hồ sơ ITviec: {itviec_url}[/blue]")
            try:
                self.page.goto(itviec_url, wait_until="domcontentloaded", timeout=35000)
                time.sleep(2)
                
                # Cloudflare check
                if "Cloudflare" in self.page.title():
                    self.wait_for_user("Bị chặn bởi Cloudflare. Vui lòng giải captcha và nhấn Enter...")
                
                # Tìm các thẻ .job-card trên trang hồ sơ ITviec
                job_cards = self.page.locator(".job-card").all()
                if job_cards:
                    console.print(f"[green]✓ Tìm thấy {len(job_cards)} job cards thực tế của công ty trên ITviec.[/green]")
                    for card in job_cards:
                        try:
                            # Tìm thẻ link tiêu đề job (có lab_feature=employer_job)
                            title_link = card.locator("a[href*='/viec-lam-it/'][href*='employer_job']").first
                            if title_link.count() > 0:
                                href = title_link.get_attribute("href")
                                text = title_link.inner_text().strip()
                                if text and href:
                                    clean_title = re.sub(r'\s+', ' ', text).strip()
                                    full_href = urljoin("https://itviec.com", href)
                                    jobs.append({
                                        "title": clean_title,
                                        "link": full_href
                                    })
                        except Exception as e:
                            continue
                else:
                    # Fallback quét toàn bộ link nếu không tìm thấy cấu trúc .job-card
                    links = self.page.locator("a").element_handles()
                    for link in links:
                        try:
                            href = link.get_attribute("href")
                            if href and "/viec-lam-it/" in href and "employer_job" in href:
                                text = link.inner_text().strip()
                                if text and len(text) > 4:
                                    clean_title = re.sub(r'\s+', ' ', text).strip()
                                    full_href = urljoin("https://itviec.com", href)
                                    jobs.append({
                                        "title": clean_title,
                                        "link": full_href
                                    })
                        except Exception:
                            continue
            except Exception as e:
                console.print(f"[yellow]Lỗi cào hồ sơ ITviec: {e}[/yellow]")

        # 2. Thử cào từ hồ sơ TopCV
        if isinstance(topcv_url, str) and topcv_url.startswith("http") and not jobs:
            console.print(f"[blue]Đang cào tự động từ hồ sơ TopCV: {topcv_url}[/blue]")
            try:
                self.page.goto(topcv_url, wait_until="domcontentloaded", timeout=35000)
                time.sleep(2)
                
                if "Cloudflare" in self.page.title():
                    self.wait_for_user("Bị chặn bởi Cloudflare. Vui lòng giải captcha và nhấn Enter...")
                
                links = self.page.locator("a").element_handles()
                for link in links:
                    try:
                        href = link.get_attribute("href")
                        # Cấu trúc link tuyển dụng thật của công ty trên TopCV Profile:
                        # /viec-lam/[job-slug]/[job-id].html?ta_source=...
                        if href and "/viec-lam/" in href and ".html" in href:
                            # Tránh dính link chuyển hướng hoặc link công ty khác
                            if "/cong-ty/" not in href and "/brand/" not in href:
                                text = link.inner_text().strip()
                                if not text:
                                    text = link.get_attribute("title") or ""
                                if text and len(text) > 4:
                                    clean_title = re.sub(r'\s+', ' ', text).strip()
                                    # Loại bỏ text rác hoặc các nút điều hướng chung
                                    if not any(x in clean_title.lower() for x in ["xem thêm", "nộp hồ sơ", "tuyển dụng", "hot", "xem chi tiết", "ứng tuyển"]):
                                        full_href = urljoin("https://www.topcv.vn", href)
                                        jobs.append({
                                            "title": clean_title,
                                            "link": full_href
                                        })
                        # Fallback cho dạng link cũ
                        elif href and ("/tuyen-dung/" in href or "/brand/" in href) and href.endswith(".html"):
                            text = link.inner_text().strip()
                            if text and len(text) > 4:
                                clean_title = re.sub(r'\s+', ' ', text).strip()
                                if not any(x in clean_title.lower() for x in ["xem thêm", "nộp hồ sơ", "tuyển dụng", "hot"]):
                                    full_href = urljoin("https://www.topcv.vn", href)
                                    jobs.append({
                                        "title": clean_title,
                                        "link": full_href
                                    })
                    except Exception:
                        continue
            except Exception as e:
                console.print(f"[yellow]Lỗi cào hồ sơ TopCV: {e}[/yellow]")
                
        # Loại bỏ trùng lặp tin tuyển dụng
        unique_jobs = []
        seen = set()
        for j in jobs:
            t_low = j["title"].lower()
            if t_low not in seen:
                seen.add(t_low)
                unique_jobs.append(j)
                
        console.print(f"[green]✓ Thu thập được {len(unique_jobs)} tin tuyển dụng tự động từ Profile.[/green]")
        return unique_jobs

    def evaluate_job(self, title, company_name):
        """Đánh giá độ phù hợp của công việc đối với bạn Nguyễn Tùng Lâm (chấm điểm từ 1-10)"""
        title_lower = title.lower()
        
        # 1. Đánh giá Level kinh nghiệm (Lọc bỏ >= 3 năm kinh nghiệm và Intern/Trainee)
        is_senior = any(kw in title_lower for kw in ["senior", "lead", "principal", "manager", "head", "director", "expert", "architect", "specialist"])
        is_intern = any(kw in title_lower for kw in ["intern", "internship", "trainee", "co-op", "thực tập", "thực tập sinh", "học việc"])
        
        # Ngoại lệ: Nếu là job AI Workflow ngách, dù ghi Senior vẫn cho cơ hội
        is_ai_workflow = "ai workflow" in title_lower or ("ai" in title_lower and "workflow" in title_lower)
        
        level_score = 10
        level_note = "Phù hợp (Junior/Fresher)"
        
        if is_senior:
            if is_ai_workflow:
                level_score = 6
                level_note = "Yêu cầu Level Cao nhưng đúng mảng AI Workflow ngách (Nên thử)"
            else:
                level_score = 3
                level_note = "Level Cao (Senior/Lead/Manager) - Không phù hợp tiêu chí <= 2 năm"
        elif is_intern:
            level_score = 3
            level_note = "Internship/Trainee - Loại bỏ theo yêu cầu của bạn"
                
        # 2. Đánh giá Stack công nghệ & Ngôn ngữ
        tech_score = 0
        match_reason = ""
        
        # Stack 1: AI Tools & AI Workflow Design (Ưu tiên số 1 - USP độc nhất của Lâm)
        if is_ai_workflow:
            tech_score = 10
            match_reason = "Đúng thế mạnh độc quyền AI Workflow Design!"
        elif "ai product" in title_lower or "ai builder" in title_lower or "ai engineer" in title_lower:
            tech_score = 9.5
            match_reason = "Công việc AI Product Builder/AI Engineer rất tiềm năng."
            
        # Stack 2: APM / Product Owner yêu cầu tiếng Nhật/Anh
        elif "apm" in title_lower or "associate product manager" in title_lower or "product manager" in title_lower or "product owner" in title_lower:
            if any(x in title_lower for x in ["japanese", "tiếng nhật", "nhật"]):
                tech_score = 9.0
                match_reason = "Vị trí APM yêu cầu tiếng Nhật (JLPT N4 & FPT Japan intern của bạn)."
            else:
                tech_score = 8.0
                match_reason = "Vị trí APM phù hợp với IELTS 6.5 và leadership của bạn."
                
        # Stack 3: Mobile App & Unity Development
        elif any(x in title_lower for x in ["android", "ios", "unity", "flutter", "react native", "mobile"]):
            if any(x in title_lower for x in ["japanese", "tiếng nhật", "nhật"]):
                tech_score = 9.0
                match_reason = "Lập trình viên Mobile yêu cầu tiếng Nhật (Kaopiz Unity/Mobile + N4)."
            else:
                tech_score = 8.0
                match_reason = "Lập trình viên Mobile/Unity phù hợp với kinh nghiệm tại Kaopiz."
                
        # Stack 4: Java & ReactJS Full-stack (Stack mạnh thời đại học)
        elif "java" in title_lower and "react" in title_lower:
            tech_score = 9.0
            match_reason = "Full-stack Java & ReactJS (đúng dự án DORM của bạn)."
        elif "java" in title_lower:
            tech_score = 7.5
            match_reason = "Lập trình viên Java (đúng Spring Boot của bạn)."
        elif "react" in title_lower:
            tech_score = 7.5
            match_reason = "Lập trình viên ReactJS."
        elif "net" in title_lower or "c#" in title_lower:
            tech_score = 7.5
            match_reason = "Lập trình viên .NET/C# (đúng kỳ thực tập NIC Global)."
            
        # Các mảng công nghệ lân cận
        elif any(x in title_lower for x in ["software", "developer", "engineer", "lập trình viên"]):
            tech_score = 6.0
            match_reason = "Lập trình viên phần mềm chung."
        elif any(x in title_lower for x in ["tester", "qa", "qc"]):
            tech_score = 5.0
            match_reason = "Vị trí QA/QC (bạn có kinh nghiệm làm Automation Testing)."
        else:
            tech_score = 2.0
            match_reason = "Công việc non-IT hoặc không đúng chuyên môn."
            
        # 3. Tính điểm tổng hợp (Kết hợp Level và Stack)
        final_score = min(level_score, tech_score)
        
        if is_senior and not is_ai_workflow:
            final_score = 3.0
        elif is_intern:
            final_score = 3.0
            
        return {
            "score": final_score,
            "level": level_note,
            "reason": match_reason
        }
