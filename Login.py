import streamlit as st

# 원래 root 디렉토리에 있던 메인 실행화일을 다른 이름을 변경하여 pages 폴더 안으로 이동시키고
# 이 sidebar_page디자인.py 파일을 root 디렉토리에 복사한 후 이전 main 실행 화일의 이름으로 변경해야 한다.

# Create pages
login_page = st.Page("pages/Login_page.py", title="로그인 페이지", icon=":material/domain:")
page_1 = st.Page("pages/1 Sim_orientation.py", title="1 Sim_orientation", icon=":material/domain:")
page_2 = st.Page("pages/2 Memory Training.py", title="2 Memory Training", icon=":material/domain:")
page_3 = st.Page("pages/3 SHT.py", title="3 SHT", icon=":material/domain:")
page_4 = st.Page("pages/4 EMT.py", title="4 EMT", icon=":material/domain:")
page_5 = st.Page("pages/5 LHT.py", title="5 LHT", icon=":material/domain:")
page_6 = st.Page("pages/6 Hemoclip.py", title="6 Hemoclip", icon=":material/domain:")
page_7 = st.Page("pages/7 Injection.py", title="7 Injection", icon=":material/domain:")
page_8 = st.Page("pages/8 APC.py", title="8 APC", icon=":material/domain:")
page_9 = st.Page("pages/9 NexPowder.py", title="9 NexPowder", icon=":material/domain:")
page_10 = st.Page("pages/10 EVL.py", title="10 EVL", icon=":material/domain:")
page_11 = st.Page("pages/11 PEG.py", title="11 PEG", icon=":material/domain:")

# position에 따라 Sim_orientation 페이지 표시 여부 결정
allowed_positions = ["Staff", "F1", "F2", "R3", "Student"]
current_position = st.session_state.get('position', '')

# Basic Course 페이지 리스트 구성
basic_course_pages = [page_1, page_2, page_3, page_4]  # 기본적으로 page_2, page_3, page_4 포함

# Set up navigation with sections
pg = st.navigation(
    {
        "로그인 페이지": [login_page],
        "Basic Course": basic_course_pages,
        "Advanced Course": [page_5, page_6, page_7, page_8, page_9, page_10, page_11],
    },
)

# Set default page configuration
st.set_page_config(
    page_title="AMC GIC Simulator Training",
    page_icon="🤖",
)

# Run the selected page
pg.run() 