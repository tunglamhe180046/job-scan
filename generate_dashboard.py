import os
import sys
import json
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

def generate_html_dashboard(input_excel="reports/matched_jobs_comprehensive.xlsx", output_html="reports/job_dashboard.html"):
    """Tự động sinh file Web Dashboard HTML với Dropdown chuyển đổi Tiếng Việt / Tiếng Anh ở góc trên bên phải"""
    
    if not os.path.exists(input_excel):
        if os.path.exists("reports/matched_jobs_report.xlsx"):
            input_excel = "reports/matched_jobs_report.xlsx"
        else:
            print(f"❌ Không tìm thấy file dữ liệu: {input_excel}")
            return

    try:
        df = pd.read_excel(input_excel)
    except Exception as e:
        print(f"❌ Lỗi đọc file Excel {input_excel}: {e}")
        return

    # Chuyển đổi DataFrame thành JSON
    jobs_data = df.to_dict(orient="records")
    json_data_str = json.dumps(jobs_data, ensure_ascii=False, indent=2)

    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job-Scan AI Dashboard | Nguyễn Tùng Lâm</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {{
            --bg-body: #0f172a;
            --bg-card: #1e293b;
            --bg-card-hover: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --primary: #3b82f6;
            --primary-glow: rgba(59, 130, 246, 0.3);
            --accent: #10b981;
            --warning: #f59e0b;
            --border-color: #334155;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', sans-serif;
        }}

        body {{
            background-color: var(--bg-body);
            color: var(--text-primary);
            min-height: 100vh;
            padding-bottom: 3rem;
        }}

        /* Header Navbar */
        header {{
            background: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            z-index: 100;
            padding: 1rem 2rem;
        }}

        .nav-container {{
            max-width: 1300px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .brand {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--primary);
        }}

        .brand i {{
            font-size: 1.5rem;
        }}

        /* Dropdown chuyển đổi ngôn ngữ ở góc trên bên phải */
        .top-right-actions {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .lang-dropdown-wrapper {{
            position: relative;
        }}

        .lang-select {{
            appearance: none;
            -webkit-appearance: none;
            background-color: var(--bg-card);
            color: var(--text-primary);
            padding: 0.55rem 2.2rem 0.55rem 1rem;
            border-radius: 20px;
            border: 1px solid var(--primary);
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 0 10px var(--primary-glow);
            background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%233b82f6%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E");
            background-repeat: no-repeat;
            background-position: right 0.8rem center;
            background-size: 0.65rem auto;
        }}

        .lang-select:hover {{
            background-color: var(--bg-card-hover);
            box-shadow: 0 0 15px var(--primary-glow);
        }}

        .lang-select option {{
            background-color: var(--bg-card);
            color: var(--text-primary);
        }}

        /* Main Container */
        .container {{
            max-width: 1300px;
            margin: 2rem auto;
            padding: 0 1.5rem;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .stat-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            display: flex;
            align-items: center;
            gap: 1.25rem;
        }}

        .stat-icon {{
            width: 52px;
            height: 52px;
            border-radius: 12px;
            background: rgba(59, 130, 246, 0.15);
            color: var(--primary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }}

        .stat-val {{
            font-size: 1.75rem;
            font-weight: 800;
        }}

        .stat-label {{
            font-size: 0.875rem;
            color: var(--text-secondary);
        }}

        /* Controls / Filter */
        .filter-section {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            align-items: center;
            justify-content: space-between;
        }}

        .search-box {{
            flex: 1;
            min-width: 280px;
            position: relative;
        }}

        .search-box input {{
            width: 100%;
            padding: 0.75rem 1rem 0.75rem 2.75rem;
            border-radius: 10px;
            border: 1px solid var(--border-color);
            background: var(--bg-body);
            color: var(--text-primary);
            font-size: 0.95rem;
        }}

        .search-box i {{
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
        }}

        .filter-group {{
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
        }}

        .filter-btn {{
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            background: var(--bg-body);
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .filter-btn.active, .filter-btn:hover {{
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }}

        /* Jobs Grid */
        .jobs-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
            gap: 1.5rem;
        }}

        .job-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .job-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
            border-color: var(--primary);
        }}

        .job-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
            margin-bottom: 1rem;
        }}

        .job-title {{
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.4;
        }}

        .job-company {{
            font-weight: 600;
            color: var(--primary);
            font-size: 0.95rem;
            margin-top: 0.25rem;
        }}

        .score-badge {{
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            font-weight: 800;
            padding: 0.35rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
            white-space: nowrap;
        }}

        .score-badge.medium {{
            background: linear-gradient(135deg, #f59e0b, #d97706);
        }}

        .job-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin: 1rem 0;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}

        .meta-item {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }}

        .job-reason {{
            background: rgba(15, 23, 42, 0.6);
            border-left: 3px solid var(--primary);
            padding: 0.75rem 1rem;
            border-radius: 0 8px 8px 0;
            font-size: 0.85rem;
            color: #cbd5e1;
            margin-bottom: 1.25rem;
        }}

        .job-actions {{
            display: flex;
            gap: 0.75rem;
        }}

        .btn-apply {{
            flex: 1;
            text-align: center;
            background: var(--primary);
            color: white;
            padding: 0.65rem 1rem;
            border-radius: 8px;
            font-weight: 600;
            text-decoration: none;
            transition: background 0.2s;
            font-size: 0.88rem;
        }}

        .btn-apply:hover {{
            background: #2563eb;
        }}

        footer {{
            text-align: center;
            margin-top: 4rem;
            color: var(--text-secondary);
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>

    <header>
        <div class="nav-container">
            <div class="brand">
                <i class="fa-solid fa-rocket"></i>
                <span id="txtNavTitle">Job-Scan AI Discovery & Matcher</span>
            </div>
            <div class="top-right-actions">
                <div class="lang-dropdown-wrapper">
                    <select id="langSelect" class="lang-select" onchange="changeLanguage(this.value)">
                        <option value="vi" selected>🇻🇳 Tiếng Việt</option>
                        <option value="en">🇬🇧 English</option>
                    </select>
                </div>
            </div>
        </div>
    </header>

    <div class="container">
        <!-- Stats Overview -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon"><i class="fa-solid fa-briefcase"></i></div>
                <div>
                    <div class="stat-val" id="statTotal">0</div>
                    <div class="stat-label" id="lblStatTotal">Tổng số job đã quét</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon" style="color: var(--accent); background: rgba(16, 185, 129, 0.15);"><i class="fa-solid fa-star"></i></div>
                <div>
                    <div class="stat-val" id="statHighMatch">0</div>
                    <div class="stat-label" id="lblStatHighMatch">Phù hợp cao (>=8.0)</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon" style="color: var(--warning); background: rgba(245, 158, 11, 0.15);"><i class="fa-solid fa-user-graduate"></i></div>
                <div>
                    <div class="stat-val">Fresher / Junior</div>
                    <div class="stat-label" id="lblStatTarget">Tiêu chí (<= 2 năm exp)</div>
                </div>
            </div>
        </div>

        <!-- Filter Bar -->
        <div class="filter-section">
            <div class="search-box">
                <i class="fa-solid fa-magnifying-glass"></i>
                <input type="text" id="searchInput" placeholder="Tìm kiếm công ty, vị trí hoặc từ khóa..." oninput="filterJobs()">
            </div>
            <div class="filter-group">
                <button class="filter-btn active" data-filter="all" onclick="setGroupFilter('all', this)" id="btnFilterAll">Tất cả</button>
                <button class="filter-btn" data-filter="high" onclick="setGroupFilter('high', this)" id="btnFilterHigh">🎯 Match Cao (>=8.0)</button>
            </div>
        </div>

        <!-- Jobs Grid -->
        <div class="jobs-grid" id="jobsContainer"></div>

        <footer>
            <p id="txtFooter">Job-Scan AI Assistant &copy; 2026 Nguyễn Tùng Lâm — FPT University Graduate (Software Engineering)</p>
        </footer>
    </div>

    <script>
        const JOBS_DATA = {json_data_str};

        const I18N = {{
            vi: {{
                navTitle: "Job-Scan AI Discovery & Matcher",
                statTotal: "Tổng số job đã quét",
                statHighMatch: "Phù hợp cao (>=8.0)",
                statTarget: "Tiêu chí (<= 2 năm exp)",
                searchPlaceholder: "Tìm kiếm công ty, vị trí hoặc từ khóa...",
                filterAll: "Tất cả",
                filterHigh: "🎯 Match Cao (>=8.0)",
                btnApply: "Xem & Ứng tuyển",
                reasonTitle: "Lý do khớp:",
                footer: "Job-Scan AI Assistant &copy; 2026 Nguyễn Tùng Lâm — Kỹ sư phần mềm FPT University"
            }},
            en: {{
                navTitle: "Job-Scan AI Discovery & Matcher",
                statTotal: "Total Scanned Jobs",
                statHighMatch: "High Match (>=8.0)",
                statTarget: "Target Level (<= 2 yrs exp)",
                searchPlaceholder: "Search company, title, or keywords...",
                filterAll: "All Jobs",
                filterHigh: "🎯 High Match (>=8.0)",
                btnApply: "View & Apply",
                reasonTitle: "Match Reason:",
                footer: "Job-Scan AI Assistant &copy; 2026 Nguyen Tung Lam — FPT University Software Engineering Graduate"
            }}
        }};

        let currentLang = localStorage.getItem('job_scan_lang') || 'vi';
        let currentFilter = 'all';

        function changeLanguage(lang) {{
            currentLang = lang;
            localStorage.setItem('job_scan_lang', lang);
            document.getElementById('langSelect').value = lang;
            
            const t = I18N[lang];
            document.getElementById('txtNavTitle').innerText = t.navTitle;
            document.getElementById('lblStatTotal').innerText = t.statTotal;
            document.getElementById('lblStatHighMatch').innerText = t.statHighMatch;
            document.getElementById('lblStatTarget').innerText = t.statTarget;
            document.getElementById('searchInput').placeholder = t.searchPlaceholder;
            document.getElementById('btnFilterAll').innerText = t.filterAll;
            document.getElementById('btnFilterHigh').innerText = t.filterHigh;
            document.getElementById('txtFooter').innerHTML = t.footer;

            renderJobs();
        }}

        function renderJobs() {{
            const container = document.getElementById('jobsContainer');
            const searchKeyword = document.getElementById('searchInput').value.toLowerCase();
            const t = I18N[currentLang];

            let filtered = JOBS_DATA.filter(job => {{
                const title = (job['Vị Trí Tuyển Dụng'] || '').toLowerCase();
                const comp = (job['Tên Công Ty'] || '').toLowerCase();
                const reason = (job['Lý Do Khớp'] || '').toLowerCase();
                const matchesSearch = title.includes(searchKeyword) || comp.includes(searchKeyword) || reason.includes(searchKeyword);
                
                const score = parseFloat(job['Điểm Phù Hợp (1-10)'] || 0);
                const matchesGroup = (currentFilter === 'all') || (currentFilter === 'high' && score >= 8.0);

                return matchesSearch && matchesGroup;
            }});

            // Stats update
            document.getElementById('statTotal').innerText = JOBS_DATA.length;
            const highCount = JOBS_DATA.filter(j => parseFloat(j['Điểm Phù Hợp (1-10)'] || 0) >= 8.0).length;
            document.getElementById('statHighMatch').innerText = highCount;

            if (filtered.length === 0) {{
                container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-secondary); padding: 3rem;">
                    <i class="fa-solid fa-folder-open" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                    <p>${{currentLang === 'vi' ? 'Không tìm thấy công việc phù hợp.' : 'No matching jobs found.'}}</p>
                </div>`;
                return;
            }}

            container.innerHTML = filtered.map(job => {{
                const score = parseFloat(job['Điểm Phù Hợp (1-10)'] || 0);
                const badgeClass = score >= 8.0 ? '' : 'medium';
                
                return `
                <div class="job-card">
                    <div>
                        <div class="job-header">
                            <div>
                                <div class="job-title">${{job['Vị Trí Tuyển Dụng'] || 'N/A'}}</div>
                                <div class="job-company">${{job['Tên Công Ty'] || 'N/A'}}</div>
                            </div>
                            <div class="score-badge ${{badgeClass}}">⭐ ${{score}}/10</div>
                        </div>

                        <div class="job-meta">
                            <span class="meta-item"><i class="fa-solid fa-money-bill-wave"></i> ${{job['Mức Lương'] || 'Thỏa thuận'}}</span>
                            <span class="meta-item"><i class="fa-solid fa-location-dot"></i> ${{job['Địa Điểm'] || 'Hà Nội'}}</span>
                        </div>

                        <div class="job-reason">
                            <strong>${{t.reasonTitle}}</strong> ${{job['Lý Do Khớp'] || 'N/A'}}
                        </div>
                    </div>

                    <div class="job-actions">
                        <a href="${{job['Link Ứng Tuyển'] || '#'}}" target="_blank" class="btn-apply">
                            <i class="fa-solid fa-arrow-up-right-from-square"></i> ${{t.btnApply}}
                        </a>
                    </div>
                </div>`;
            }}).join('');
        }}

        function filterJobs() {{
            renderJobs();
        }}

        function setGroupFilter(filterType, btn) {{
            currentFilter = filterType;
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            renderJobs();
        }}

        // Initialize language and dashboard
        document.addEventListener('DOMContentLoaded', () => {{
            changeLanguage(currentLang);
        }});
    </script>
</body>
</html>"""

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # Đồng bộ sang index.html ở root để dễ mở
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"✓ Đã xuất thành công Web HTML Dashboard tại: {output_html} & index.html")

if __name__ == "__main__":
    generate_html_dashboard()
