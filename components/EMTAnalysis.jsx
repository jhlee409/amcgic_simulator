const EMTAnalysis = ({ videoUrl, imageUrls, analysisResults, onSelectEMT }) => {
  return (
    <div className="emt-analysis-container">
      {/* 분석 결과 표시 부분 */}
      <div className="analysis-results">
        {/* ... existing code ... */}
      </div>
      
      {/* Refresh 버튼 추가 */}
      <div className="refresh-button-container" style={{ marginTop: '20px', textAlign: 'center' }}>
        <button 
          className="refresh-button"
          onClick={onSelectEMT}
          style={{
            padding: '10px 20px',
            backgroundColor: '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          새로고침
        </button>
      </div>
    </div>
  );
}; 