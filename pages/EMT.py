# Similar session state initialization and video player logic
if 'show_emt_video' not in st.session_state:
    st.session_state.show_emt_video = False

# Video player button and display logic
if st.button("동영상 시청"):
    st.session_state.show_emt_video = not st.session_state.show_emt_video
    # ... log creation code ...

if st.session_state.show_emt_video:
    # ... video player HTML ... 