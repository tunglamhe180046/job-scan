import os
import time
import re
from urllib.parse import urlparse
import pandas as pd
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from scraper import ITViecScraper
from topcv_scraper import TopCVScraper
from topdev_scraper import TopDevScraper
from job_matcher import JobMatcher
from apply_assistant import ApplyAssistant

console = Console()

def print_banner():
    console.print("\n" + "="*60, style="bold cyan")
    console.print("         🚀 Job Board Company Scraper & Matcher 🚀", style="bold green")
    console.print("             (ITviec, TopCV.vn & CV Matcher)", style="italic yellow")
    console.print("="*60 + "\n", style="bold cyan")

def save_data(data, output_file, platform):
    """Lưu dữ liệu ra file Excel hoặc CSV"""
    df = pd.DataFrame(data)
    
    # Chuẩn hóa tên cột
    url_col_name = "Link ITviec" if platform == "1" else "Link TopCV"
    df.columns = ["Tên Công Ty", url_col_name, "Website Công Ty"]
    
    # Loại bỏ trùng lặp nếu có
    df = df.drop_duplicates(subset=[url_col_name])
    
    file_ext = os.path.splitext(output_file)[1].lower()
    
    try:
        if file_ext == '.xlsx':
            df.to_excel(output_file, index=False)
        else:
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
        console.print(f"[green]✓ Đã lưu thành công {len(df)} dòng dữ liệu vào file: {output_file}[/green]")
    except Exception as e:
        console.print(f"[red]❌ Lỗi khi lưu file {output_file}: {e}[/red]")
        backup_csv = f"backup_companies_{int(time.time())}.csv"
        df.to_csv(backup_csv, index=False, encoding='utf-8-sig')
        console.print(f"[yellow]⚠️ Đã lưu dự phòng vào file: {backup_csv}[/yellow]")

def get_topcv_page_url(base_url, page_num):
    """Tạo URL phân trang cho TopCV"""
    parsed = urlparse(base_url)
    query = parsed.query
    if not query:
        next_query = f"page={page_num}"
    elif "page=" in query:
        next_query = re.sub(r'page=\d+', f"page={page_num}", query)
    else:
        next_query = f"{query}&page={page_num}"
    return parsed._replace(query=next_query).geturl()

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

def run_job_matching():
    """Chạy chức năng cào và đối chiếu tin tuyển dụng phù hợp với CV"""
    console.print("\n[bold green]=== KHỞI CHẠY BỘ QUÉT TIN TUYỂN DỤNG & ĐỐI CHIẾU CV ===[/bold green]")
    merged_file = "reports/all_companies_merged.xlsx"
    output_file = "reports/matched_jobs_report.xlsx"
    
    if not os.path.exists(merged_file):
        if os.path.exists("all_companies_merged.xlsx"):
            merged_file = "all_companies_merged.xlsx"
        else:
            console.print(f"[bold red]❌ Không tìm thấy file dữ liệu gộp {merged_file}. Vui lòng chạy cào danh sách công ty trước.[/bold red]")
            return
        
    try:
        df_merged = pd.read_excel(merged_file)
    except Exception as e:
        console.print(f"[bold red]❌ Lỗi đọc file {merged_file}: {e}[/bold red]")
        return
        
    console.print(f"Đã đọc danh sách: [bold yellow]{len(df_merged)} công ty[/bold yellow] từ file {merged_file}.")
    
    # Cho phép người dùng giới hạn số lượng công ty quét thử nghiệm
    num_to_scan = Prompt.ask("[bold]Nhập số lượng công ty muốn quét tuyển dụng[/bold] (Nhấn Enter để quét tất cả)", default=str(len(df_merged)))
    try:
        num_to_scan = min(int(num_to_scan), len(df_merged))
    except ValueError:
        num_to_scan = len(df_merged)
        
    df_to_scan = df_merged.head(num_to_scan)
    
    # Hỏi người dùng chọn chế độ quét
    console.print("\n[bold]Chọn chế độ quét việc làm:[/bold]")
    console.print("1. Quét tự động qua Hồ sơ ITviec/TopCV (Tự động 100% - Khuyên dùng khi chạy nhiều)")
    console.print("2. Quét trực tiếp qua Website riêng của từng công ty (Bán tự động - Cần tương tác)")
    mode = Prompt.ask("Nhập chế độ (1 hoặc 2)", choices=["1", "2"], default="1")
    
    # Đọc lịch sử đã ứng tuyển cũ để không bị ghi đè
    applied_history = {}
    if os.path.exists(output_file):
        try:
            df_old = pd.read_excel(output_file)
            for _, r in df_old.iterrows():
                link_old = r.get("Link Ứng Tuyển")
                status_old = r.get("Trạng Thái Ứng Tuyển", "Chưa ứng tuyển")
                date_old = r.get("Ngày Ứng Tuyển", "N/A")
                if link_old and status_old == "Đã ứng tuyển":
                    applied_history[link_old] = (status_old, date_old)
        except Exception:
            pass

    matcher = JobMatcher()
    matched_jobs = []
    
    try:
        matcher.start_browser()
        
        for idx, row in df_to_scan.iterrows():
            comp_name = row["Tên Công Ty"]
            website = row["Website Công Ty"]
            it_url = row.get("Link ITviec", "")
            top_url = row.get("Link TopCV", "")
            
            console.print(f"\n[bold cyan]------------------------------------------------------------[/bold cyan]")
            console.print(f"👉 [{idx+1}/{num_to_scan}] Đang xử lý công ty: [bold]{comp_name}[/bold]")
            
            jobs_raw = []
            
            if mode == "1":
                # Chế độ 1: Tự động qua profiles
                jobs_raw = matcher.extract_jobs_from_profiles(it_url, top_url)
            else:
                # Chế độ 2: Bán tự động qua website riêng
                if not isinstance(website, str) or website.lower() in ["nan", "n/a", ""]:
                    console.print(f"[yellow]✗ Bỏ qua {comp_name} vì không có website chính thức.[/yellow]")
                    continue
                careers_url = matcher.find_careers_page(website, comp_name)
                jobs_raw = matcher.extract_jobs_from_page(careers_url)
            
            # Lọc và chấm điểm từng job
            matched_count = 0
            for job in jobs_raw:
                title = job["title"]
                link = job["link"]
                
                evaluation = matcher.evaluate_job(title, comp_name)
                if evaluation["score"] >= 5.0:
                    status_val, date_val = applied_history.get(link, ("Chưa ứng tuyển", "N/A"))
                    matched_jobs.append({
                        "Tên Công Ty": comp_name,
                        "Vị Trí Tuyển Dụng": title,
                        "Điểm Phù Hợp (1-10)": evaluation["score"],
                        "Đánh Giá Kinh Nghiệm": evaluation["level"],
                        "Lý Do Khớp": evaluation["reason"],
                        "Link Ứng Tuyển": link,
                        "Trạng Thái Ứng Tuyển": status_val,
                        "Ngày Ứng Tuyển": date_val
                    })
                    matched_count += 1
                    
            console.print(f"[green]✓ Đã lọc được {matched_count} job phù hợp từ {comp_name}.[/green]")
            
            # Lưu tạm kết quả sau mỗi công ty
            if matched_jobs:
                df_temp = pd.DataFrame(matched_jobs)
                df_temp = df_temp.sort_values(by="Điểm Phù Hợp (1-10)", ascending=False)
                safe_save_excel(df_temp, output_file)
                
            time.sleep(2)
            
        # Lưu kết quả cuối cùng
        console.print(f"\n[bold green]=== HOÀN THÀNH QUÉT TUYỂN DỤNG ===[/bold green]")
        if matched_jobs:
            df_final = pd.DataFrame(matched_jobs)
            df_final = df_final.sort_values(by="Điểm Phù Hợp (1-10)", ascending=False)
            actual_saved_path = safe_save_excel(df_final, output_file)
            console.print(f"[green]✓ Đã lưu thành công [bold yellow]{len(df_final)}[/bold yellow] công việc phù hợp nhất vào file: {actual_saved_path}[/green]")
            
            # Hiển thị TOP 10 công việc phù hợp nhất lên màn hình
            table = Table(title="TOP 10 CÔNG VIỆC PHÙ HỢP NHẤT CHO BẠN")
            table.add_column("Điểm", style="bold yellow")
            table.add_column("Công ty", style="cyan")
            table.add_column("Vị Trí", style="magenta")
            table.add_column("Lý Do Khớp", style="green")
            
            for item in matched_jobs[:10]:
                table.add_row(
                    str(item["Điểm Phù Hợp (1-10)"]),
                    item["Tên Công Ty"],
                    item["Vị Trí Tuyển Dụng"],
                    item["Lý Do Khớp"]
                )
            console.print(table)
        else:
            console.print("[yellow]✗ Không tìm thấy công việc nào phù hợp với CV của bạn trong đợt quét này.[/yellow]")
            
    except Exception as e:
        console.print(f"[bold red]Đã xảy ra lỗi hệ thống: {e}[/bold red]")
        import traceback
        traceback.print_exc()
    finally:
        matcher.close_browser()

def run_apply_assistant():
    """Chạy chức năng hỗ trợ ứng tuyển bán tự động"""
    assistant = ApplyAssistant()
    assistant.run_assistant()

def run_topdev_job_scan():
    """Read a TopDev/Saramin search URL and verify job availability page by page."""
    scraper = TopDevScraper()
    default_url = (
        "https://topdev.vn/viec-lam/tim-kiem?job_categories_ids="
        "2%2C3%2C4%2C5%2C6%2C7%2C8%2C9%2C10%2C11%2C12%2C13%2C67&keyword=&region_ids=01"
    )
    listing_url = Prompt.ask("[bold]Enter TopDev/Saramin search URL[/bold]", default=default_url)
    pages_to_scan = Prompt.ask("[bold]Number of TopDev pages to read[/bold]", default="6")
    try:
        pages_to_scan = max(1, int(pages_to_scan))
    except ValueError:
        pages_to_scan = 6

    try:
        scraper.start_browser()
        scraper.wait_for_user(
            "Wait until the TopDev job cards are fully visible. If a CAPTCHA appears, complete it in the browser first."
        )
        raw_jobs = scraper.extract_jobs_from_pages(
            listing_url, pages=pages_to_scan
        )
        if not raw_jobs:
            console.print("[bold red]No TopDev job links were found on the rendered page.[/bold red]")
            return

        console.print(
            f"[green]Collected {len(raw_jobs)} unique jobs from {pages_to_scan} pages "
            f"(TopDev API reports {getattr(scraper, 'api_total', '?')} matching jobs in total).[/green]"
        )

        verified_jobs = scraper.verify_jobs(raw_jobs)
        os.makedirs("reports", exist_ok=True)
        output_path = os.path.join(
            "reports", f"topdev_jobs_verified_{time.strftime('%Y-%m-%d')}.xlsx"
        )
        safe_save_excel(pd.DataFrame(verified_jobs), output_path)

        active_jobs = [job for job in verified_jobs if job["candidate_rule"] == "eligible"]
        table = Table(title="Verified TopDev jobs eligible for review")
        table.add_column("Title", style="cyan")
        table.add_column("Days left", justify="right")
        table.add_column("Link", style="green")
        for job in active_jobs[:20]:
            table.add_row(job["title"], str(job["days_left"] or "?"), job["link"])
        console.print(table)
        console.print(
            f"[green]Verified {len(verified_jobs)} jobs; {len(active_jobs)} are active and within the <=2-year rule. Saved: {output_path}[/green]"
        )
    finally:
        scraper.close_browser()

def main():
    print_banner()
    
    # Bước 1: Chọn chức năng
    console.print("[bold]Chọn chức năng:[/bold]")
    console.print("1. Cào danh sách công ty trên ITviec")
    console.print("2. Cào danh sách công ty trên TopCV.vn")
    console.print("3. Quét website công ty & Lọc job phù hợp với CV")
    console.print("4. Hỗ trợ ứng tuyển bán tự động (Apply Assistant)")
    console.print("5. Quét TopDev/Saramin và kiểm tra hạn từng JD")
    console.print("6. Xuất & Cập nhật Web HTML Dashboard (Hỗ trợ Tiếng Việt & Tiếng Anh)")
    choice = Prompt.ask("Nhập lựa chọn (1, 2, 3, 4, 5 hoặc 6)", choices=["1", "2", "3", "4", "5", "6"], default="3")
    
    if choice == "3":
        run_job_matching()
        return
    elif choice == "4":
        run_apply_assistant()
        return
    elif choice == "5":
        run_topdev_job_scan()
        return
    elif choice == "6":
        from generate_dashboard import generate_html_dashboard
        generate_html_dashboard()
        return
        
    # Các chức năng 1 và 2 (Cào danh sách)
    if choice == "1":
        default_url = "https://itviec.com/viec-lam-it/ha-noi?job_selected=chuyen-vien-data-engineer-python-sql-global-glory-5405&page=9"
        start_url = Prompt.ask("[bold]Nhập URL bắt đầu từ ITviec[/bold]", default=default_url)
        scraper = ITViecScraper()
        url_key = "itviec_url"
    else:
        default_url = "https://www.topcv.vn/tim-viec-lam-cong-nghe-thong-tin-tai-nam-tu-liem-l1d131cr257?exp=2,3,4&position=1&type_keyword=1&sba=1&category_family=r257&locations=l1d131,107,110&saturday_status=0"
        start_url = Prompt.ask("[bold]Nhập URL bắt đầu từ TopCV[/bold]", default=default_url)
        scraper = TopCVScraper()
        url_key = "topcv_url"
        
    max_pages = Prompt.ask("[bold]Nhập số lượng trang cần quét[/bold]", default="1")
    try:
        max_pages = int(max_pages)
    except ValueError:
        max_pages = 1
        console.print("[yellow]Số trang không hợp lệ, mặc định quét 1 trang.[/yellow]")
        
    output_file = Prompt.ask("[bold]Nhập tên file kết quả (xlsx hoặc csv)[/bold]", default="reports/companies_list.xlsx")
    if not output_file.endswith(('.xlsx', '.csv')):
        output_file += ".xlsx"

    try:
        scraper.start_browser()
        
        console.print("\n[yellow]Đang mở trang web đầu tiên...[/yellow]")
        scraper.page.goto(start_url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)
        
        scraper.wait_for_user("Vui lòng vượt qua Cloudflare/CAPTCHA (nếu có) trên trình duyệt, đảm bảo trang đã hiển thị danh sách việc làm ổn định, sau đó nhấn Enter tại đây...")

        all_companies = []
        current_url = start_url
        
        console.print("\n[bold green]=== BƯỚC 1: THU THẬP DANH SÁCH CÔNG TY ===[/bold green]")
        
        for p in range(1, max_pages + 1):
            console.print(f"\n[bold]Đang quét trang {p}/{max_pages}...[/bold]")
            
            companies_on_page = scraper.extract_companies_from_list(current_url)
            
            existing_urls = [c[url_key] for c in all_companies]
            added_count = 0
            for comp in companies_on_page:
                if comp[url_key] not in existing_urls:
                    all_companies.append(comp)
                    existing_urls.append(comp[url_key])
                    added_count += 1
            
            console.print(f"[green]Đã thêm {added_count} công ty mới từ trang {p}. Tổng số công ty hiện tại: {len(all_companies)}[/green]")
            
            if p < max_pages:
                if choice == "1":
                    next_url = scraper.get_next_page_url(current_url)
                else:
                    next_url = get_topcv_page_url(start_url, p + 1)
                
                console.print(f"[blue]Chuyển hướng đến trang tiếp theo: {next_url}[/blue]")
                current_url = next_url
                time.sleep(3)
        
        if not all_companies:
            console.print("[bold red]❌ Không tìm thấy công ty nào để cào website. Vui lòng kiểm tra lại URL hoặc bộ chọn CSS.[/bold red]")
            return

        console.print("\n[bold green]=== BƯỚC 2: CÀO WEBSITE CHÍNH THỨC CỦA CÁC CÔNG TY ===[/bold green]")
        console.print(f"Tổng số công ty cần quét website: {len(all_companies)}")
        
        final_results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("[cyan]Đang cào website...", total=len(all_companies))
            
            for index, comp in enumerate(all_companies):
                comp_name = comp["name"]
                comp_url = comp[url_key]
                
                progress.update(task, description=f"[cyan]Đang quét: {comp_name[:30]}...[/cyan]")
                
                potential_websites = scraper.scrape_company_website(comp_url)
                
                final_results.append({
                    "name": comp_name,
                    url_key: comp_url,
                    "potential_websites": potential_websites
                })
                
                progress.advance(task)
                
                if (index + 1) % 5 == 0:
                    temp_output = f"temp_{output_file}"
                    temp_data = []
                    for res in final_results:
                        best = res["potential_websites"][0] if res["potential_websites"] else "N/A"
                        temp_data.append({
                            "name": res["name"],
                            url_key: res[url_key],
                            "website": best
                        })
                    save_data(temp_data, temp_output, choice)
                
                time.sleep(2.5)

        domain_counts = {}
        for res in final_results:
            seen_domains = set()
            for url in res["potential_websites"]:
                try:
                    domain = urlparse(url).netloc.lower()
                    if domain:
                        seen_domains.add(domain)
                except Exception:
                    continue
            for domain in seen_domains:
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        system_domains = {dom for dom, count in domain_counts.items() if count >= 3}
        if system_domains:
            console.print(f"\n[yellow]⚠️  Phát hiện {len(system_domains)} domain hệ thống dùng chung và tự động loại bỏ: {system_domains}[/yellow]")

        final_clean_data = []
        for res in final_results:
            valid_urls = []
            for url in res["potential_websites"]:
                try:
                    domain = urlparse(url).netloc.lower()
                    if domain not in system_domains:
                        valid_urls.append(url)
                except Exception:
                    continue
            
            if valid_urls:
                valid_urls.sort(key=len)
                best_website = valid_urls[0]
            else:
                best_website = "N/A"
                
            final_clean_data.append({
                "name": res["name"],
                url_key: res[url_key],
                "website": best_website
            })

        console.print("\n[bold green]=== HOÀN THÀNH QUÁ TRÌNH CÀO DỮ LIỆU ===[/bold green]")
        save_data(final_clean_data, output_file, choice)
        final_results = final_clean_data
        
        temp_output = f"temp_{output_file}"
        if os.path.exists(temp_output):
            try:
                os.remove(temp_output)
            except Exception:
                pass
                
        table = Table(title="Danh sách Công ty & Website")
        table.add_column("Tên Công Ty", style="cyan", no_wrap=True)
        table.add_column("Website", style="green")
        
        for item in final_results[:15]:
            table.add_row(item["name"], item["website"])
            
        console.print(table)
        if len(final_results) > 15:
            console.print(f"...và {len(final_results) - 15} công ty khác đã được ghi vào file {output_file}.")

    except Exception as e:
        console.print(f"[bold red]Đã xảy ra lỗi hệ thống: {e}[/bold red]")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close_browser()

if __name__ == "__main__":
    main()
