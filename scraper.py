import os
import re
import requests
from dotenv import load_dotenv

# .env 파일 로드 (로컬 실행용)
load_dotenv()
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
from datetime import datetime

# Airtable 설정
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = "리포트 자료 추출"
AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--headless")  # headless 모드
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Selenium WebDriver 초기화 (Selenium 4.6+는 자동으로 ChromeDriver 관리)
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)

# 페이지별 데이터 추출 함수
def extract_industry_report(row):
    """산업분석 리포트 데이터 추출"""
    cols = row.find_elements(By.TAG_NAME, "td")
    if len(cols) < 5:
        return None
       
    try:
        title_element = cols[1].find_element(By.TAG_NAME, "a")
        return {
            "category": cols[0].text.strip(),
            "title": title_element.text.strip(),
            "company": cols[2].text.strip(),
            "date": cols[4].text.strip(),
            "detail_url": urljoin("https://finance.naver.com", title_element.get_attribute("href"))
        }
    except:
        return None

def extract_investment_report(row):
    """투자정보 리포트 데이터 추출"""
    cols = row.find_elements(By.TAG_NAME, "td")
    if len(cols) < 4:
        return None
       
    try:
        title_element = cols[0].find_element(By.TAG_NAME, "a")
        return {
            "category": "투자정보",
            "title": title_element.text.strip(),
            "company": cols[1].text.strip(),
            "date": cols[3].text.strip(),
            "detail_url": urljoin("https://finance.naver.com", title_element.get_attribute("href"))
        }
    except:
        return None

def extract_market_report(row):
    """시황정보 리포트 데이터 추출"""
    cols = row.find_elements(By.TAG_NAME, "td")
    if len(cols) < 4:
        return None
       
    try:
        title_element = cols[0].find_element(By.TAG_NAME, "a")
        return {
            "category": "시황정보",
            "title": title_element.text.strip(),
            "company": cols[1].text.strip(),
            "date": cols[3].text.strip(),
            "detail_url": urljoin("https://finance.naver.com", title_element.get_attribute("href"))
        }
    except:
        return None

def extract_economy_report(row):
    """경제분석 리포트 데이터 추출"""
    cols = row.find_elements(By.TAG_NAME, "td")
    if len(cols) < 4:
        return None
       
    try:
        title_element = cols[0].find_element(By.TAG_NAME, "a")
        return {
            "category": "경제분석",
            "title": title_element.text.strip(),
            "company": cols[1].text.strip(),
            "date": cols[3].text.strip(),
            "detail_url": urljoin("https://finance.naver.com", title_element.get_attribute("href"))
        }
    except:
        return None

def extract_company_report(row):
    """종목분석 리포트 데이터 추출"""
    cols = row.find_elements(By.TAG_NAME, "td")
    if len(cols) < 5:
        return None
       
    try:
        # 종목명 (첫 번째 컬럼)
        stock_element = cols[0].find_element(By.TAG_NAME, "a")
        stock_name = stock_element.text.strip()
        
        # 제목 (두 번째 컬럼)
        title_element = cols[1].find_element(By.TAG_NAME, "a")
        
        # PDF 링크 (네 번째 컬럼 - 첨부)
        try:
            pdf_element = cols[3].find_element(By.TAG_NAME, "a")
            pdf_url = pdf_element.get_attribute("href")
        except:
            pdf_url = None
        
        return {
            "category": "종목분석",
            "stock_name": stock_name,
            "title": title_element.text.strip(),
            "company": cols[2].text.strip(),
            "date": cols[4].text.strip(),
            "detail_url": urljoin("https://finance.naver.com", title_element.get_attribute("href")),
            "pdf_url": pdf_url  # 목록에서 직접 PDF URL 추출
        }
    except:
        return None

# 페이지별 추출 함수 매핑
report_extractors = {
    "https://finance.naver.com/research/industry_list.naver": (extract_industry_report, "산업분석 리포트"),
    "https://finance.naver.com/research/invest_list.naver": (extract_investment_report, "투자정보 리포트"),
    "https://finance.naver.com/research/market_info_list.naver": (extract_market_report, "시황정보 리포트"),
    "https://finance.naver.com/research/economy_list.naver": (extract_economy_report, "경제분석 리포트"),
    "https://finance.naver.com/research/company_list.naver": (extract_company_report, "종목분석 리포트")
}

# 모든 리포트 메타데이터 저장
all_reports = []

# 각 리포트 페이지 스크레이핑
for url, (extractor, report_type) in report_extractors.items():
    try:
        driver.get(url)
        table = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "type_1")))
        rows = table.find_elements(By.TAG_NAME, "tr")

        for row in rows:
            try:
                data = extractor(row)
                if not data:
                    continue

                # 날짜 형식 변환
                if re.match(r"\d{2}\.\d{2}\.\d{2}", data["date"]):
                    full_date = "20" + data["date"].replace(".", "-")
                else:
                    continue

                all_reports.append({
                    "category": data["category"],
                    "stock_name": data.get("stock_name"),  # 종목분석 리포트용
                    "title": data["title"],
                    "company": data["company"],
                    "full_date": full_date,
                    "detail_url": data["detail_url"],
                    "report_type": report_type,
                    "list_pdf_url": data.get("pdf_url")  # 목록에서 가져온 PDF URL (종목분석용)
                })

            except Exception as e:
                print(f"{url} 행 처리 중 오류: {e}")
                continue

    except Exception as e:
        print(f"{url} 페이지 처리 중 오류: {e}")
        continue

# 오늘 날짜에 해당하는 리포트만 필터링
today = datetime.now().strftime("%Y-%m-%d")
filtered_reports = [report for report in all_reports if report["full_date"] == today]

if not filtered_reports:
    print(f"{today} 날짜에 해당하는 리포트가 없습니다.")
    driver.quit()
    exit()

# 필터링된 리포트의 상세 페이지 처리
for report in filtered_reports:
    try:
        driver.get(report["detail_url"])
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "view_cnt")))

        # 요약 추출
        try:
            content_div = driver.find_element(By.CLASS_NAME, "view_cnt")
            summary = content_div.find_element(By.TAG_NAME, "div").text.strip()
            if not summary:
                summary = "요약을 찾을 수 없습니다."
        except:
            summary = "요약을 찾을 수 없습니다."

        # PDF URL 추출 (종목분석은 이미 목록에서 가져온 경우 사용)
        if report.get("list_pdf_url"):
            pdf_url = report["list_pdf_url"]
        else:
            try:
                pdf_link = driver.find_element(By.XPATH, "//a[contains(@href, '.pdf')]")
                pdf_url = urljoin("https://finance.naver.com", pdf_link.get_attribute("href"))
            except:
                pdf_url = None

        report["summary"] = summary
        report["pdf_url"] = pdf_url

    except Exception as e:
        print(f"상세 페이지 처리 중 오류 {report['detail_url']}: {e}")
        report["summary"] = "요약을 찾을 수 없습니다."
        report["pdf_url"] = None
        continue

# Airtable에 업로드
for report in filtered_reports:
    if report["full_date"] and report["pdf_url"]:
        fields = {
            "날짜": report["full_date"],
            "리포트 종류": report["report_type"],
            "분류": report["category"],
            "증권사": report["company"],
            "리포트명": report["title"],
            "리포트 링크": report["detail_url"],
            "PDF파일": [{"url": report["pdf_url"]}],
            "PDF파일 링크": report["pdf_url"],
            "리포트 서머리": report["summary"]
        }
        
        # 종목분석 리포트인 경우 종목명 필드 추가
        if report.get("stock_name"):
            fields["종목명"] = report["stock_name"]
        
        report_data = {"fields": fields}
        try:
            response = requests.post(AIRTABLE_URL, headers=HEADERS, json=report_data)
            if response.status_code == 200:
                print(f"성공적으로 업로드됨: {report['title']} ({report['report_type']})")
            else:
                print(f"업로드 실패 {report['title']}: {response.text}")
        except Exception as e:
            print(f"업로드 중 오류 {report['title']}: {e}")
    else:
        print(f"날짜 또는 PDF URL 누락으로 인해 {report['title']} 건너뜀")

# 정리
driver.quit()
print("스크레이핑 및 업로드 완료.")
