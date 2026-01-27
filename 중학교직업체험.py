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
# 2. 프로그램 일정 및 정원 설정 (선생님 수정 구역)
# --------------------------------------------------------------------------
SCHEDULE = {
    "2월 1일": {
        "A고등학교": [
            {"name": "프로그램1 (AI 코딩)", "limit": 25}, 
            {"name": "프로그램2 (로봇)", "limit": 15},     
            {"name": "프로그램3 (3D 프린팅)", "limit": 20} 
        ],
        "B고등학교": [
            {"name": "프로그램1 (제과)", "limit": 12},     
            {"name": "프로그램2 (제빵)", "limit": 12},
            {"name": "프로그램3 (바리스타)", "limit": 10}
        ],
        "C고등학교": [
            {"name": "프로그램1 (드론)", "limit": 30},     
            {"name": "프로그램2 (VR 체험)", "limit": 20},
            {"name": "프로그램3 (게임개발)", "limit": 20}
        ],
    },
    "2월 2일": {
         "A고등학교": [
            {"name": "프로그램1 (AI 코딩)", "limit": 25},
            {"name": "프로그램2 (로봇)", "limit": 15},
            {"name": "프로그램3 (3D 프린팅)", "limit": 20}
        ],
        "B고등학교": [
            {"name": "프로그램1 (제과)", "limit": 12},
            {"name": "프로그램2 (제빵)", "limit": 12},
            {"name": "프로그램3 (바리스타)", "limit": 10}
        ],
        "C고등학교": [
            {"name": "프로그램1 (드론)", "limit": 30},
            {"name": "프로그램2 (VR 체험)", "limit": 20},
            {"name": "프로그램3 (게임개발)", "limit": 20}
        ],
    }
}

COLUMNS = ["신청일시", "이름", "연락처", "소속학교", "학년", "반", "체험날짜", "학교", "프로그램"]

# --------------------------------------------------------------------------
# 3. 데이터 처리 함수
# --------------------------------------------------------------------------
def load_data():
    try:
        data = sheet.get_all_values()
        if len(data) <= 1: 
            return pd.DataFrame(columns=COLUMNS)
        return pd.DataFrame(data[1:], columns=data[0])
    except:
        return pd.DataFrame(columns=COLUMNS)

def save_data(new_entry_list):
    sheet.append_row(new_entry_list)

def get_program_count(date, school, program_name):
    df = load_data()
    if df.empty: return 0
    filtered = df[
        (df['체험날짜'] == date) & 
        (df['학교'] == school) & 
        (df['프로그램'] == program_name)
    ]
    return len(filtered)

def get_user_history(name, phone):
    df = load_data()
    if df.empty: return pd.DataFrame(columns=COLUMNS)
    return df[(df['이름'].str.strip() == name.strip()) & (df['연락처'].str.strip() == phone.strip())]

def format_phone_number(phone):
    if len(phone) == 11 and phone.isdigit():
        return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
    return phone

# --------------------------------------------------------------------------
# 4. [오픈런] 시간 통제 설정
# --------------------------------------------------------------------------
OPEN_YEAR = 2024
OPEN_MONTH = 1
OPEN_DAY = 1
OPEN_HOUR = 9
OPEN_MINUTE = 0

kst = pytz.timezone('Asia/Seoul')
now_kst = datetime.now(kst)
open_time = datetime(OPEN_YEAR, OPEN_MONTH, OPEN_DAY, OPEN_HOUR, OPEN_MINUTE, 0, tzinfo=kst)

if now_kst < open_time:
    st.title("🚧 신청 기간이 아닙니다")
    st.error(f"📢 신청 시작 시간: {open_time.strftime('%Y년 %m월 %d일 %H시 %M분')}")
    st.info(f"🕰️ 현재 시간: {now_kst.strftime('%H시 %M분 %S초')}")
    st.write("시간이 되면 아래 [새로고침] 버튼을 눌러주세요.")
    if st.button("🔄 새로고침 (시간 확인)"):
        st.rerun()
    st.stop() 

# --------------------------------------------------------------------------
# 5. 메인 화면 및 로직 (수정된 부분)
# --------------------------------------------------------------------------
st.title("🏫 중학교 직업체험 신청")

st.markdown("""
### 📢 [신청 전 유의사항]
1. **날짜를 먼저 선택**해야 해당 일자의 학교 및 프로그램 목록이 나타납니다.
2. **같은 날짜**에는 **1개의 프로그램**만 신청할 수 있습니다.
3. 이전에 신청했던 프로그램과 **동일한 프로그램은 중복 신청이 불가능**합니다.
4. 각 프로그램은 **설정된 정원(선착순)** 마감입니다.
5. 본인 확인을 위해 **이름과 연락처를 정확하게** 입력해주세요.
""")

st.info("""
**🔒 [개인정보 수집 및 이용 안내]** 본 신청 페이지에서 수집하는 개인정보(이름, 연락처, 학교, 학년, 반)는 **'중학교 직업체험 활동' 운영 및 관리 목적**으로만 사용됩니다.
신청하기 버튼을 누르시면 위 내용에 동의하는 것으로 간주됩니다.
""")

st.markdown("---")

# =========================================================
# [중요] 선택 메뉴를 form 밖으로 꺼냈습니다! (즉시 반응하도록)
# =========================================================
st.subheader("1. 체험 프로그램 선택")

# 1. 날짜 및 학교 선택 (여기서 바꾸면 바로바로 화면이 바뀝니다)
selected_date = st.selectbox("날짜 선택", list(SCHEDULE.keys()))
available_schools = list(SCHEDULE[selected_date].keys())
selected_school = st.selectbox("체험할 고등학교 선택", available_schools)

# 2. 선택된 학교에 맞는 프로그램 목록 가져오기
raw_programs_data = SCHEDULE[selected_date][selected_school]

display_options = []
display_map = {} 
limit_map = {}

# 마감 여부 실시간 확인
for item in raw_programs_data:
    prog_name = item["name"]   
    prog_limit = item["limit"] 
    
    current_count = get_program_count(selected_date, selected_school, prog_name)
    
    if current_count >= prog_limit:
        display_text = f"🚫 [마감] {prog_name}"
    else:
        display_text = f"{prog_name} (신청: {current_count}/{prog_limit}명)"
    
    display_options.append(display_text)
    display_map[display_text] = prog_name
    limit_map[prog_name] = prog_limit 

# 3. 프로그램 선택창 표시
selected_display = st.selectbox("프로그램 선택", display_options)
real_program_name = display_map[selected_display]
current_limit = limit_map[real_program_name]

st.markdown("---")

# =========================================================
# 학생 정보 입력 및 제출 버튼 (여기는 form으로 감싸서 한 번에 제출)
# =========================================================
st.subheader("2. 학생 정보 입력")

with st.form("application_form"):
    col1, col2 = st.columns(2)
    with col1:
        name_input = st.text_input("이름 (예: 홍길동)")
        school_input = st.text_input("중학교 (예: OO중)")
        grade_input = st.selectbox("학년", ["1학년", "2학년", "3학년"])
    with col2:
        phone_input = st.text_input("연락처 (숫자만 입력)", max_chars=11)
        class_input = st.text_input("반 (숫자만 입력)")

    st.markdown("---")
    submitted = st.form_submit_button("위 내용으로 신청하기", use_container_width=True)

    # 제출 버튼을 눌렀을 때 처리
    if submitted:
        if not name_input or not phone_input or not school_input or not class_input:
            st.error("모든 정보를 입력해주세요.")
        elif not phone_input.isdigit():
            st.warning("연락처에는 숫자만 입력해주세요.")
        elif len(phone_input) != 11:
            st.warning("연락처 11자리를 모두 입력해주세요.")
        elif not phone_input.startswith("010"):
            st.warning("연락처는 010으로 시작해야 합니다.")
        elif "[마감]" in selected_display:
            st.error("선택하신 프로그램은 이미 마감되었습니다.")
        else:
            formatted_phone = format_phone_number(phone_input)
            
            # 최종 마감 재확인
            final_count = get_program_count(selected_date, selected_school, real_program_name)
            
            if final_count >= current_limit:
                st.error(f"아쉽지만 방금 마감되었습니다. (정원 {current_limit}명 초과)")
            else:
                user_history = get_user_history(name_input, formatted_phone)
                
                date_dup = pd.DataFrame()
                prog_dup = pd.DataFrame()
                
                if not user_history.empty:
                    date_dup = user_history[user_history['체험날짜'] == selected_date]
                    prog_dup = user_history[user_history['프로그램'] == real_program_name]
                
                if not date_dup.empty:
                    st.error(f"🚫 '{selected_date}'에는 이미 신청 내역이 있어 중복 신청할 수 없습니다.")
                elif not prog_dup.empty:
                    st.error(f"🚫 '{real_program_name}' 프로그램은 이미 신청하셨습니다.")
                else:
                    new_entry_list = [
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        name_input,
                        formatted_phone,
                        school_input,
                        grade_input,
                        class_input,
                        selected_date,
                        selected_school,
                        real_program_name
                    ]
                    
                    save_data(new_entry_list)
                    st.success(f"✅ 신청완료! 명단에 안전하게 저장되었습니다.")

# 관리자 메뉴
with st.expander("관리자 메뉴"):
    st.write("데이터는 구글 스프레드시트에 실시간으로 저장되고 있습니다.")
    if 'SHEET_URL' in locals():
        st.link_button("📊 구글 시트로 이동하여 명단 확인하기", SHEET_URL)
