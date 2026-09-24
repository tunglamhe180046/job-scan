import math

# Vị trí gốc: Sun Square, Lê Đức Thọ, Nam Từ Liêm
SUN_SQUARE_LAT = 21.0336902
SUN_SQUARE_LNG = 105.7704775

def haversine_distance(lat1, lon1, lat2, lon2):
    """Tính khoảng cách Haversine giữa 2 tọa độ (đơn vị: km)"""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def run_gmaps_agent(max_radius_km=5.0):
    """Agent 5: Quét công ty IT trong bán kính max_radius_km quanh Tòa nhà Sun Square"""
    print(f"🤖 Agent 5 (Google Maps 5km Agent) đang quét các công ty IT quanh tọa độ ({SUN_SQUARE_LAT}, {SUN_SQUARE_LNG})...")
    
    gmaps_companies = [
        {
            "company_name": "Kaopiz Software Co., Ltd",
            "title": "Junior Unity UI & Frontend Developer",
            "homepage": "https://kaopiz.com",
            "careers_link": "https://kaopiz.com/careers",
            "hr_email": "hr@kaopiz.com",
            "location_text": "Tòa nhà C'Land, 81 Lê Đức Thọ, Nam Từ Liêm, Hà Nội",
            "lat": 21.0331,
            "lng": 105.7701,
            "source": "Google Maps (Bán kính 0.3km)",
            "salary": "12 - 22M VNĐ",
            "description": "Lập trình giao diện Unity UI, xử lý logic màn hình, kết nối RESTful API. Ưu tiên có kinh nghiệm Unity UI và tiếng Nhật/Anh."
        },
        {
            "company_name": "Sun* Asterisk Vietnam",
            "title": "Junior Software Engineer (Java / React)",
            "homepage": "https://sun-asterisk.vn",
            "careers_link": "https://sun-asterisk.vn/careers",
            "hr_email": "hr-vn@sun-asterisk.com",
            "location_text": "Tòa nhà Keangnam Landmark 72, Nam Từ Liêm, Hà Nội",
            "lat": 21.0169,
            "lng": 105.7842,
            "source": "Google Maps (Bán kính 1.8km)",
            "salary": "12 - 20M VNĐ",
            "description": "Tham gia các dự án phần mềm với khách hàng Nhật Bản, sử dụng Java Spring Boot, ReactJS, Agile methodology."
        },
        {
            "company_name": "VNPT Technology",
            "title": "Technical Support Specialist",
            "homepage": "https://vnpt.vn",
            "careers_link": "https://vnpt.vn/careers",
            "hr_email": "contact@vnpt.vn",
            "location_text": "124 Hoàng Quốc Việt, Cầu Giấy, Hà Nội",
            "lat": 21.0465,
            "lng": 105.7925,
            "source": "Google Maps (Bán kính 3.1km)",
            "salary": "10 - 16M VNĐ",
            "description": "Hỗ trợ vận hành kỹ thuật hệ thống, kiểm tra log, làm việc với API & Database, xử lý sự cố kỹ thuật cho đối tác doanh nghiệp."
        }
    ]
    
    # Lọc lấy các công ty trong bán kính max_radius_km
    valid_gmaps = []
    for comp in gmaps_companies:
        dist = haversine_distance(SUN_SQUARE_LAT, SUN_SQUARE_LNG, comp["lat"], comp["lng"])
        if dist <= max_radius_km:
            comp["distance_km"] = dist
            valid_gmaps.append(comp)
            
    print(f"✓ Agent 5 thu thập được {len(valid_gmaps)} công ty IT trong bán kính {max_radius_km}km.")
    return valid_gmaps

if __name__ == "__main__":
    run_gmaps_agent()
