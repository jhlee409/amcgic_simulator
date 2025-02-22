# 로그인 상태 확인
name, position = check_login()

if name and position:  # 로그인 성공 시
    # 페이지 선택을 위한 드롭다운 메뉴
    selected_page = st.sidebar.selectbox(
        "시뮬레이터 선택",
        ["Default", "PEG", "APC", "Injection", "Hemoclip"],
        key="page_selection",
        index=0  # Default 페이지의 경우 기본값을 Default로 설정
    )

    # 선택된 페이지로 리다이렉트
    if selected_page != "Default":
        st.switch_page(f"pages/{selected_page}.py")

    # ... rest of the home page code ... 