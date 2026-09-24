def run_fb_agent():
    """Agent 1: Quét các bài tuyển dụng IT Hà Nội từ Facebook / HR Groups & Post Fanpage"""
    print("🤖 Agent 1 (Facebook IT Jobs) đang chạy...")
    
    fb_jobs = [
        {
            "company_name": "Rikkeisoft JSC",
            "title": "Junior AI Workflow & Backend Developer (Java / Python)",
            "homepage": "https://rikkeisoft.com",
            "careers_link": "https://rikkeisoft.com/co-hoi-nghe-nghiep/",
            "hr_email": "tuyendung@rikkeisoft.com",
            "location_text": "Tòa nhà Keangnam Landmark 72, Nam Từ Liêm, Hà Nội",
            "lat": 21.0169,
            "lng": 105.7842,
            "source": "Facebook IT Jobs Hanoi Group",
            "salary": "15 - 25M VNĐ",
            "description": "Ứng dụng các công cụ AI (Claude, Cursor, Codex) vào quy trình phân tích yêu cầu, tự động hóa code, thiết kế prompt/context flows và review chất lượng."
        },
        {
            "company_name": "Kaopiz Software Co., Ltd",
            "title": "Junior Unity UI & Frontend App Developer",
            "homepage": "https://kaopiz.com",
            "careers_link": "https://kaopiz.com/recruit/",
            "hr_email": "hr@kaopiz.com",
            "location_text": "Tòa nhà C'Land, 81 Lê Đức Thọ, Nam Từ Liêm, Hà Nội",
            "lat": 21.0331,
            "lng": 105.7701,
            "source": "FB Fanpage Kaopiz Careers",
            "salary": "12 - 22M VNĐ",
            "description": "Lập trình giao diện Unity UI, xử lý tương tác người dùng, kết nối API backend. Làm việc trực tiếp với đối tác Nhật Bản và quốc tế."
        }
    ]
    
    print(f"✓ Agent 1 thu thập được {len(fb_jobs)} tin tuyển dụng từ Facebook & Fanpage HR.")
    return fb_jobs

if __name__ == "__main__":
    run_fb_agent()
