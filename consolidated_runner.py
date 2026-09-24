import os
import sys
import math
import re
import pandas as pd
from apply_assistant import safe_save_excel

from scrapers.fb_agent import run_fb_agent
from scrapers.itviec_agent import run_itviec_agent
from scrapers.topcv_agent import run_topcv_agent
from scrapers.careerviet_agent import run_careerviet_agent
from scrapers.gmaps_agent import run_gmaps_agent, SUN_SQUARE_LAT, SUN_SQUARE_LNG, haversine_distance

# Đảm bảo in Tiếng Việt UTF-8 trên Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

def evaluate_cv_fit(title, company_name, description=""):
    """Đánh giá độ phù hợp của công việc với CV Nguyễn Tùng Lâm (1-10)"""
    t_low = title.lower()
    desc_low = description.lower()
    
    # 1. Loại bỏ các vị trí không phù hợp (Senior >=3 năm, Intern, Sales)
    is_senior = any(kw in t_low for kw in ["senior", "lead", "principal", "manager", "director", "architect"])
    is_intern = any(kw in t_low for kw in ["intern", "internship", "trainee", "co-op", "thực tập", "học việc"])
    is_sales = any(kw in t_low for kw in ["sales", "telesales", "bán hàng", "chốt đơn", "bất động sản"])
    
    if is_sales or is_intern:
        return 2.0, "REJECT", "Loại bỏ (Vị trí Intern/Trainee hoặc Sales)"
        
    if is_senior and "ai workflow" not in t_low:
        return 3.5, "REJECT", "Loại bỏ (Yêu cầu Senior/Management >= 3 năm)"
        
    score = 7.0
    reasons = []
    
    # Cộng điểm theo stack kỹ thuật & thế mạnh CV
    if "ai workflow" in t_low or "prompt" in t_low or "ai" in desc_low:
        score += 2.8
        reasons.append("Thế mạnh độc quyền AI Workflow Design & Prompting")
    elif "java" in t_low and "react" in t_low:
        score += 2.5
        reasons.append("Khớp Fullstack Java Spring Boot & ReactJS (Đúng dự án DORM)")
    elif "java" in t_low or "spring boot" in t_low:
        score += 2.0
        reasons.append("Khớp Java Spring Boot & MySQL")
    elif ".net" in t_low or "c#" in t_low:
        score += 2.0
        reasons.append("Khớp C#/.NET (Kinh nghiệm thực tập NIC Global)")
    elif "unity" in t_low or "mobile" in t_low:
        score += 2.2
        reasons.append("Khớp Unity UI & App Dev (Kinh nghiệm Kaopiz)")
    elif "react" in t_low:
        score += 1.8
        reasons.append("Khớp ReactJS Frontend")
        
    if "ba" in t_low or "business analyst" in t_low:
        score += 1.8
        reasons.append("Phù hợp Phân tích Yêu cầu, SRS/BRD & Jira")
    elif "qa" in t_low or "tester" in t_low or "automation" in t_low:
        score += 1.5
        reasons.append("Phù hợp kỹ năng Automation Test & Unit/UI testing")
    elif "comtor" in t_low or "brse" in t_low or "tiếng nhật" in t_low:
        score += 2.0
        reasons.append("Tận dụng JLPT N4 + 3 tháng thực tập Nhật")
    elif "technical support" in t_low or "technical writer" in t_low:
        score += 1.5
        reasons.append("Tận dụng IELTS 6.5 + Bằng SE FPT University")
        
    final_score = min(10.0, round(score, 1))
    reason_str = " | ".join(reasons) if reasons else "Phù hợp tiêu chí Fresher/Junior IT Hà Nội"
    
    return final_score, "ACCEPT", reason_str

def main():
    print("==============================================================")
    print("🚀 BẮT ĐẦU CHẠY PIPELINE TỔNG HỢP CÔNG VIỆC ĐA AGENT QUÉT THEO KHOẢNG CÁCH")
    print(f"📍 Tọa độ anchor (Sun Square, Nam Từ Liêm): ({SUN_SQUARE_LAT}, {SUN_SQUARE_LNG})")
    print("==============================================================\n")
    
    # 1. Thu thập dữ liệu từ 5 Agents
    raw_list = []
    raw_list.extend(run_fb_agent())
    raw_list.extend(run_itviec_agent())
    raw_list.extend(run_topcv_agent())
    raw_list.extend(run_careerviet_agent())
    raw_list.extend(run_gmaps_agent())
    
    print(f"\n📊 Tổng số tin thu thập thô từ 5 Agent: {len(raw_list)}")
    
    # 2. Khử trùng lặp theo (company_name + title)
    unique_map = {}
    for item in raw_list:
        key = f"{item['company_name'].lower().strip()}_{item['title'].lower().strip()}"
        if key not in unique_map:
            unique_map[key] = item
            
    unique_jobs = list(unique_map.values())
    print(f"✓ Sau khi loại trùng lặp: còn {len(unique_jobs)} vị trí.")
    
    # 3. Lọc khắt khe & Chấm điểm CV & Tính khoảng cách
    final_rows = []
    rejected_count = 0
    
    for job in unique_jobs:
        comp = job["company_name"]
        title = job["title"]
        homepage = job.get("homepage", "").strip()
        careers = job.get("careers_link", "").strip()
        email = job.get("hr_email", "").strip()
        
        # Tính khoảng cách GPS
        lat = job.get("lat", SUN_SQUARE_LAT)
        lng = job.get("lng", SUN_SQUARE_LNG)
        dist_km = haversine_distance(SUN_SQUARE_LAT, SUN_SQUARE_LNG, lat, lng)
        
        # Đánh giá CV fit
        score, status, reason = evaluate_cv_fit(title, comp, job.get("description", ""))
        
        if status == "REJECT":
            rejected_count += 1
            continue
            
        # Quy tắc Lọc Link Careers / Email HR
        has_direct_contact = bool(careers or email)
        category_label = ""
        
        if has_direct_contact:
            category_label = "✅ Ứng tuyển Trực tiếp (Có Careers/Email)"
        else:
            # Không có Careers link & không có Email HR
            if score >= 7.5:
                category_label = "⭐ MỤC RIÊNG LƯU Ý (Phù hợp CV cao, Nộp qua Sàn)"
            else:
                # Thiếu liên hệ VÀ điểm < 7.5 -> LOẠI BỎ
                rejected_count += 1
                continue
                
        final_rows.append({
            "Khoảng Cách (km)": dist_km,
            "Tên Công Ty": comp,
            "Vị Trí Tuyển Dụng": title,
            "Phân Loại Ứng Tuyển": category_label,
            "Điểm CV (1-10)": score,
            "Mức Lương": job.get("salary", "Thỏa thuận"),
            "Link Trang Chủ": homepage if homepage else "N/A",
            "Link Tuyển Dụng (Careers)": careers if careers else "N/A",
            "Email HR Tuyển Dụng": email if email else "N/A",
            "Địa Chỉ Công Ty": job.get("location_text", "Hà Nội"),
            "Nguồn Dữ Liệu": job.get("source", "N/A"),
            "Lý Do Khớp CV": reason,
            "Mô Tả Công Việc": job.get("description", "")
        })
        
    df = pd.DataFrame(final_rows)
    
    # 4. Sắp xếp theo Khoảng cách từ Gần tới Xa (Khoảng Cách (km) tăng dần)
    df = df.sort_values(by="Khoảng Cách (km)", ascending=True)
    
    # 5. Xuất 1 file Excel duy nhất bằng safe_save_excel
    os.makedirs("reports", exist_ok=True)
    excel_path = "reports/consolidated_jobs_by_distance.xlsx"
    saved_excel = safe_save_excel(df, excel_path)
    
    # Đồng bộ cả sang reports/matched_jobs_report.xlsx để tương thích Apply Assistant
    safe_save_excel(df, "reports/matched_jobs_report.xlsx")
    
    # 6. Xuất Báo cáo Markdown Tóm tắt
    md_path = "reports/consolidated_jobs_summary.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# BÁO CÁO TỔNG HỢP CÔNG VIỆC TỪ 5 AGENTS (SẮP XẾP THEO KHOẢNG CÁCH GẦN -> XA)\n\n")
        f.write(f"📍 **Vị trí gốc của bạn**: Tòa nhà Sun Square (Lê Đức Thọ, Nam Từ Liêm, Hà Nội)\n")
        f.write(f"📊 **Tổng số cơ hội vượt qua bộ lọc khắt khe**: {len(df)} vị trí (Đã loại {rejected_count} vị trí không phù hợp / thiếu liên hệ)\n\n")
        f.write("---\n\n")
        
        for idx, r in df.iterrows():
            f.write(f"### 🎯 [{idx+1}] {r['Vị Trí Tuyển Dụng']} - **{r['Tên Công Ty']}**\n")
            f.write(f"- 🚗 **Khoảng cách**: `{r['Khoảng Cách (km)']} km` từ nhà bạn\n")
            f.write(f"- 🏷️ **Phân loại**: `{r['Phân Loại Ứng Tuyển']}` | **Điểm CV**: `{r['Điểm CV (1-10)']}/10`\n")
            f.write(f"- 🌐 **Trang chủ**: {r['Link Trang Chủ']}\n")
            f.write(f"- 📄 **Link Careers**: {r['Link Tuyển Dụng (Careers)']}\n")
            f.write(f"- ✉️ **Email HR**: `{r['Email HR Tuyển Dụng']}`\n")
            f.write(f"- 📍 **Địa chỉ**: {r['Địa Chỉ Công Ty']} | **Nguồn**: {r['Nguồn Dữ Liệu']}\n")
            f.write(f"- 💡 **Lý do khớp**: {r['Lý Do Khớp CV']}\n\n")
            
    print(f"\n✅ ĐÃ XUẤT THÀNH CÔNG 1 FILE EXCEL DUY NHẤT TẠI: {excel_path}")
    print(f"✅ ĐÃ XUẤT BÁO CÁO MARKDOWN TẠI: {md_path}")
    print(f"🎉 Tổng số công ty được lưu: {len(df)} (Sắp xếp từ gần nhất {df.iloc[0]['Khoảng Cách (km)']}km đến xa nhất {df.iloc[-1]['Khoảng Cách (km)']}km)")

if __name__ == "__main__":
    main()
