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
    st.balloons()
    del st.session_state['success_msg']

if 'warning_msg' in st.session_state:
    st.warning(st.session_state['warning_msg'])
    del st.session_state['warning_msg']

# =========================================================
# 1단계: 학생 정보 입력 (초기화를 위해 key 값 추가)
# =========================================================
st.subheader("1. 학생 정보 입력")

row1_col1, row1_col2 = st.columns(2)
with row1_col1:
    name_input = st.text_input("이름 (예: 홍길동)", key="k_name")
with row1_col2:
    phone_input = st.text_input("연락처 (숫자만 입력)", max_chars=11, key="k_phone")

row2_col1, row2_col2, row2_col3 = st.columns(3)
with row2_col1:
    school_input = st.text_input("중학교 (예: OO중)", key="k_school")
with row2_col2:
    grade_input = st.selectbox("학년", ["1학년", "2학년", "3학년"], index=None, placeholder="선택하세요", key="k_grade")
with row2_col3:
    class_input = st.text_input("반 (숫자만 입력)", key="k_class")

st.markdown("---")

# =========================================================
# 2단계: 체험 프로그램 선택 (초기화를 위해 key 값 추가)
# =========================================================
st.subheader("2. 체험 프로그램 선택")

selected_date = st.selectbox("날짜 선택", list(SCHEDULE.keys()), index=None, placeholder="📅 날짜를 선택하세요", key="k_date")

available_schools = list(SCHEDULE[selected_date].keys()) if selected_date else []
selected_school = st.selectbox("체험할 고등학교 선택", available_schools, index=None, placeholder="🏫 체험할 고등학교를 선택하세요", key="k_highschool")

display_options = []
display_map = {} 
limit_map = {}

if selected_date and selected_school:
    cached_df = load_data_cached()
    raw_programs_data = SCHEDULE[selected_date][selected_school]

    for item in raw_programs_data:
        prog_name = item["name"]   
        prog_limit = item["limit"] 
        
        current_count = count_in_dataframe(cached_df, selected_date, selected_school, prog_name)
        
        if current_count >= (prog_limit + RESERVE_LIMIT):
            display_text = f"🚫 [마감] {prog_name} (정원 및 예비 마감)"
        elif current_count >= prog_limit:
            res_num = current_count - prog_limit + 1
            display_text = f"⚠️ [예비신청 가능] {prog_name} (현재 예비 {res_num}/{RESERVE_LIMIT}번)"
        else:
            display_text = f"✅ [정원신청 가능] {prog_name} (신청현황: {current_count}/{prog_limit}명)"
        
        display_options.append(display_text)
        display_map[display_text] = prog_name
        limit_map[prog_name] = prog_limit 

selected_display = st.selectbox("프로그램 선택", display_options, index=None, placeholder="💡 신청할 프로그램을 선택하세요", key="k_program")

st.markdown("---")

# =========================================================
# 3단계: 최종 신청 버튼 (성공 시 내용 초기화 기능 추가)
# =========================================================
if st.button("🚀 신청하기", use_container_width=True, type="primary"):
    
    if not name_input or not name_input.strip():
        st.error("❌ [학생 정보] '이름' 칸이 비어있습니다. 이름을 입력해주세요.")
    elif not phone_input or not phone_input.strip():
        st.error("❌ [학생 정보] '연락처' 칸이 비어있습니다. 연락처를 입력해주세요.")
    elif not school_input or not school_input.strip():
        st.error("❌ [학생 정보] '중학교' 칸이 비어있습니다. 학교명을 입력해주세요.")
    elif not grade_input:
        st.error("❌ [학생 정보] '학년'을 선택해주세요. (현재 '선택하세요' 상태입니다)")
    elif not class_input or not class_input.strip():
        st.error("❌ [학생 정보] '반' 칸이 비어있습니다. 몇 반인지 입력해주세요.")
    elif not selected_date or not selected_school or not selected_display:
        st.error("❌ [프로그램 선택] 날짜, 고등학교, 프로그램을 모두 정확하게 골라주세요.")
    elif not phone_input.isdigit():
        st.warning("연락처에는 하이픈(-) 없이 숫자만 입력해주세요.")
    elif len(phone_input) != 11:
        st.warning("연락처 11자리를 모두 입력해주세요.")
    elif not phone_input.startswith("010"):
        st.warning("연락처는 010으로 시작해야 합니다.")
    elif "[마감]" in selected_display:
        st.error("❌ 이미 예비 인원까지 모두 마감되었습니다.")
    else:
        real_program_name = display_map[selected_display]
        current_limit = limit_map[real_program_name]
        formatted_phone = format_phone_number(phone_input.strip())
        clean_name = name_input.strip()
        clean_school = school_input.strip()
        clean_class = class_input.strip()
        
        fresh_df = load_data_fresh() 
        final_count = count_in_dataframe(fresh_df, selected_date, selected_school, real_program_name)
        
        if final_count >= (current_limit + RESERVE_LIMIT):
            st.error(f"😭 아쉽지만 예비 인원까지 모두 마감되었습니다.")
            load_data_cached.clear() 
        else:
            user_history = get_user_history(fresh_df, clean_name, formatted_phone)
            
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
                if final_count < current_limit:
                    status_text = str(final_count + 1) 
                else:
                    reserve_no = final_count - current_limit + 1
                    status_text = f"예비 {reserve_no}" 

                new_entry_list = [
                    datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S"),
                    clean_name,
                    formatted_phone,
                    clean_school,
                    grade_input,
                    clean_class,
                    selected_date,
                    selected_school,
                    real_program_name,
                    status_text  
                ]
                
                save_data(new_entry_list)
                
                # 🔴 [핵심 로직] 성공 메시지를 기억해두고, 모든 입력칸 지우기
                if final_count < current_limit:
                    st.session_state['success_msg'] = f"🎉 신청이 완료되었습니다! ({real_program_name})"
                else:
                    reserve_no = final_count - current_limit + 1
                    st.session_state['warning_msg'] = f"예비 {reserve_no}번으로 접수되었습니다. ({real_program_name})"
                
                # 입력창을 새하얗게 초기화하는 마법의 코드
                for key in ["k_name", "k_phone", "k_school", "k_grade", "k_class", "k_date", "k_highschool", "k_program"]:
                    if key in st.session_state:
                        del st.session_state[key]
                        
                # 화면 즉시 새로고침 (입력칸 비우고 맨 위로 올림)
                st.rerun()

with st.expander("관리자 메뉴"):
    st.write("데이터는 구글 스프레드시트에 실시간으로 저장되고 있습니다.")
    if 'SHEET_URL' in locals():
        st.link_button("📊 구글 시트로 이동하여 명단 확인하기", SHEET_URL)
