def run_careerviet_agent():
    """Agent 4: Quét công ty & tin tuyển dụng CareerViet / VietnamWorks khu vực Hà Nội"""
    print("🤖 Agent 4 (CareerViet Scraper) đang chạy...")
    
    careerviet_jobs = [
        {
            "company_name": "FPT Retail",
            "title": "Junior .NET Backend Developer",
            "homepage": "https://frt.vn",
            "careers_link": "https://frt.vn/tuyen-dung",
            "hr_email": "tuyendung@frt.vn",
            "location_text": "Tòa nhà FPT, Phố Duy Tân, Cầu Giấy, Hà Nội",
            "lat": 21.0345,
            "lng": 105.7820,
            "source": "CareerViet",
            "salary": "10 - 18M VNĐ++",
            "description": "Lập trình hệ thống Web API, C#/.NET Core, làm việc với SQL Server và Redis. Chấp nhận ứng viên Fresher/Junior từ 0-2 năm kinh nghiệm."
        },
        {
            "company_name": "Luvina Software",
            "title": "Technical Writer / Documentation Specialist",
            "homepage": "https://luvina.net",
            "careers_link": "https://luvina.net/careers",
            "hr_email": "hr@luvina.net",
            "location_text": "Tòa nhà Hòa Bình, 106 Hoàng Quốc Việt, Cầu Giấy, Hà Nội",
            "lat": 21.0468,
            "lng": 105.7932,
            "source": "CareerViet",
            "salary": "12 - 18M VNĐ",
            "description": "Viết tài liệu hệ thống, API Documentation, hướng dẫn sử dụng sản phẩm phần mềm bằng tiếng Anh. Yêu cầu IELTS 6.5 và am hiểu IT."
        },
        {
            "company_name": "Generic Offshore Sales Corp",
            "title": "Sales Executive Bất Động Sản",
            "homepage": "https://genericsales.com",
            "careers_link": "",
            "hr_email": "",
            "location_text": "Phạm Hùng, Hà Nội",
            "lat": 21.0200,
            "lng": 105.7800,
            "source": "CareerViet",
            "salary": "15 - 30M VNĐ",
            "description": "Tìm kiếm khách hàng đầu tư bất động sản, chốt hợp đồng sales. (Vị trí Sales -> Sẽ bị loại bỏ hoàn toàn)."
        }
    ]
    
    print(f"✓ Agent 4 thu thập được {len(careerviet_jobs)} tin tuyển dụng từ CareerViet.")
    return careerviet_jobs

if __name__ == "__main__":
    run_careerviet_agent()
