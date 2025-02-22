# Similar session state initialization and video player logic
if 'show_sht_video' not in st.session_state:
    st.session_state.show_sht_video = False

# Video player button and display logic
if st.button("동영상 시청"):
    st.session_state.show_sht_video = not st.session_state.show_sht_video
    # ... log creation code ...

if st.session_state.show_sht_video:
    # ... video player HTML ... 