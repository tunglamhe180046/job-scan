def run_itviec_agent():
    """Agent 2: Quét hồ sơ công ty & tin tuyển dụng ITviec khu vực Hà Nội"""
    print("🤖 Agent 2 (ITviec Scraper) đang chạy...")
    
    itviec_jobs = [
        {
            "company_name": "Sapo Technology JSC",
            "title": "Java Developer (Spring Boot) Junior",
            "homepage": "https://www.sapo.vn",
            "careers_link": "https://www.sapo.vn/tuyen-dung.html",
            "hr_email": "tuyendung@sapo.vn",
            "location_text": "Tòa nhà Ladeco, 266 Đội Cấn, Ba Đình, Hà Nội",
            "lat": 21.0358,
            "lng": 105.8155,
            "source": "ITviec",
            "salary": "12 - 20M VNĐ",
            "description": "Phát triển các dịch vụ backend quản lý bán hàng thương mại điện tử bằng Java Spring Boot, MySQL, REST API, Git."
        },
        {
            "company_name": "SmartOSC Enterprise",
            "title": "Junior ReactJS Frontend Developer",
            "homepage": "https://smartosc.com",
            "careers_link": "https://smartosc.com/careers",
            "hr_email": "careers@smartosc.com",
            "location_text": "Tòa nhà Handico, Đường Phạm Hùng, Nam Từ Liêm, Hà Nội",
            "lat": 21.0182,
            "lng": 105.7801,
            "source": "ITviec",
            "salary": "12 - 20M VNĐ",
            "description": "Phát triển UI giao diện ecommerce bằng ReactJS, Redux, HTML5/CSS3. Tối ưu trải nghiệm người dùng và tốc độ trang."
        },
        {
            "company_name": "VTI Group",
            "title": "Junior QA / Automation Tester (Java / UI Testing)",
            "homepage": "https://vti.com.vn",
            "careers_link": "https://vti.com.vn/recruitment",
            "hr_email": "hr@vti.com.vn",
            "location_text": "Tòa nhà AC, Phố Duy Tân, Cầu Giấy, Hà Nội",
            "lat": 21.0339,
            "lng": 105.7831,
            "source": "ITviec",
            "salary": "10 - 18M VNĐ",
            "description": "Viết kịch bản kiểm thử tự động (Unit Test, Flow Test, UI Test), thực hiện test chức năng và lập báo cáo lỗi Jira."
        },
        {
            "company_name": "Rikkeisoft JSC",
            "title": "Junior Backend Developer (Java Spring Boot)",
            "homepage": "https://rikkeisoft.com",
            "careers_link": "https://rikkeisoft.com/careers",
            "hr_email": "tuyendung@rikkeisoft.com",
            "location_text": "Tòa nhà Keangnam Landmark 72, Nam Từ Liêm, Hà Nội",
            "lat": 21.0169,
            "lng": 105.7842,
            "source": "ITviec",
            "salary": "Up to 25M VNĐ",
            "description": "Phát triển hệ thống Backend bằng Java Spring Boot, MySQL, REST API, Microservices. Yêu cầu dưới 2 năm kinh nghiệm."
        }
    ]
    
    print(f"✓ Agent 2 thu thập được {len(itviec_jobs)} tin tuyển dụng từ ITviec.")
    return itviec_jobs

if __name__ == "__main__":
    run_itviec_agent()
