import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import re
from datetime import datetime
import pytz

# --- 1. 설정 및 구글 시트 연결 ---

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

# [수정 전] "A고등학교": ["프로그램1", "프로그램2"]
# [수정 후] 아래와 같이 변경

SCHEDULE = {
    "2월 1일": {
        "A고등학교": [
            {"name": "프로그램1 (AI 코딩)", "limit": 25},  # 25명
            {"name": "프로그램2 (로봇)", "limit": 15},     # 15명
            {"name": "프로그램3 (3D 프린팅)", "limit": 20} # 20명
        ],
        "B고등학교": [
            {"name": "프로그램1 (제과)", "limit": 12},     # 실습실이 작음
            {"name": "프로그램2 (제빵)", "limit": 12},
            {"name": "프로그램3 (바리스타)", "limit": 10}
        ],
        "C고등학교": [
            {"name": "프로그램1 (드론)", "limit": 30},     # 강당 사용
            {"name": "프로그램2 (VR 체험)", "limit": 20},
            {"name": "프로그램3 (게임개발)", "limit": 20}
        ],
    },
    # ... (다른 날짜들도 위와 같은 형식으로 수정해주셔야 합니다) ...
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
    },
    # (나머지 날짜도 동일한 규칙으로 작성해주세요)
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
# --- 🕒 [오픈런 설정] 신청 시작 시간 설정 ---
# 선생님! 아래 숫자를 원하는 날짜/시간으로 바꾸세요 (예: 2024년 3월 4일 9시 0분 0초)
OPEN_YEAR = 2026
OPEN_MONTH = 1
OPEN_DAY = 27
OPEN_HOUR = 11
OPEN_MINUTE = 0

# 한국 시간 설정 (건드리지 마세요)
kst = pytz.timezone('Asia/Seoul')
now_kst = datetime.now(kst)
open_time = datetime(OPEN_YEAR, OPEN_MONTH, OPEN_DAY, OPEN_HOUR, OPEN_MINUTE, 0, tzinfo=kst)

# 시간이 안 됐으면 문 닫아걸기
if now_kst < open_time:
    st.title("🚧 신청 기간이 아닙니다")
    st.error(f"📢 신청 시작 시간: {open_time.strftime('%Y년 %m월 %d일 %H시 %M분')}")
    st.info(f"🕰️ 현재 시간: {now_kst.strftime('%H시 %M분 %S초')}")
    
    st.write("시간이 되면 아래 [새로고침] 버튼을 눌러주세요.")
    if st.button("🔄 새로고침 (시간 확인)"):
        st.rerun()
        
    st.stop() # 🛑 여기서 프로그램 실행을 멈춥니다! (아래 신청폼이 안 보임)
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

# ... (위쪽 학생 정보 입력 코드는 그대로 두세요) ...

    st.markdown("---")
    st.subheader("2. 체험 프로그램 선택")
    
    selected_date = st.selectbox("날짜 선택", list(SCHEDULE.keys()))
    available_schools = list(SCHEDULE[selected_date].keys())
    selected_school = st.selectbox("체험할 고등학교 선택", available_schools)
    
    # [수정된 부분] 선택된 학교의 프로그램 목록(이름+정원)을 가져옵니다.
    raw_programs_data = SCHEDULE[selected_date][selected_school]
    
    display_options = []
    display_map = {} # 화면에 보이는 이름 -> 실제 데이터 연결
    limit_map = {}   # 프로그램 이름 -> 정원 수 연결

    # 반복문을 돌면서 마감 여부를 확인합니다.
    for item in raw_programs_data:
        prog_name = item["name"]   # 프로그램 이름
        prog_limit = item["limit"] # 프로그램별 정원 (15명, 25명 등)
        
        # 현재 신청된 인원 확인
        current_count = get_program_count(selected_date, selected_school, prog_name)
        
        # 마감 여부 체크 (20명 고정이 아니라 prog_limit 사용)
        if current_count >= prog_limit:
            display_text = f"🚫 [마감] {prog_name}"
        else:
            display_text = f"{prog_name} (신청: {current_count}/{prog_limit}명)"
        
        display_options.append(display_text)
        display_map[display_text] = prog_name
        limit_map[prog_name] = prog_limit # 나중에 신청할 때 쓰려고 저장

    selected_display = st.selectbox("프로그램 선택", display_options)
    real_program_name = display_map[selected_display]
    
    # 선택한 프로그램의 정원을 가져옵니다.
    current_limit = limit_map[real_program_name]

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

            # [수정된 부분] 최종 저장 전, 다시 한번 해당 프로그램의 정원(current_limit)으로 마감 체크
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
                    
# 관리자 메뉴는 이제 필요 없어서 삭제하거나, 시트 링크만 제공
with st.expander("관리자 메뉴"):
    st.write("데이터는 구글 스프레드시트에 실시간으로 저장되고 있습니다.")
    if 'SHEET_URL' in locals():
        st.link_button("📊 구글 시트로 이동하여 명단 확인하기", SHEET_URL)


