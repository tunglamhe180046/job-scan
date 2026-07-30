# Job Scan

An interactive Python toolkit for collecting company information from ITviec and TopCV, discovering company websites, matching vacancies against a configurable candidate profile, and assisting with job-application preparation.

It is designed as a **human-in-the-loop** workflow: Playwright opens a visible browser so that the user can handle CAPTCHA, inspect pages, and make the final submission decision themselves.

## Highlights

- Collects company profiles from ITviec and TopCV search-result pages.
- Extracts candidate official websites and removes recurring platform/system domains.
- Exports company data to Excel or CSV.
- Finds vacancies from ITviec/TopCV company profiles or a company's own careers page.
- Scores roles against a candidate profile and preserves prior application status in reports.
- Generates tailored cover-letter drafts and can fill supported application forms.
- Leaves the final **Apply** action to the user.

## Tech Stack

- Python 3.8+
- Playwright
- pandas and openpyxl
- Rich terminal UI

## Project Structure

```text
job-scan/
├── main.py              # Interactive command-line entry point
├── scraper.py           # ITviec company discovery
├── topcv_scraper.py     # TopCV company discovery
├── job_matcher.py       # Vacancy extraction and profile-based scoring
├── apply_assistant.py   # Cover-letter drafting and assisted form filling
├── requirements.txt
└── README.md
```

Generated reports, browser sessions, debug captures, virtual environments, and the separately versioned `My-CV` folder are deliberately excluded from Git.

## Getting Started

### Prerequisites

- Python 3.8 or later
- An internet connection
- A Chromium-compatible browser installation through Playwright

### Installation

```powershell
git clone https://github.com/tunglamhe180046/job-scan.git
cd job-scan

python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
playwright install chromium
```

On Command Prompt, activate the virtual environment with:

```bat
venv\Scripts\activate.bat
```

## Usage

Run the interactive menu:

```powershell
python main.py
```

The menu provides four workflows:

1. **ITviec company discovery** — collects companies from an ITviec results page and identifies candidate official websites.
2. **TopCV company discovery** — performs the equivalent workflow for TopCV.
3. **Job matching** — reads the merged company report, collects vacancies, scores suitable roles, and saves `reports/matched_jobs_report.xlsx`.
4. **Apply Assistant** — prepares a tailored cover letter and fills supported fields. The user reviews the content and submits the application manually.

### Company Discovery Workflow

1. Select ITviec or TopCV from the menu.
2. Enter a results-page URL and the number of pages to process.
3. When Chromium opens, complete any CAPTCHA/Cloudflare challenge yourself.
4. Return to the terminal and press Enter to continue.
5. Choose an `.xlsx` or `.csv` output path, such as `reports/companies_list.xlsx`.

The tool collects profile links, extracts external links, counts domains that recur across three or more companies, removes those shared platform domains, and selects the shortest remaining candidate URL as the company's website.

### Job Matching Workflow

The matcher reads `reports/all_companies_merged.xlsx` (or `all_companies_merged.xlsx` in the project root), then supports two modes:

- **Profile mode**: gathers job posts from ITviec and TopCV company profiles.
- **Company-site mode**: finds a careers page on the official company website and extracts job links.

Roles receive a 1–10 fit score from the configured profile. The current rules prioritize AI workflow, Java/React, .NET, mobile/Unity, Japanese-language, and junior/fresher opportunities while down-ranking internships and senior/lead roles. Review the generated report before applying; scoring is guidance, not a hiring recommendation.

## Responsible Use

- Use the tool only with websites and accounts you are authorized to access.
- Respect each site's terms of service, robots policies, rate limits, and applicable law.
- CAPTCHA and anti-bot challenges must be completed by the user in the visible browser.
- Do not automate final job submissions without an explicit human review.
- Local browser sessions are stored under `user_data/` and are ignored by Git. Never commit this directory.

## Output and Privacy

The default output directory is `reports/`. It may contain company information, job links, application statuses, and dates, so it is intentionally ignored by Git. The persistent Playwright browser profile in `user_data/` may contain session data and is also ignored.

## Troubleshooting

**`playwright` command is not found**

Activate the virtual environment and reinstall dependencies:

```powershell
pip install -r requirements.txt
playwright install chromium
```

**A website shows Cloudflare or CAPTCHA**

Complete the challenge in the browser window, then return to the terminal and press Enter when prompted.

**An Excel report cannot be overwritten**

Close the report in Excel and run the workflow again. The tool attempts to save a timestamped fallback file when the destination is locked.
