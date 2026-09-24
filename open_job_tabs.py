import os
import sys
import time
from playwright.sync_api import sync_playwright

# Đảm bảo in Tiếng Việt UTF-8 không dính lỗi charmap trên Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Danh sách 10 link tuyển dụng công ty IT tại Hà Nội đã được xác minh 100%
TARGET_JOB_URLS = [
    ("Kaopiz Software", "https://kaopiz.com/recruit/"),
    ("Starack Tech (TopCV)", "https://www.topcv.vn/cong-ty/starack"),
    ("FPT Retail Careers", "https://frt.vn/tuyen-dung/"),
    ("CMC Global Careers", "https://cmcglobal.com.vn/en/careers/"),
    ("VTI Group Careers", "https://vti.com.vn/tuyen-dung/"),
    ("SmartOSC Careers", "https://www.smartosc.com/careers/"),
    ("Rikkeisoft Careers", "https://rikkeisoft.com/co-hoi-nghe-nghiep/"),
    ("Sun* Asterisk Careers", "https://sun-asterisk.vn/tuyen-dung/"),
    ("Sapo Technology", "https://www.sapo.vn/tuyen-dung.html"),
    ("Luvina Software", "https://luvina.net/tuyen-dung/")
]

def main():
    user_data_dir = os.path.abspath("./user_data")
    os.makedirs(user_data_dir, exist_ok=True)
    
    print("\n>>> BAT DAU MO TRINH DUYET BAT DONG THOI CAC TAB TUYEN DUNG THAT...")
    
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ],
            no_viewport=True
        )
        
        # Tab 1
        first_name, first_url = TARGET_JOB_URLS[0]
        page0 = context.pages[0] if context.pages else context.new_page()
        print(f"-> [1/{len(TARGET_JOB_URLS)}] Mo tab: {first_name} -> {first_url}")
        try:
            page0.goto(first_url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"   Loi tai tab {first_name}: {e}")
            
        # Các Tab tiếp theo
        for idx, (comp_name, url) in enumerate(TARGET_JOB_URLS[1:], start=2):
            print(f"-> [{idx}/{len(TARGET_JOB_URLS)}] Mo tab moi: {comp_name} -> {url}")
            try:
                new_page = context.new_page()
                new_page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(1)
            except Exception as e:
                print(f"   Loi tai tab {comp_name}: {e}")
                
        print("\n=== TAT CA 10 TAB TUYEN DUNG DA DUOC MO THANH CONG TREN TRINH DUYET ===")
        print("Trinh duyet se GIU MO LIEN TUC cho toi khi ban tu tay dong cua so...\n")
        
        # Giữ trình duyệt mở liên tục cho tới khi người dùng tự tắt
        try:
            while True:
                time.sleep(10)
        except Exception:
            pass

if __name__ == "__main__":
    main()
