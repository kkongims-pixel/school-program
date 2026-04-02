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
# 2. 프로그램 일정 및 정원 설정 (정원 10명, 예비 2명)
# --------------------------------------------------------------------------
RESERVE_LIMIT = 2  # 🔴 예비 인원을 2명으로 수정했습니다.

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
        if len(data) <= 1: return pd.DataFrame(columns=COLUMNS)
        return pd.DataFrame(data[1:], columns=data[0])
    except: return pd.DataFrame(columns=COLUMNS)

def load_data_fresh():
    try:
        data = sheet.get_all_values()
        if len(data) <= 1: return pd.DataFrame(columns=COLUMNS)
        return pd.DataFrame(data[1:], columns=data[0])
    except: return pd.DataFrame(columns=COLUMNS)

def save_data(new_entry_list):
    sheet.append_row(new_entry_list)
    load_data_cached.clear()

def count_in_dataframe(df, date, school, program_name):
    if df.empty: return 0
    return len(df[(df['체험날짜'] == date) & (df['학교'] == school) & (df['프로그램'] == program_name)])

def get_user_history(df, name, phone):
    if df.empty: return pd.DataFrame(columns=COLUMNS)
    return df[(df['이름'].str.strip() == name.strip()) & (df['연락처'].str.strip() == phone.strip())]

def format_phone_number(phone):
    if len(phone) == 11 and phone.isdigit(): return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
    return phone

# --------------------------------------------------------------------------
# 4. 시간 설정 (KST)
# --------------------------------------------------------------------------
kst = pytz.timezone('Asia/Seoul')
now_kst = datetime.now(kst)

# --------------------------------------------------------------------------
# 5. 메인 화면 구성
# --------------------------------------------------------------------------
# 제목 크기 조정 (한 줄로 나오게)
st.markdown("<h2 style='font-size: 30px; font-weight: bold; word-break: keep-all; margin-bottom: 20px;'>🏫 2026년 신산업분야 중학생 직업체험 프로그램 신청</h2>", unsafe_allow_html=True)

st.markdown("""
### 📢 [신청 전 유의사항]
1. **날짜를 먼저 선택**해야 해당 일자의 학교 및 프로그램 목록이 나타납니다.
2. **같은 날짜**에는 **1개의 프로그램**만 신청할 수 있습니다.
3. 이전에 신청했던 프로그램과 **동일한 프로그램은 중복 신청이 불가능**합니다.
4. 각 프로그램은 **설정된 정원(선착순)** 마감입니다.
5. **예비 신청자**는 정원 내 취소자가 발생할 경우 **순차적**으로 연락드립니다.
6. 본인 확인을 위해 **이름과 연락처를 정확하게** 입력해주세요.
""")

st.info("""
**🔒 [개인정보 수집 및 이용 안내]** 본 신청 페이지에서 수집하는 개인정보(이름, 연락처, 학교, 학년, 반)는 **'직업체험 프로그램' 운영 및 관리 목적**으로만 사용됩니다.
""")

st.markdown("---")

# =========================================================
# 1단계: 학생 정보 입력 (에러 난 부분 수정 완료!)
# =========================================================
st.subheader("1. 학생 정보 입력")
r1c1, r1c2 = st.columns(2)
with r1c1: 
    name_input = st.text_input("이름 (예: 홍길동)")
with r1c2: 
    phone_input = st.text_input("연락처 (숫자만 입력)", max_chars=11)

r2c1, r2c2, r2c3 = st.columns(3)
with r2c1: 
    school_input = st.text_input("중학교 (예: OO중)")
with r2c2: 
    grade_input = st.selectbox("학년", ["1학년", "2학년", "3학년"])
with r2c3: 
    class_input = st.text_input("반 (숫자만 입력)")

st.markdown("---")

# =========================================================
# 2단계: 체험 프로그램 선택
# =========================================================
st.subheader("2. 체험 프로그램 선택")
selected_date = st.selectbox("날짜 선택", list(SCHEDULE.keys()))
selected_school = st.selectbox("체험할 고등학교 선택", list(SCHEDULE[selected_date].keys()))

cached_df = load_data_cached()
raw_programs_data = SCHEDULE[selected_date][selected_school]

display_options = []
display_map, limit_map = {}, {}

for item in raw_programs_data:
    prog_name, prog_limit = item["name"], item["limit"]
    current_count = count_in_dataframe(cached_df, selected_date, selected_school, prog_name)
    
    if current_count >= (prog_limit + RESERVE_LIMIT):
        display_text = f"🚫 [마감] {prog_name}"
    elif current_count >= prog_limit:
        res_num = current_count - prog_limit + 1
        display_text = f"⚠️ [예비신청 가능] {prog_name} (예비 {res_num}/{RESERVE_LIMIT}번)"
    else:
        display_text = f"✅ [정원신청 가능] {prog_name} (신청현황: {current_count}/{prog_limit}명)"
    
    display_options.append(display_text)
    display_map[display_text], limit_map[prog_name] = prog_name, prog_limit

selected_display = st.selectbox("프로그램 선택", display_options)
real_program_name = display_map[selected_display]
current_limit = limit_map[real_program_name]

st.markdown("---")

# =========================================================
# 3단계: 최종 신청 버튼 (🔴 버튼 문구 및 강조 수정)
# =========================================================
st.write("") # 간격 조절
if st.button("🚀 신청하기", use_container_width=True, type="primary"):
    
    if not name_input or not phone_input or not school_input or not class_input:
        st.error("❌ 학생 정보를 모두 입력해주세요.")
    elif not phone_input.isdigit():
        st.warning("연락처에는 숫자만 입력해주세요.")
    elif len(phone_input) != 11:
        st.warning("연락처 11자리를 모두 입력해주세요.")
    elif not phone_input.startswith("010"):
        st.warning("연락처는 010으로 시작해야 합니다.")
    elif "[마감]" in selected_display:
        st.error("❌ 이미 예비 인원까지 모두 마감되었습니다.")
    else:
        formatted_phone = format_phone_number(phone_input)
        fresh_df = load_data_fresh() 
        final_count = count_in_dataframe(fresh_df, selected_date, selected_school, real_program_name)
        
        if final_count >= (current_limit + RESERVE_LIMIT):
            st.error(f"😭 아쉽지만 예비 인원까지 모두 마감되었습니다.")
            load_data_cached.clear() 
        else:
            user_history = get_user_history(fresh_df, name_input, formatted_phone)
            
            if not user_history.empty:
                date_dup = user_history[user_history['체험날짜'] == selected_date]
                prog_dup = user_history[user_history['프로그램'] == real_program_name]
                
                if not date_dup.empty:
                    st.error(f"🚫 '{selected_date}'에는 이미 신청 내역이 있어 중복 신청할 수 없습니다.")
                elif not prog_dup.empty:
                    st.error(f"🚫 '{real_program_name}' 프로그램은 이미 신청하셨습니다.")
                else:
                    # 저장 로직
                    if final_count < current_limit:
                        status_text = str(final_count + 1)
                    else:
                        reserve_no = final_count - current_limit + 1
                        status_text = f"예비 {reserve_no}"

                    new_entry_list = [
                        datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S"),
                        name_input, formatted_phone, school_input, grade_input, class_input,
                        selected_date, selected_school, real_program_name, status_text
                    ]
                    save_data(new_entry_list)
                    
                    if final_count < current_limit:
                        st.success(f"🎉 신청이 완료되었습니다! ({real_program_name})")
                        st.balloons()
                    else:
                        reserve_no = final_count - current_limit + 1
                        st.warning(f"예비 {reserve_no}번으로 접수되었습니다.")

with st.expander("관리자 메뉴"):
    st.write("데이터는 구글 스프레드시트에 실시간으로 저장되고 있습니다.")
    if 'SHEET_URL' in locals():
        st.link_button("📊 구글 시트로 이동하여 명단 확인하기", SHEET_URL)
