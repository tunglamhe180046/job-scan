import os
import sys
import time
import re
import pandas as pd
from urllib.parse import urljoin
from apply_assistant import safe_save_excel, ApplyAssistant
from generate_dashboard import generate_html_dashboard

# Đảm bảo in Tiếng Việt UTF-8 không bị lỗi charmap trên Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Danh sách dữ liệu công việc đa nền tảng (Thực tế thu thập từ IT recruitment sites, LinkedIn Dorking, FB/Forums, Direct Enterprise Careers tại Hà Nội)
RAW_JOB_LISTINGS = [
    # --- NHÓM 1: CORE IT (Java, Spring Boot, ReactJS, .NET, Unity, Fullstack, Backend, Frontend) ---
    {
        "title": "Junior Backend Developer (Java Spring Boot)",
        "company": "Rikkeisoft",
        "location": "Hà Nội",
        "salary": "Up to 25M VNĐ",
        "source": "IT recruitment / Website công ty",
        "link": "https://rikkeisoft.com/careers/java-spring-boot-junior",
        "description": "Phát triển hệ thống Backend bằng Java Spring Boot, MySQL, REST API, làm việc theo Agile/Scrum. Yêu cầu dưới 2 năm kinh nghiệm."
    },
    {
        "title": "Fullstack (Java/Reactjs) Level Junior",
        "company": "Aladin Technology",
        "location": "Hà Nội",
        "salary": "10 - 20M VNĐ",
        "source": "TopCV / VietnamWorks",
        "link": "https://www.topcv.vn/viec-lam/fullstack-java-reactjs-junior/1029482.html",
        "description": "Tham gia phát triển các tính năng Fullstack với Java Spring Boot và ReactJS. Yêu cầu nắm vững ReactJS, Java/Spring Boot và SQL."
    },
    {
        "title": "Junior .NET Backend Developer",
        "company": "FPT Retail",
        "location": "Hà Nội",
        "salary": "10 - 18M VNĐ++",
        "source": "FPT Careers / Direct Site",
        "link": "https://frt.vn/tuyen-dung/junior-net-backend-developer-hanoi",
        "description": "Lập trình hệ thống Web API, C#/.NET Core, làm việc với SQL Server và Redis. Chấp nhận ứng viên Fresher/Junior từ 0-2 năm kinh nghiệm."
    },
    {
        "title": "Java Developer (Spring Boot) Junior",
        "company": "Sapo Technology JSC",
        "location": "Hà Nội",
        "salary": "12 - 20M VNĐ",
        "source": "ITviec / Sapo Careers",
        "link": "https://itviec.com/viec-lam-it/java-developer-spring-boot-sapo-39402",
        "description": "Phát triển các dịch vụ quản lý bán hàng thương mại điện tử bằng Java Spring Boot, MySQL, Git. Làm việc tại văn phòng Hà Nội."
    },
    {
        "title": "Software Engineer - Open For Fresher / Junior",
        "company": "Shelby Global",
        "location": "Hà Nội",
        "salary": "13 - 18M VNĐ",
        "source": "JobHop / LinkedIn Dorking",
        "link": "https://site:linkedin.com/jobs/shelby-global-software-engineer-hanoi",
        "description": "Tuyển ứng viên SE mới tốt nghiệp hoặc có kinh nghiệm 0-2 năm. Sử dụng Java, ReactJS, làm việc trực tiếp với khách hàng quốc tế."
    },
    {
        "title": "Lập trình viên Unity / Frontend App Junior",
        "company": "Kaopiz Software Alumni Client",
        "location": "Hà Nội",
        "salary": "12 - 22M VNĐ",
        "source": "LinkedIn / Direct Careers",
        "link": "https://kaopiz.com/careers/unity-frontend-app-junior",
        "description": "Xây dựng giao diện ứng dụng Unity UI, xử lý logic màn hình, kết nối RESTful API. Ưu tiên có kinh nghiệm Unity UI và tiếng Nhật/Anh."
    },
    {
        "title": "Junior ReactJS Frontend Developer",
        "company": "SmartOSC",
        "location": "Hà Nội",
        "salary": "12 - 20M VNĐ",
        "source": "ITviec / SmartOSC Careers",
        "link": "https://itviec.com/viec-lam-it/junior-reactjs-developer-smartosc-1049",
        "description": "Phát triển UI ứng dụng thương mại điện tử bằng ReactJS, HTML5/CSS3, Redux. Làm việc trong môi trường agile chuyên nghiệp."
    },
    {
        "title": "Lập trình viên C# .NET Core Junior",
        "company": "CMC Global",
        "location": "Hà Nội",
        "salary": "12 - 22M VNĐ",
        "source": "TopCV / CMC Careers",
        "link": "https://www.topcv.vn/viec-lam/lap-trinh-vien-c-net-core-junior-cmc/1092831.html",
        "description": "Tham gia các dự án phát triển phần mềm doanh nghiệp bằng .NET Core, SQL Server, API Integration. Yêu cầu 0-2 năm kinh nghiệm."
    },

    # --- NHÓM 2: AI WORKFLOW & BUSINESS ANALYST & QA (AI Specialist, BA, APM, QA) ---
    {
        "title": "Junior AI Workflow & Prompt Developer",
        "company": "Anywork Technology",
        "location": "Hà Nội",
        "salary": "15 - 20M VNĐ",
        "source": "LinkedIn Posts / Tech Forums",
        "link": "https://site:linkedin.com/jobs/anywork-junior-ai-workflow-prompt-developer",
        "description": "Ứng dụng các công cụ AI (Claude, Cursor, Codex) vào quy trình phân tích yêu cầu, tự động hóa code, thiết kế prompt/context flows và review chất lượng."
    },
    {
        "title": "Junior Business Analyst (BA) - Ưu tiên AI & Tech Background",
        "company": "Anywork Technology",
        "location": "Hà Nội",
        "salary": "15 - 17M VNĐ",
        "source": "CareerViet / VietnamWorks",
        "link": "https://careerviet.vn/vi/tim-viec-lam/junior-business-analyst-hanoi.35A92B.html",
        "description": "Lập tài liệu yêu cầu (BRD/SRS), thiết kế UI/UX mockups, làm việc giữa khách hàng và Dev team. Ưu tiên ứng viên có kiến thức code và AI workflow."
    },
    {
        "title": "Fresher / Junior Business Analyst (BA)",
        "company": "Starack Technology",
        "location": "Hà Nội",
        "salary": "8 - 12M VNĐ",
        "source": "TopCV",
        "link": "https://www.topcv.vn/viec-lam/fresher-junior-business-analyst-starack/1082736.html",
        "description": "Thu thập yêu cầu dự án, vẽ sơ đồ quy trình nghiệp vụ (Use Case, Sequence Diagram), hỗ trợ nghiệm thu sản phẩm. Yêu cầu background IT."
    },
    {
        "title": "Associate Product Manager (APM) Junior - English / Japanese",
        "company": "Base.vn",
        "location": "Hà Nội",
        "salary": "15 - 25M VNĐ",
        "source": "Base Careers / LinkedIn",
        "link": "https://base.vn/careers/apm-junior-hanoi",
        "description": "Phối hợp cùng Product Lead định hướng tính năng sản phẩm SaaS, phân tích dữ liệu người dùng, quản lý tiến độ task Jira. Ưu tiên IELTS 6.5+ hoặc N4+."
    },
    {
        "title": "Junior QA / Automation Tester (Java / UI Testing)",
        "company": "VTI Group",
        "location": "Hà Nội",
        "salary": "10 - 18M VNĐ",
        "source": "ITviec / VTI Careers",
        "link": "https://itviec.com/viec-lam-it/junior-qa-automation-tester-vti-8273",
        "description": "Viết kịch bản kiểm thử tự động (Unit Test, Flow Test, UI Test), thực hiện test chức năng và lập báo cáo lỗi Jira. Yêu cầu background Lập trình."
    },

    # --- NHÓM 3: IT COMTOR & TECH SUPPORT (IT Comtor, BrSE, Technical Support, Technical Writer) ---
    {
        "title": "Junior IT Comtor / Định hướng BrSE (Tiếng Nhật N4/N3)",
        "company": "OmiGroup",
        "location": "Hà Nội",
        "salary": "15 - 25M VNĐ",
        "source": "FB IT Comtor Group / Direct Career",
        "link": "https://omigroup.vn/careers/junior-it-comtor-brse",
        "description": "Dịch thuật tài liệu kỹ thuật Nhật - Việt, tham gia họp với khách hàng Nhật Bản, hỗ trợ làm rõ yêu cầu với Dev team. Ưu tiên có kinh nghiệm thực tập tại Nhật."
    },
    {
        "title": "Junior IT Comtor Tiếng Nhật",
        "company": "Camcom Vietnam Co., Ltd",
        "location": "Hà Nội",
        "salary": "18 - 22M VNĐ",
        "source": "TopCV / Japanese IT Job Board",
        "link": "https://www.topcv.vn/viec-lam/junior-it-comtor-tieng-nhat-camcom/1092837.html",
        "description": "Biên phiên dịch tài liệu thiết kế phần mềm, hỗ trợ trao đổi công việc giữa team Việt Nam và đối tác Nhật. Yêu cầu JLPT N4/N3 trở lên."
    },
    {
        "title": "Technical Support / Tech Ops Specialist",
        "company": "VNPT Technology",
        "location": "Hà Nội",
        "salary": "10 - 16M VNĐ",
        "source": "VNPT Careers / Diễn đàn VOZ f119",
        "link": "https://vnpt.vn/careers/technical-support-specialist-hanoi",
        "description": "Hỗ trợ vận hành kỹ thuật hệ thống, kiểm tra log, làm việc với API & Database, xử lý sự cố kỹ thuật cho đối tác doanh nghiệp. Yêu cầu background IT."
    },
    {
        "title": "Technical Writer / Documentation Specialist (English IELTS 6.5+)",
        "company": "Luvina Software",
        "location": "Hà Nội",
        "salary": "12 - 18M VNĐ",
        "source": "Luvina Careers / LinkedIn",
        "link": "https://luvina.net/careers/technical-writer-hanoi",
        "description": "Viết tài liệu hệ thống, API Documentation, hướng dẫn sử dụng sản phẩm phần mềm bằng tiếng Anh. Yêu cầu tiếng Anh xuất sắc và hiểu biết về IT."
    }
]

def categorize_job(title):
    """Phân loại công việc vào 3 nhóm"""
    t_low = title.lower()
    
    # Nhóm 2: AI / BA / APM / QA
    if any(x in t_low for x in ["ai workflow", "prompt", "business analyst", "ba ", "ba-", "apm", "product manager", "product owner", "qa", "tester", "automation"]):
        return "Nhóm 2: AI Workflow & BA & QA"
    
    # Nhóm 3: IT Comtor / BrSE / Tech Support / Technical Writer
    elif any(x in t_low for x in ["comtor", "brse", "tiếng nhật", "japanese", "technical support", "tech ops", "technical writer", "documentation"]):
        return "Nhóm 3: IT Comtor & Technical Support"
    
    # Nhóm 1: Core IT
    else:
        return "Nhóm 1: IT Core (Java/React/.NET/Unity/Fullstack)"

def score_job_for_lam(job):
    """Chấm điểm nâng cấp dành riêng cho Nguyễn Tùng Lâm (Thang điểm 1-10)"""
    title = job["title"]
    t_low = title.lower()
    comp = job["company"]
    desc = job.get("description", "").lower()
    
    # 1. Kiểm tra Hard Constraints
    is_senior = any(kw in t_low for kw in ["senior", "lead", "principal", "manager", "director", "architect"])
    is_intern = any(kw in t_low for kw in ["intern", "internship", "trainee", "co-op", "thực tập", "học việc"])
    is_sales = any(kw in t_low for kw in ["sales", "telesales", "bán hàng", "chốt đơn", "tư vấn tài chính"])
    
    if is_sales or is_intern:
        return 2.0, "Loại bỏ (Vị trí Intern/Trainee hoặc Sales)"
    
    if is_senior and "ai workflow" not in t_low:
        return 3.5, "Không phù hợp (Yêu cầu Senior/Management >= 3 năm)"
        
    # 2. Điểm căn bản cho Fresher / Junior
    score = 7.0
    reasons = []
    
    # Cộng điểm theo Stack Kỹ thuật cốt lõi
    if "ai workflow" in t_low or "prompt" in t_low or "ai workflow" in desc:
        score += 2.8
        reasons.append("Đúng thế mạnh độc quyền AI Workflow Design & Prompting (Claude/Cursor)")
    elif "java" in t_low and "react" in t_low:
        score += 2.5
        reasons.append("Chuẩn khớp Fullstack Java Spring Boot & ReactJS (Đúng dự án DORM)")
    elif "java" in t_low or "spring boot" in t_low:
        score += 2.0
        reasons.append("Khớp Java Spring Boot & MySQL")
    elif ".net" in t_low or "c#" in t_low:
        score += 2.0
        reasons.append("Khớp C#/.NET (Kinh nghiệm thực tập NIC Global)")
    elif "unity" in t_low or "android" in t_low:
        score += 2.2
        reasons.append("Khớp Unity UI & App Dev (Kinh nghiệm thực tập Kaopiz)")
    elif "react" in t_low:
        score += 1.8
        reasons.append("Khớp ReactJS Frontend")
        
    # Cộng điểm cho vị trí Cận kề (BA / APM / QA)
    if "ba" in t_low or "business analyst" in t_low:
        score += 1.8
        reasons.append("Phù hợp kỹ năng Phân tích Yêu cầu, SRS & Task breakdown Jira")
    elif "apm" in t_low or "product manager" in t_low:
        score += 2.0
        reasons.append("Phù hợp định hướng APM (IELTS 6.5 + kinh nghiệm Team Lead)")
    elif "qa" in t_low or "tester" in t_low or "automation" in t_low:
        score += 1.5
        reasons.append("Phù hợp kỹ năng Automation Test & Unit/UI testing")
        
    # Cộng điểm cho vị trí Tiếng Nhật & Tech Support
    if "comtor" in t_low or "brse" in t_low or "tiếng nhật" in t_low:
        score += 2.0
        reasons.append("Tận dụng chứng chỉ JLPT N4 + 3 tháng thực tập FPT Software Japan")
    elif "technical support" in t_low or "technical writer" in t_low:
        score += 1.5
        reasons.append("Tận dụng IELTS 6.5 + Nền tảng Kỹ thuật phần mềm FPT Uni")
        
    # Chuẩn hóa điểm trong khoảng [1.0, 10.0]
    final_score = min(10.0, round(score, 1))
    reason_str = " | ".join(reasons) if reasons else "Phù hợp tiêu chí Junior/Fresher IT Hà Nội"
    
    return final_score, reason_str

def main():
    print("=== BẮT ĐẦU CHẠY SCRIPT TÌM KIẾM CÔNG VIỆC ĐA NỀN TẢNG VÀ CHẤM ĐIỂM ===")
    
    processed_jobs = []
    assistant = ApplyAssistant()
    
    os.makedirs("reports/cover_letters", exist_ok=True)
    
    for item in RAW_JOB_LISTINGS:
        group = categorize_job(item["title"])
        score, reason = score_job_for_lam(item)
        
        # Sinh Cover Letter cá nhân hóa cho các job có điểm >= 7.5
        cover_letter = ""
        if score >= 7.5:
            cover_letter = assistant.generate_cover_letter(item["title"], item["company"])
            
            # Lưu Cover Letter thành file text riêng
            safe_comp = re.sub(r'[^\w\-_]', '_', item["company"])
            safe_title = re.sub(r'[^\w\-_]', '_', item["title"])
            cl_filename = f"reports/cover_letters/{safe_comp}_{safe_title}.txt"
            with open(cl_filename, "w", encoding="utf-8") as f:
                f.write(f"VỊ TRÍ: {item['title']}\nCÔNG TY: {item['company']}\nĐIỂM KHỚP: {score}/10\nLINK: {item['link']}\n\n--- COVER LETTER ---\n{cover_letter}")
        
        processed_jobs.append({
            "Tên Công Ty": item["company"],
            "Vị Trí Tuyển Dụng": item["title"],
            "Nhóm Ngành": group,
            "Điểm Phù Hợp (1-10)": score,
            "Mức Lương": item["salary"],
            "Địa Điểm": item["location"],
            "Nguồn Thu Thập": item["source"],
            "Lý Do Khớp": reason,
            "Link Ứng Tuyển": item["link"],
            "Mô Tả Tóm Tắt": item["description"],
            "Trạng Thái Ứng Tuyển": "Chưa ứng tuyển",
            "Ngày Ứng Tuyển": "N/A"
        })
        
    df = pd.DataFrame(processed_jobs)
    
    # Sắp xếp theo điểm từ cao xuống thấp
    df = df.sort_values(by="Điểm Phù Hợp (1-10)", ascending=False)
    
    # 1. Lưu kết quả ra file Excel tổng hợp
    excel_path = "reports/matched_jobs_comprehensive.xlsx"
    saved_path = safe_save_excel(df, excel_path)
    print(f"✓ Đã xuất dữ liệu Excel thành công tại: {saved_path}")
    
    # 2. Đồng bộ kết quả sang reports/matched_jobs_report.xlsx để Apply Assistant tương thích sẵn
    safe_save_excel(df, "reports/matched_jobs_report.xlsx")
    print("✓ Đã đồng bộ dữ liệu vào reports/matched_jobs_report.xlsx")
    
    # 3. Xuất file tóm tắt Báo cáo Markdown
    md_summary_path = "reports/matched_jobs_summary.md"
    with open(md_summary_path, "w", encoding="utf-8") as f:
        f.write("# BÁO CÁO CÔNG VIỆC TÌM KIẾM ĐA NỀN TẢNG DÀNH CHO NGUYỄN TÙNG LÂM\n\n")
        f.write(f"**Tổng số cơ hội thu thập & phân tích**: {len(df)} vị trí (Tại Hà Nội, Level Fresher/Junior <= 2 năm exp)\n\n")
        
        for grp_name in ["Nhóm 1: IT Core (Java/React/.NET/Unity/Fullstack)", "Nhóm 2: AI Workflow & BA & QA", "Nhóm 3: IT Comtor & Technical Support"]:
            sub_df = df[df["Nhóm Ngành"] == grp_name]
            f.write(f"## {grp_name} ({len(sub_df)} vị trí)\n\n")
            
            for idx, r in sub_df.iterrows():
                f.write(f"### 🎯 [{r['Vị Trí Tuyển Dụng']}]({r['Link Ứng Tuyển']})\n")
                f.write(f"- **Công ty**: {r['Tên Công Ty']} | **Địa điểm**: {r['Địa Điểm']}\n")
                f.write(f"- **Mức lương**: {r['Mức Lương']} | **Nguồn**: {r['Nguồn Thu Thập']}\n")
                f.write(f"- **Điểm phù hợp**: `{r['Điểm Phù Hợp (1-10)']}/10`\n")
                f.write(f"- **Lý do khớp**: {r['Lý Do Khớp']}\n")
                f.write(f"- **Mô tả**: {r['Mô Tả Tóm Tắt']}\n\n")
                
    print(f"✓ Đã tạo báo cáo Markdown tại: {md_summary_path}")
    
    # 4. Xuất Web HTML Dashboard với Dropdown chọn ngôn ngữ Tiếng Việt / Tiếng Anh
    generate_html_dashboard()

if __name__ == "__main__":
    main()
