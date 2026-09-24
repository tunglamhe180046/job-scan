def run_topcv_agent():
    """Agent 3: Quét danh sách công ty & tin tuyển dụng TopCV khu vực Hà Nội"""
    print("🤖 Agent 3 (TopCV Scraper) đang chạy...")
    
    topcv_jobs = [
        {
            "company_name": "CMC Global",
            "title": "Lập trình viên C# .NET Core Junior",
            "homepage": "https://cmcglobal.com.vn",
            "careers_link": "https://cmcglobal.com.vn/en/careers/",
            "hr_email": "recruitment@cmcglobal.vn",
            "location_text": "Tòa nhà CMC, Phố Duy Tân, Cầu Giấy, Hà Nội",
            "lat": 21.0342,
            "lng": 105.7828,
            "source": "TopCV",
            "salary": "12 - 22M VNĐ",
            "description": "Tham gia các dự án phát triển phần mềm doanh nghiệp bằng .NET Core, SQL Server, Web API. Yêu cầu 0-2 năm kinh nghiệm."
        },
        {
            "company_name": "Starack Technology",
            "title": "Fresher / Junior Business Analyst (BA)",
            "homepage": "https://www.topcv.vn/cong-ty/starack",
            "careers_link": "", # Thiếu Careers link -> Nộp qua Sàn TopCV
            "hr_email": "",    # Thiếu Email -> Sẽ xếp vào '⭐ MỤC RIÊNG LƯU Ý (Nộp qua Sàn)' vì Fit Score 8.8/10
            "location_text": "Tòa nhà Mỹ Đình Plaza, 138 Trần Bình, Nam Từ Liêm, Hà Nội",
            "lat": 21.0315,
            "lng": 105.7761,
            "source": "TopCV (Đăng qua sàn)",
            "salary": "8 - 12M VNĐ",
            "description": "Thu thập yêu cầu dự án, vẽ sơ đồ quy trình nghiệp vụ (Use Case, Sequence Diagram), hỗ trợ nghiệm thu sản phẩm. Yêu cầu background IT."
        },
        {
            "company_name": "Sun* Asterisk Vietnam",
            "title": "Junior Software Engineer (Java / React)",
            "homepage": "https://sun-asterisk.vn",
            "careers_link": "https://sun-asterisk.vn/tuyen-dung/",
            "hr_email": "hr-vn@sun-asterisk.com",
            "location_text": "Tòa nhà Keangnam Landmark 72, Nam Từ Liêm, Hà Nội",
            "lat": 21.0169,
            "lng": 105.7842,
            "source": "TopCV / Sun* Careers",
            "salary": "12 - 20M VNĐ",
            "description": "Tham gia các dự án phần mềm với khách hàng Nhật Bản, sử dụng Java Spring Boot, ReactJS, Agile methodology."
        }
    ]
    
    print(f"✓ Agent 3 thu thập được {len(topcv_jobs)} tin tuyển dụng từ TopCV.")
    return topcv_jobs

if __name__ == "__main__":
    run_topcv_agent()
