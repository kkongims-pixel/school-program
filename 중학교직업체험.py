import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import re
from datetime import datetime
import pytz
import time
import random  # 동시 접속 분산을 위한 랜덤 모듈

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
    "6월 13일(토요일)": {
        "전자공고": [
            {"name": "프로그램1 (미래 자동차)", "limit": 10},     
            {"name": "프로그램2 (자율주행 자동차)", "limit": 10},
            {"name": "프로그램3 (모빌리티 랩)", "limit": 10}
        ],
    },
    "6월 17일(수요일)": {
        "스마트 캠퍼스": [
            {"name": "프로그램 (스마트시티 크리에이터)", "limit": 20}
        ],
    },
    "7월 11일(토요일)": {
        "자연과학고": [
            {"name": "프로그램1 (AI 플로리스트)", "limit": 10},
            {"name": "프로그램2 (미래의 베이커리공작소)", "limit": 10},
            {"name": "프로그램3 (AI 반려동물 영양설계사)", "limit": 10},
            {"name": "프로그램4 (K-디저트 셰프)", "limit": 10}
        ],
        "전남공고": [
            {"name": "프로그램1 (첨단 드론 조종사)", "limit": 10}, 
            {"name": "프로그램2 (스마트 가구 디자이너)", "limit": 10},     
        ]
    }
}

COLUMNS = ["신청일시", "이름", "연락처", "소속학교", "학년", "반", "체험날짜", "학교", "프로그램", "접수상태"]

# --------------------------------------------------------------------------
# 3. 데이터 처리 함수 (ttl=30 설정으로 구글 시트 부하 감소)
# --------------------------------------------------------------------------
@st.cache_data(ttl=30) # 🔴 30초 동안은 캐시된 데이터를 사용하여 API 요청 횟수를 줄입니다.
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
# 4. [오픈런] 시간 통제 설정
# --------------------------------------------------------------------------
OPEN_YEAR, OPEN_MONTH, OPEN_DAY = 2026, 4, 7
OPEN_HOUR, OPEN_MINUTE = 11, 20

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

st.info("**🔒 [개인정보 수집 안내]** 본 신청 페이지에서 수집하는 개인정보는 **운영 및 관리 목적**으로만 사용됩니다.")
st.markdown("---")

# 풍선 효과 애니메이션
if st.session_state.get('show_balloons', False):
    st.balloons()
    st.session_state['show_balloons'] = False

# =========================================================
# 1단계: 학생 정보 입력 
# =========================================================
st.subheader("1. 학생 정보 입력")
r1c1, r1c2 = st.columns(2)
with r1c1: name_input = st.text_input("이름 (예: 홍길동)", key="k_name")
with r1c2: phone_input = st.text_input("연락처 (숫자만 입력)", max_chars=11, key="k_phone")

r2c1, r2c2, r2c3 = st.columns(3)
with r2c1: school_input = st.text_input("중학교 (예: OO중)", key="k_school")
with r2c2: grade_input = st.selectbox("학년", ["1학년", "2학년", "3학년"], index=None, placeholder="선택", key="k_grade")
with r2c3: class_input = st.text_input("반 (숫자만 입력)", key="k_class")
st.markdown("---")

# =========================================================
# 2단계: 체험 프로그램 선택 
# =========================================================
st.subheader("2. 체험 프로그램 선택")
selected_date = st.selectbox("날짜 선택", list(SCHEDULE.keys()), index=None, placeholder="📅 날짜를 선택하세요", key="k_date")
available_schools = list(SCHEDULE[selected_date].keys()) if selected_date else []
selected_school = st.selectbox("체험할 고등학교 선택", available_schools, index=None, placeholder="🏫 고등학교를 선택하세요", key="k_highschool")

display_options, display_map, limit_map = [], {}, {}

if selected_date and selected_school:
    cached_df = load_data_cached()
    for item in SCHEDULE[selected_date][selected_school]:
        prog_name, prog_limit = item["name"], item["limit"]
        current_count = count_in_dataframe(cached_df, selected_date, selected_school, prog_name)
        
        if current_count >= (prog_limit + RESERVE_LIMIT):
            display_text = f"🚫 [마감] {prog_name} (정원 및 예비 마감)"
        elif current_count >= prog_limit:
            res_num = current_count - prog_limit + 1
            display_text = f"⚠️ [예비신청 가능] {prog_name} (현재 예비 {res_num}/{RESERVE_LIMIT}번)"
        else:
            display_text = f"✅ [정원신청 가능] {prog_name} (신청현황: {current_count}/{prog_limit}명)"
        
        display_options.append(display_text)
        display_map[display_text], limit_map[prog_name] = prog_name, prog_limit 

selected_display = st.selectbox("프로그램 선택", display_options, index=None, placeholder="💡 프로그램을 선택하세요", key="k_program")
st.markdown("---")

# =========================================================
# 3단계: 최종 신청 (🔴 랜덤 딜레이 대기열 및 노란색 완료 박스 적용)
# =========================================================
# 성공 시 노란색 박스를 보여줍니다.
if st.session_state.get('show_complete_msg', False):
    st.markdown(st.session_state['complete_msg_html'], unsafe_allow_html=True)
    st.session_state['show_complete_msg'] = False

else:
    if st.button("🚀 신청하기", use_container_width=True, type="primary"):
        if not name_input or not name_input.strip() or not phone_input or not phone_input.strip() or not school_input or not school_input.strip() or not grade_input or not class_input or not class_input.strip():
            st.error("❌ 학생 정보를 빈칸 없이 모두 입력해주세요.")
        elif not selected_date or not selected_school or not selected_display:
            st.error("❌ 날짜, 고등학교, 프로그램을 모두 선택해주세요.")
        elif not phone_input.isdigit() or len(phone_input) != 11 or not phone_input.startswith("010"):
            st.warning("❌ 연락처는 010으로 시작하는 숫자 11자리여야 합니다.")
        elif "[마감]" in selected_display:
            st.error("❌ 이미 예비 인원까지 모두 마감되었습니다.")
        else:
            real_program_name = display_map[selected_display]
            current_limit = limit_map[real_program_name]
            formatted_phone = format_phone_number(phone_input.strip())
            clean_name, clean_school, clean_class = name_input.strip(), school_input.strip(), class_input.strip()
            
            # 🔴 [마법의 대기열 시스템] 
            with st.spinner("서버에 안전하게 연결 중입니다. 창을 닫지 말고 잠시만 기다려주세요... 🚀"):
                success = False
                error_message = ""
                
                # 최대 5번까지 구글 시트에 끈질기게 요청합니다.
                for attempt in range(5):
                    try:
                        fresh_df = load_data_fresh() 
                        final_count = count_in_dataframe(fresh_df, selected_date, selected_school, real_program_name)
                        
                        if final_count >= (current_limit + RESERVE_LIMIT):
                            error_message = "😭 아쉽지만 예비 인원까지 모두 마감되었습니다."
                            break 
                            
                        user_history = get_user_history(fresh_df, clean_name, formatted_phone)
                        if not user_history.empty:
                            if not user_history[user_history['체험날짜'] == selected_date].empty:
                                error_message = f"🚫 '{selected_date}'에는 이미 신청 내역이 있습니다."
                                break
                            elif not user_history[user_history['프로그램'] == real_program_name].empty:
                                error_message = f"🚫 '{real_program_name}' 프로그램은 이미 신청하셨습니다."
                                break
                        
                        status_text = str(final_count + 1) if final_count < current_limit else f"예비 {final_count - current_limit + 1}"
                        
                        new_entry_list = [
                            datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S"),
                            clean_name, formatted_phone, clean_school, grade_input, clean_class,
                            selected_date, selected_school, real_program_name, status_text  
                        ]
                        save_data(new_entry_list)
                        success = True
                        break 
                        
                    except Exception as e:
                        # 🔴 핵심: 에러 발생 시 1.0초 ~ 3.5초 사이의 무작위 시간 대기 후 재시도
                        time.sleep(random.uniform(1.0, 3.5)) 
                
            # 결과 처리 및 노란색 메시지 박스 생성
            if success:
                if final_count < current_limit:
                    st.session_state['show_balloons'] = True
                    st.session_state['complete_msg_html'] = f"""
                    <div style="background-color: #FFE066; padding: 20px; border-radius: 10px; text-align: center; color: #333; margin-bottom: 20px; border: 2px solid #F4C430;">
                        <h3 style="margin: 0; font-weight: bold; color: #000;">✅ 신청이 완료되었습니다!</h3>
                        <p style="margin: 10px 0 0 0; font-size: 16px;">({real_program_name})</p>
                    </div>"""
                else:
                    st.session_state['complete_msg_html'] = f"""
                    <div style="background-color: #FFE066; padding: 20px; border-radius: 10px; text-align: center; color: #333; margin-bottom: 20px; border: 2px solid #F4C430;">
                        <h3 style="margin: 0; font-weight: bold; color: #000;">⚠️ 예비 {final_count - current_limit + 1}번으로 접수되었습니다.</h3>
                        <p style="margin: 10px 0 0 0; font-size: 16px;">({real_program_name})</p>
                    </div>"""
                
                st.session_state['show_complete_msg'] = True
                # 입력된 모든 값을 초기화합니다.
                for key in ["k_name", "k_phone", "k_school", "k_grade", "k_class", "k_date", "k_highschool", "k_program"]:
                    if key in st.session_state: del st.session_state[key]
                st.rerun()
                
            elif error_message:
                st.error(error_message)
                load_data_cached.clear()
            else:
                st.error("🚦 대기 인원이 너무 많습니다. 5~10초 뒤에 다시 [신청하기]를 눌러주세요!")

with st.expander("관리자 메뉴"):
    st.write("데이터는 구글 스프레드시트에 실시간으로 저장되고 있습니다.")
    if 'SHEET_URL' in locals():
        st.link_button("📊 구글 시트로 이동하여 명단 확인하기", SHEET_URL)
