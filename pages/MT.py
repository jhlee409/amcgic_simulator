# Similar session state initialization and video player logic
if 'show_mt_video' not in st.session_state:
    st.session_state.show_mt_video = False

# Video player button and display logic
if st.button("동영상 시청"):
    st.session_state.show_mt_video = not st.session_state.show_mt_video
    # ... log creation code ...

if st.session_state.show_mt_video:
    # ... video player HTML ... 