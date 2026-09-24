import os
import time
import re
from urllib.parse import urlparse
import pandas as pd
from playwright.sync_api import sync_playwright
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

console = Console()

def safe_save_excel(df, path):
    """Ghi đè file Excel an toàn. Nếu file đang mở (bị khóa), ghi ra file mới có timestamp"""
    try:
        df.to_excel(path, index=False)
        return path
    except PermissionError:
        import time
        timestamp = int(time.time())
        base, ext = os.path.splitext(path)
        new_path = f"{base}_{timestamp}{ext}"
        df.to_excel(new_path, index=False)
        console.print(f"[yellow]⚠️  File '{path}' đang mở hoặc bị khóa. Đã lưu dự phòng sang: '{new_path}'[/yellow]")
        return new_path

class ApplyAssistant:
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
            headless=False,
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
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()
        console.print("[yellow]Trình duyệt đã được đóng.[/yellow]")

    def check_if_already_applied(self):
        """Kiểm tra trên DOM trang web xem job này đã được nộp trước đó hay chưa"""
        try:
            applied_indicators = [
                ".applied-badge",
                "button:has-text('Đã ứng tuyển')",
                "a:has-text('Đã ứng tuyển')",
                "div:has-text('Đã ứng tuyển')",
                ".btn-applied",
                "button[disabled]:has-text('Applied')",
                "button[disabled]:has-text('Đã nộp')"
            ]
            for sel in applied_indicators:
                element = self.page.locator(sel).first
                if element.count() > 0 and element.is_visible():
                    return True
        except Exception as e:
            console.print(f"[yellow]Lỗi kiểm tra nút ứng tuyển: {e}[/yellow]")
        return False

    def generate_cover_letter(self, title, company_name):
        """Tự động sinh Cover Letter cá nhân hóa dựa trên tiêu đề công việc"""
        title_lower = title.lower()
        
        # 1. Mẫu AI
        if any(k in title_lower for k in ["ai", "workflow", "prompt", "agent", "llm", "rag"]):
            return f"""Dear Hiring Manager,

I am very excited to apply for the {title} position at {company_name}. As an AI Agent Engineer at Minh Bach JSC specializing in enterprise digital transformation and full-stack software development, I possess deep technical expertise in Python, LLMs, RAG, Multimodal Vision pipelines, Agent Memory Management (Short-term/Long-term), and Skill Orchestration (Waterfall Skills architecture).

In my recent work, I authored open-source architectures including Word Tools (an in-place DOCX surgical engine with optimistic locking for AI agents) and Google Maps Radar (a multimodal spatial intelligence and multi-agent system). Additionally, my Software Engineering degree from FPT University equips me with strong foundations in Python, Node.js, Java (Spring Boot), ReactJS, and .NET.

I am confident that my practical experience in AI Agent engineering, RAG, and workflow optimization will allow me to create immediate impact at {company_name}. Thank you for your time and consideration.

Sincerely,
Nguyen Tung Lam"""

        # 2. Mẫu APM / Bridge SE / Yêu cầu tiếng Nhật
        elif any(x in title_lower for x in ["apm", "product manager", "product owner", "bridge", "japanese", "tiếng nhật", "nhật"]):
            return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {title} position at {company_name}. Having graduated in Software Engineering from FPT University and completed a 3-month internship in Japan, I have developed both technical knowledge and cross-cultural communication skills.

I possess JLPT N4 (Japanese) and IELTS 6.5 (English), which allow me to collaborate effectively in international teams. During my time in Japan and at Kaopiz, I worked closely with customers and development teams to clarify requirements and manage project milestones. I am eager to apply my leadership and bilingual capabilities to help {company_name} deliver successful products.

Thank you for considering my application. I look forward to the opportunity to discuss how I can contribute to your team.

Sincerely,
Nguyen Tung Lam"""

        # 3. Mẫu Mobile App / Unity
        elif any(x in title_lower for x in ["android", "ios", "unity", "flutter", "react native", "mobile"]):
            return f"""Dear Hiring Manager,

I am writing to apply for the {title} position at {company_name}. As a Software Engineering graduate from FPT University with practical experience developing mobile apps and front-end solutions, I am eager to contribute to {company_name}'s mobile products.

During my internship and project work at Kaopiz, I gained hands-on experience developing front-end applications and working with mobile technologies and Unity. I am highly adaptable, detail-oriented, and proficient in Git workflows. I am excited to apply my skills to build smooth and responsive mobile experiences for your users.

Thank you for your time and consideration.

Sincerely,
Nguyen Tung Lam"""

        # 4. Mẫu Java / ReactJS / .NET
        elif any(x in title_lower for x in ["java", "react", "spring boot", "net", "c#"]):
            return f"""Dear Hiring Manager,

I am very interested in the {title} position at {company_name}. With solid experience in Java (Spring Boot), ReactJS, and C# (.NET), I am confident in my ability to contribute to your engineering team immediately.

Throughout my software engineering coursework and enterprise projects, I have developed scalable web applications using Java Spring Boot and ReactJS, designing RESTful APIs and handling transactional business logic. I also completed an internship at NIC Global where I developed C#/.NET enterprise systems. I am passionate about writing clean, maintainable code and collaborating in agile teams.

Thank you for considering my application. I hope to have the chance to discuss my qualifications with you in an interview.

Sincerely,
Nguyen Tung Lam"""

        # 5. Mẫu chung
        else:
            return f"""Dear Hiring Manager,

I am writing to express my interest in the {title} position at {company_name}. As a Software Engineering graduate from FPT University (December 2025), I have built strong foundations in software development methodologies, version control (Git), and agile team collaboration.

I am proficient in Java, ReactJS, .NET, and have a strong interest in AI-assisted development to enhance coding efficiency. I have also achieved an IELTS score of 6.5 and completed an internship working in bilingual environments. I am highly motivated to learn and contribute to {company_name}.

Thank you for your time and consideration.

Sincerely,
Nguyen Tung Lam"""

    def autofill_cover_letter(self, cover_letter):
        """Tự động điền Cover Letter vào form ứng tuyển trên trình duyệt nếu có"""
        try:
            # Các selector phổ biến của ô nhập Cover Letter/Thư giới thiệu
            selectors = [
                "textarea[placeholder*='cover letter']", 
                "textarea[placeholder*='giới thiệu']",
                "textarea[placeholder*='introduce']",
                "textarea[name*='cover_letter']",
                "textarea[id*='cover-letter']",
                "textarea[id*='introduce']",
                ".cover-letter-editor div[contenteditable='true']",
                "#cover-letter-textarea",
                "textarea.cover-letter-textarea"
            ]
            
            for selector in selectors:
                element = self.page.locator(selector).first
                if element.count() > 0:
                    element.click()
                    element.fill(cover_letter)
                    console.print(f"[green]✓ Đã tự động điền Cover Letter vào trường: '{selector}'[/green]")
                    return True
        except Exception as e:
            console.print(f"[yellow]Lỗi tự động điền Cover Letter: {e}[/yellow]")
        return False

    def run_assistant(self):
        """Khởi chạy giao diện và quy trình hỗ trợ ứng tuyển bán tự động"""
        report_file = "reports/matched_jobs_report.xlsx"
        
        if not os.path.exists(report_file):
            console.print(f"[bold red]❌ Không tìm thấy file kết quả khớp công việc '{report_file}'. Vui lòng chạy tính năng số 3 trước.[/bold red]")
            return
            
        try:
            df = pd.read_excel(report_file)
        except Exception as e:
            console.print(f"[bold red]❌ Lỗi đọc file Excel: {e}[/bold red]")
            return
            
        if df.empty:
            console.print("[yellow]Danh sách công việc trống. Không có công việc nào để ứng tuyển.[/yellow]")
            return
            
        # Đảm bảo có 2 cột quản lý trạng thái
        if "Trạng Thái Ứng Tuyển" not in df.columns:
            df["Trạng Thái Ứng Tuyển"] = "Chưa ứng tuyển"
        if "Ngày Ứng Tuyển" not in df.columns:
            df["Ngày Ứng Tuyển"] = "N/A"
            
        console.print(f"\n[bold green]=== HỆ THỐNG HỖ TRỢ ỨNG TUYỂN BÁN TỰ ĐỘNG (APPLY ASSISTANT) ===[/bold green]")
        
        # Hiển thị danh sách công việc để người dùng lựa chọn
        table = Table(title="Danh Sách Việc Làm Phù Hợp Đã Lọc")
        table.add_column("STT", style="dim")
        table.add_column("Công ty", style="cyan")
        table.add_column("Vị Trí Tuyển Dụng", style="magenta")
        table.add_column("Điểm", style="bold yellow")
        table.add_column("Trạng Thái", style="bold green")
        table.add_column("Ngày Nộp", style="dim blue")
        table.add_column("Lý Do Khớp", style="green")
        
        for idx, row in df.iterrows():
            title_val = row["Vị Trí Tuyển Dụng"] if "Vị Trí Tuyển Dụng" in df.columns else row.iloc[1]
            score_val = row["Điểm Phù Hợp (1-10)"] if "Điểm Phù Hợp (1-10)" in df.columns else row.iloc[2]
            reason_val = row["Lý Do Khớp"] if "Lý Do Khớp" in df.columns else row.iloc[4]
            status_val = str(row.get("Trạng Thái Ứng Tuyển", "Chưa ứng tuyển"))
            date_val = str(row.get("Ngày Ứng Tuyển", "N/A"))
            
            status_style = "bold green" if status_val == "Đã ứng tuyển" else "yellow"
            
            table.add_row(
                str(idx + 1),
                str(row["Tên Công Ty"]),
                str(title_val),
                str(score_val),
                f"[{status_style}]{status_val}[/{status_style}]",
                date_val,
                str(reason_val)
            )
        console.print(table)
        
        # Nhận lựa chọn từ người dùng
        selection = Prompt.ask(
            "[bold]Nhập danh sách STT bạn muốn ứng tuyển[/bold] (Ví dụ: 1,3,5 hoặc nhập 'all' để nộp tất cả)", 
            default="1"
        )
        
        indices_to_apply = []
        if selection.lower() == 'all':
            indices_to_apply = list(range(len(df)))
        else:
            try:
                parts = [p.strip() for p in selection.split(",")]
                for p in parts:
                    idx = int(p) - 1
                    if 0 <= idx < len(df):
                        indices_to_apply.append(idx)
            except ValueError:
                console.print("[red]Lựa chọn không hợp lệ. Thoát chương trình.[/red]")
                return
                
        if not indices_to_apply:
            console.print("[yellow]Không có công việc nào được chọn.[/yellow]")
            return
            
        # Khởi động trình duyệt
        self.start_browser()
        
        try:
            for count, idx in enumerate(indices_to_apply):
                row = df.iloc[idx]
                comp_name = row["Tên Công Ty"]
                title = row["Vị Trí Tuyển Dụng"] if "Vị Trí Tuyển Dụng" in df.columns else row.iloc[1]
                job_url = row["Link Ứng Tuyển"] if "Link Ứng Tuyển" in df.columns else row.iloc[5]
                current_status = str(row.get("Trạng Thái Ứng Tuyển", "Chưa ứng tuyển"))
                apply_date = str(row.get("Ngày Ứng Tuyển", "N/A"))
                
                console.print(f"\n[bold cyan]============================================================[/bold cyan]")
                console.print(f"👉 [{count+1}/{len(indices_to_apply)}] Tiến hành ứng tuyển: [bold]{title}[/bold] tại [bold]{comp_name}[/bold]")
                
                if current_status == "Đã ứng tuyển":
                    console.print(f"[bold yellow]⚠️  Dữ liệu ghi nhận job này ĐÃ ỨNG TUYỂN vào ngày: {apply_date}[/bold yellow]")
                    skip_choice = Prompt.ask("Bạn có muốn mở lại trang để xem/nộp lại không?", choices=["y", "n"], default="n")
                    if skip_choice.lower() == "n":
                        console.print("[yellow]-> Bỏ qua job đã ứng tuyển.[/yellow]")
                        continue

                if not isinstance(job_url, str) or not job_url.startswith("http"):
                    console.print(f"[red]❌ Link ứng tuyển không hợp lệ: {job_url}[/red]")
                    continue
                    
                # 1. Sinh Cover Letter cá nhân hóa
                cover_letter = self.generate_cover_letter(title, comp_name)
                
                console.print(f"\n[bold yellow]📝 COVER LETTER ĐƯỢC AI SOẠN RIÊNG CHO BẠN:[/bold yellow]")
                console.print(f"[italic]{cover_letter}[/italic]\n")
                
                # 2. Mở trang ứng tuyển
                console.print(f"[blue]Đang mở link ứng tuyển: {job_url}[/blue]")
                try:
                    self.page.goto(job_url, wait_until="domcontentloaded", timeout=45000)
                    time.sleep(3)
                except Exception as e:
                    console.print(f"[red]Lỗi không thể tải trang ứng tuyển: {e}[/red]")
                
                # 3. Tự động kiểm tra DOM xem đã nộp trước đó chưa
                if self.check_if_already_applied():
                    console.print(f"[bold green]✓ TỰ ĐỘNG PHÁT HIỆN: Nút 'Đã ứng tuyển' trên trang web đang bật![/bold green]")
                    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
                    df.at[idx, "Trạng Thái Ứng Tuyển"] = "Đã ứng tuyển"
                    if str(df.at[idx, "Ngày Ứng Tuyển"]) == "N/A":
                        df.at[idx, "Ngày Ứng Tuyển"] = now_str
                    safe_save_excel(df, report_file)
                    
                    cont_choice = Prompt.ask("Trang web xác nhận bạn đã ứng tuyển job này. Bạn có muốn xem tiếp job khác không?", choices=["y", "n"], default="y")
                    if cont_choice.lower() == "y":
                        continue
                    
                # 4. Tự động điền Cover Letter (nếu tìm thấy trường text)
                autofilled = self.autofill_cover_letter(cover_letter)
                if not autofilled:
                    console.print("[yellow]⚠️  Không thể tự động điền Cover Letter. Bạn vui lòng copy bức thư trên để dán thủ công nếu cần.[/yellow]")
                
                # 5. Chờ người dùng kiểm tra và nộp đơn bằng tay
                console.print(f"\n[bold green]👉 Vui lòng hoàn tất ứng tuyển trên trình duyệt (Chọn CV, điền thông tin bổ sung và bấm 'Nộp đơn').[/bold green]")
                console.print(f"[bold red]⚠️  SAU KHI ĐÃ BẤM NỘP ĐƠN THÀNH CÔNG, quay lại đây nhấn Enter để lưu trạng thái & chuyển tiếp...[/bold red]")
                input("Nhấn Enter để ghi nhận 'Đã ứng tuyển'...")
                
                # Ghi nhận trạng thái và lưu file Excel ngay lập tức
                now_str = time.strftime("%Y-%m-%d %H:%M:%S")
                df.at[idx, "Trạng Thái Ứng Tuyển"] = "Đã ứng tuyển"
                df.at[idx, "Ngày Ứng Tuyển"] = now_str
                actual_path = safe_save_excel(df, report_file)
                console.print(f"[bold green]✓ Đã cập nhật trạng thái 'Đã ứng tuyển' ({now_str}) vào file: {actual_path}[/bold green]")
                
            console.print("\n[bold green]✓ Quá trình hỗ trợ ứng tuyển bán tự động đã hoàn tất![/bold green]")
            
        except Exception as e:
            console.print(f"[bold red]Lỗi hệ thống: {e}[/bold red]")
        finally:
            self.close_browser()

if __name__ == "__main__":
    assistant = ApplyAssistant()
    assistant.run_assistant()
