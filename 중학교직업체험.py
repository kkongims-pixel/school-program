import streamlit as st
import pandas as pd
import os
import re 
from datetime import datetime

# --- 1. 설정 및 데이터 정의 ---
MAX_CAPACITY = 20  # 프로그램당 정원

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

DB_FILE = 'applications.csv'
COLUMNS = ["신청일시", "이름", "연락처", "소속학교", "학년", "반", "체험날짜", "학교", "프로그램"]

# --- 2. 함수 정의 ---

def load_data():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame(columns=COLUMNS)
    try:
        df = pd.read_csv(DB_FILE, dtype=str)
        if not all(col in df.columns for col in COLUMNS):
            return pd.DataFrame(columns=COLUMNS)
        return df
    except:
        return pd.DataFrame(columns=COLUMNS)

def save_data(new_entry):
    df = load_data()
    new_df = pd.DataFrame([new_entry])
    if df.empty:
        new_df.to_csv(DB_FILE, index=False)
    else:
        new_df.to_csv(DB_FILE, mode='a', header=False, index=False)

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
    """숫자만 들어온 11자리를 010-XXXX-XXXX 형태로 변환"""
    if len(phone) == 11 and phone.isdigit():
        return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
    return phone

# --- 3. UI 구성 ---

st.set_page_config(page_title="체험 프로그램 신청", page_icon="🏫")

st.title("🏫 중학교 직업체험 신청")

# [수정된 부분] 1. 입력 유의사항
st.markdown("""
### 📢 [신청 전 유의사항]
1. **날짜를 먼저 선택**해야 해당 일자의 학교 및 프로그램 목록이 나타납니다.
2. **같은 날짜**에는 **1개의 프로그램**만 신청할 수 있습니다.
3. 이전에 신청했던 프로그램과 **동일한 프로그램은 중복 신청이 불가능**합니다. (다양한 체험 권장)
4. 각 프로그램은 **선착순 20명** 마감이며, 정원이 차면 신청할 수 없습니다.
5. 본인 확인 및 안내를 위해 **이름과 연락처를 정확하게** 입력해주세요.
""")

# [수정된 부분] 2. 개인정보 수집 및 이용 안내
st.info("""
**🔒 [개인정보 수집 및 이용 안내]** 본 신청 페이지에서 수집하는 개인정보(이름, 연락처, 학교, 학년, 반)는 **'중학교 직업체험 활동' 운영 및 관리 목적**으로만 사용됩니다.
수집된 정보는 프로그램 종료 후 안전하게 파기되며, 이 외의 목적으로 절대 사용되지 않습니다.
**신청하기 버튼을 누르시면 위 내용에 동의하는 것으로 간주됩니다.**
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
    display_map = {}
    display_options = []

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
                    st.error(f"🚫 '{selected_date}'에는 이미 신청 내역이 있어 중복 신청할 수 없습니다.")
                elif not prog_dup.empty:
                    st.error(f"🚫 '{real_program_name}' 프로그램은 이미 신청하셨습니다.")
                else:
                    new_entry = {
                        "신청일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "이름": name_input,
                        "연락처": formatted_phone,
                        "소속학교": school_input,
                        "학년": grade_input,
                        "반": class_input,
                        "체험날짜": selected_date,
                        "학교": selected_school,
                        "프로그램": real_program_name
                    }
                    save_data(new_entry)
                    st.success(f"✅ 신청완료! ({formatted_phone}으로 저장되었습니다)")

# --- 4. 관리자 메뉴 ---
with st.expander("관리자 메뉴 (비밀번호: 없음)"):
    st.write("▼ 실시간 신청 명단 확인")
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, dtype=str)
        st.dataframe(df)
        
        csv_data = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("엑셀(CSV) 다운로드", csv_data, "신청명단.csv", "text/csv")
        
        if st.button("🚨 데이터 전체 초기화"):
            os.remove(DB_FILE)
            st.rerun()
