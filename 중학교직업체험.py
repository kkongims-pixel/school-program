import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import re
from datetime import datetime

# --- 1. 설정 및 구글 시트 연결 ---
MAX_CAPACITY = 20  # 프로그램당 정원

# Streamlit Secrets에서 정보 가져오기
try:
    # 1. 시트 주소 가져오기
    SHEET_URL = st.secrets["gsheets"]["sheet_url"]
    
    # 2. 인증 정보(JSON) 가져오기
    json_creds = json.loads(st.secrets["gsheets"]["service_account"])
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(json_creds, scopes=scope)
    client = gspread.authorize(creds)
    
    # 3. 시트 연결
    sheet = client.open_by_url(SHEET_URL).sheet1
except Exception as e:
    st.error(f"구글 시트 연결 오류: {e}")
    st.stop()

SCHEDULE = {
    "2월 1일": {
        "A고등학교": ["프로그램1 (AI 코딩)", "프로그램2 (로봇)", "프로그램3 (3D 프린팅)"],
        "B고등학교": ["프로그램1 (제과)", "프로그램2 (제빵)", "프로그램3 (바리스타)"],
        "C고등학교": ["프로그램1 (드론)", "프로그램2 (VR 체험)", "프로그램3 (게임개발)"],
    },
    "2월 2일": {
        "A고등학교": ["프로그램1 (AI 코딩)", "프로그램2 (로봇)", "프로그램3 (3D 프린팅)"],
        "B고등학교": ["프로그램1 (제과)", "프로그램2 (제빵)", "프로그램3 (바리스타)"],
        "C고등학교": ["프로그램1 (드론)", "프로그램2 (VR 체험)", "프로그램3 (게임개발)"],
    },
    "2월 3일": {
        "A고등학교": ["프로그램1 (AI 코딩)", "프로그램2 (로봇)", "프로그램3 (3D 프린팅)"],
        "B고등학교": ["프로그램1 (제과)", "프로그램2 (제빵)", "프로그램3 (바리스타)"],
        "C고등학교": ["프로그램1 (드론)", "프로그램2 (VR 체험)", "프로그램3 (게임개발)"],
    },
    "2월 4일": {
        "A고등학교": ["프로그램1 (심화 코딩)", "프로그램2 (로봇 축구)"],
        "B고등학교": ["프로그램1 (설탕 공예)", "프로그램2 (케이크)"],
        "C고등학교": ["프로그램1 (드론 레이싱)", "프로그램2 (메타버스)"],
    }
}

COLUMNS = ["신청일시", "이름", "연락처", "소속학교", "학년", "반", "체험날짜", "학교", "프로그램"]

# --- 2. 데이터 처리 함수 (구글 시트용) ---

def load_data():
    """구글 시트에서 모든 데이터를 읽어와 DataFrame으로 반환"""
    try:
        data = sheet.get_all_values()
        # 데이터가 헤더만 있거나 비어있을 경우
        if len(data) <= 1: 
            return pd.DataFrame(columns=COLUMNS)
        # 첫 번째 줄은 헤더로 쓰고 나머지만 데이터로 변환
        return pd.DataFrame(data[1:], columns=data[0])
    except:
        return pd.DataFrame(columns=COLUMNS)

def save_data(new_entry_list):
    """구글 시트에 한 줄 추가 (리스트 형태)"""
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

# --- 3. UI 구성 ---

st.set_page_config(page_title="체험 프로그램 신청", page_icon="🏫")

st.title("🏫 중학교 직업체험 신청")

st.markdown("""
### 📢 [신청 전 유의사항]
1. **날짜를 먼저 선택**해야 해당 일자의 학교 및 프로그램 목록이 나타납니다.
2. **같은 날짜**에는 **1개의 프로그램**만 신청할 수 있습니다.
3. 이전에 신청했던 프로그램과 **동일한 프로그램은 중복 신청이 불가능**합니다.
4. 각 프로그램은 **선착순 20명** 마감입니다.
5. 본인 확인을 위해 **이름과 연락처를 정확하게** 입력해주세요.
""")

st.info("""
**🔒 [개인정보 수집 및 이용 안내]** 본 신청 페이지에서 수집하는 개인정보(이름, 연락처, 학교, 학년, 반)는 **'중학교 직업체험 활동' 운영 및 관리 목적**으로만 사용됩니다.
신청하기 버튼을 누르시면 위 내용에 동의하는 것으로 간주됩니다.
""")

st.markdown("---")

with st.form("application_form"):
    st.subheader("1. 학생 정보 입력")
    
    col1, col2 = st.columns(2)
    with col1:
        name_input = st.text_input("이름", placeholder="예: 홍길동")
    with col2:
        phone_input = st.text_input(
            "연락처 (숫자만 입력)", 
            placeholder="01012345678", 
            max_chars=11,
            help="하이픈(-) 없이 숫자 11자리만 입력해주세요."
        )

    col3, col4, col5 = st.columns(3)
    with col3:
        school_input = st.text_input("소속 중학교", placeholder="예: 한국중")
    with col4:
        grade_input = st.selectbox("학년", ["1학년", "2학년", "3학년"])
    with col5:
        class_input = st.text_input("반", placeholder="숫자만 입력 (예: 3)")

    st.markdown("---")
    st.subheader("2. 체험 프로그램 선택")
    
    selected_date = st.selectbox("날짜 선택", list(SCHEDULE.keys()))
    available_schools = list(SCHEDULE[selected_date].keys())
    selected_school = st.selectbox("체험할 고등학교 선택", available_schools)
    
    raw_programs = SCHEDULE[selected_date][selected_school]
    display_options = []
    display_map = {}

    for prog in raw_programs:
        current_count = get_program_count(selected_date, selected_school, prog)
        if current_count >= MAX_CAPACITY:
            display_text = f"🚫 [마감] {prog}"
        else:
            display_text = f"{prog} (신청현황: {current_count}/{MAX_CAPACITY}명)"
        display_options.append(display_text)
        display_map[display_text] = prog

    selected_display = st.selectbox("프로그램 선택", display_options)
    real_program_name = display_map[selected_display]

    st.markdown("---")
    submitted = st.form_submit_button("위 내용으로 신청하기", use_container_width=True)

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

            final_count = get_program_count(selected_date, selected_school, real_program_name)
            if final_count >= MAX_CAPACITY:
                st.error("신청하는 도중에 마감되었습니다. 😭")
            else:
                user_history = get_user_history(name_input, formatted_phone)
                
                date_dup = pd.DataFrame()
                prog_dup = pd.DataFrame()
                
                if not user_history.empty:
                    date_dup = user_history[user_history['체험날짜'] == selected_date]
                    prog_dup = user_history[user_history['프로그램'] == real_program_name]
                
                if not date_dup.empty:
                    st.error(f"🚫 '{selected_date}'에는 이미 신청 내역이 있습니다.")
                elif not prog_dup.empty:
                    st.error(f"🚫 '{real_program_name}' 프로그램은 이미 신청하셨습니다.")
                else:
                    # 5. 구글 시트에 저장할 리스트 생성 (순서 중요!)
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

# 관리자 메뉴는 이제 필요 없어서 삭제하거나, 시트 링크만 제공
with st.expander("관리자 메뉴"):
    st.write("데이터는 구글 스프레드시트에 실시간으로 저장되고 있습니다.")
    if 'SHEET_URL' in locals():
        st.link_button("📊 구글 시트로 이동하여 명단 확인하기", SHEET_URL)
