import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import re
from datetime import datetime
import pytz

# --------------------------------------------------------------------------
# 1. 설정 및 구글 시트 연결
# --------------------------------------------------------------------------
st.set_page_config(page_title="체험 프로그램 신청", page_icon="🏫")

# Streamlit Secrets에서 정보 가져오기
try:
    SHEET_URL = st.secrets["gsheets"]["sheet_url"]
    json_creds = json.loads(st.secrets["gsheets"]["service_account"])
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(json_creds, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SHEET_URL).sheet1
except Exception as e:
    st.error(f"구글 시트 연결 오류: {e}")
    st.stop()

# --------------------------------------------------------------------------
# 2. 프로그램 일정 및 정원 설정
# --------------------------------------------------------------------------
RESERVE_LIMIT = 2  # 예비 인원 2명

SCHEDULE = {
    "2월 1일": {
        "자연과학고": [
            {"name": "프로그램1 (플라워)", "limit": 10},
            {"name": "프로그램2 (제과)", "limit": 10},
            {"name": "프로그램3 (펫푸드)", "limit": 10},
            {"name": "프로그램4 (조리)", "limit": 10}
        ],
        "전남공고": [
            {"name": "프로그램1 (AI 드론)", "limit": 10}, 
            {"name": "프로그램2 (AI 목공)", "limit": 10},     
            {"name": "프로그램3 (디퓨저)", "limit": 10} 
        ],
        "전자공고": [
            {"name": "프로그램1 (미래 자동차)", "limit": 10},     
            {"name": "프로그램2 (VR 체험)", "limit": 10},
            {"name": "프로그램3 (자율주행)", "limit": 10}
        ],
    },
    "2월 2일": {
        "자연과학고": [
            {"name": "프로그램1 (플라워)", "limit": 10},
            {"name": "프로그램2 (제과)", "limit": 10},
            {"name": "프로그램3 (펫푸드)", "limit": 10},
            {"name": "프로그램4 (조리)", "limit": 10}
        ],
        "전남공고": [
            {"name": "프로그램1 (AI 드론)", "limit": 10}, 
            {"name": "프로그램2 (AI 목공)", "limit": 10},     
            {"name": "프로그램3 (디퓨저)", "limit": 10} 
        ],
        "전자공고": [
            {"name": "프로그램1 (미래 자동차)", "limit": 10},     
            {"name": "프로그램2 (VR 체험)", "limit": 10},
            {"name": "프로그램3 (자율주행)", "limit": 10}
        ],
    }
}

COLUMNS = ["신청일시", "이름", "연락처", "소속학교", "학년", "반", "체험날짜", "학교", "프로그램", "접수상태"]

# --------------------------------------------------------------------------
# 3. 데이터 처리 함수
# --------------------------------------------------------------------------
@st.cache_data(ttl=5) 
def load_data_cached():
    try:
        data = sheet.get_all_values()
        if len(data) <= 1: 
            return pd.DataFrame(columns=COLUMNS)
        return pd.DataFrame(data[1:], columns=data[0])
    except:
        return pd.DataFrame(columns=COLUMNS)

def load_data_fresh():
    try:
        data = sheet.get_all_values()
        if len(data) <= 1: 
            return pd.DataFrame(columns=COLUMNS)
        return pd.DataFrame(data[1:], columns=data[0])
    except:
        return pd.DataFrame(columns=COLUMNS)

def save_data(new_entry_list):
    sheet.append_row(new_entry_list)
    load_data_cached.clear()

def count_in_dataframe(df, date, school, program_name):
    if df.empty: return 0
    filtered = df[
        (df['체험날짜'] == date) & 
        (df['학교'] == school) & 
        (df['프로그램'] == program_name)
    ]
    return len(filtered)

def get_user_history(df, name, phone):
    if df.empty: return pd.DataFrame(columns=COLUMNS)
    return df[(df['이름'].str.strip() == name.strip()) & (df['연락처'].str.strip() == phone.strip())]

def format_phone_number(phone):
    if len(phone) == 11 and phone.isdigit():
        return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
    return phone

# --------------------------------------------------------------------------
# 4. [오픈런] 시간 통제 설정
# --------------------------------------------------------------------------
OPEN_YEAR = 2026
OPEN_MONTH = 4
OPEN_DAY = 7
OPEN_HOUR = 11
OPEN_MINUTE = 20

kst = pytz.timezone('Asia/Seoul')
now_kst = datetime.now(kst)
open_time = kst.localize(datetime(OPEN_YEAR, OPEN_MONTH, OPEN_DAY, OPEN_HOUR, OPEN_MINUTE))

if now_kst < open_time:
    st.title("🚧 신청 기간이 아닙니다")
    st.error(f"📢 신청 시작 시간: {open_time.strftime('%Y년 %m월 %d일 %H시 %M분')}")
    st.info(f"🕰 현재 한국 시간: {now_kst.strftime('%Y년 %m월 %d일 %H시 %M분 %S초')}")
    st.write("시간이 되면 아래 [새로고침] 버튼을 눌러주세요.")
    if st.button("🔄 새로고침 (시간 확인)"):
        st.rerun()
    st.stop() 

# --------------------------------------------------------------------------
# 5. 메인 화면 구성
# --------------------------------------------------------------------------
st.markdown("<h2 style='font-size: 30px; font-weight: bold; word-break: keep-all; margin-bottom: 20px;'>🏫 2026년 신산업분야 중학생 직업체험 프로그램 신청</h2>", unsafe_allow_html=True)

st.markdown("""
### 📢 [신청 전 유의사항]
1. 본인 확인을 위해 **이름과 연락처를 정확하게** 입력해주세요.
2. **날짜를 먼저 선택**해야 해당 일자의 학교 및 프로그램 목록이 나타납니다.
3. **같은 날짜**에는 **1개의 프로그램**만 신청할 수 있습니다.
4. 이전에 신청했던 프로그램과 **동일한 프로그램은 중복 신청이 불가능**합니다.
5. 각 프로그램은 **설정된 정원(선착순)** 마감입니다.
6. **예비 신청자**는 정원 내 취소자가 발생할 경우 **순차적**으로 연락드립니다.
""")

st.info("""
**🔒 [개인정보 수집 및 이용 안내]** 본 신청 페이지에서 수집하는 개인정보(이름, 연락처, 학교, 학년, 반)는 **'직업체험 프로그램' 운영 및 관리 목적**으로만 사용됩니다.
신청하기 버튼을 누르시면 위 내용에 동의하는 것으로 간주됩니다.
""")

st.markdown("---")

# 🔴 [추가됨] 초기화 후 성공 메시지를 띄워주는 구역
if 'success_msg' in st.session_state:
    st.success(st.session_state['success_msg'])
