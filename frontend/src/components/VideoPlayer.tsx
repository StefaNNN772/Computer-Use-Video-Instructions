import React from 'react';

interface Props {
  videoUrl:  string;
  videoFilename: string;
  onRegenerate: () => void;
  isLoading: boolean;
  results?:  {
    successful_steps: number;
    failed_steps: number;
    total_steps: number;
  } | null;
}

const API_URL = 'http://localhost:5000';

const VideoPlayer: React.FC<Props> = ({ 
  videoUrl, 
  videoFilename, 
  onRegenerate, 
  isLoading,
  results 
}) => {
  const fullVideoUrl = `${API_URL}${videoUrl}`;
  const downloadUrl = `${API_URL}/api/download/${videoFilename}`;

  return (
    <div className="video-section">
      <h2>🎬 Generate Video</h2>
      
      {results && (
        <div className="results-summary">
          <span className="result-item success">
            ✅ Successful:  {results.successful_steps}
          </span>
          <span className="result-item">
            📊 Total: {results.total_steps}
          </span>
          {results.failed_steps > 0 && (
            <span className="result-item error">
              ❌ Failed: {results.failed_steps}
            </span>
          )}
        </div>
      )}
      
      <div className="video-container">
        <video
          key={videoUrl}
          controls
          autoPlay
          src={fullVideoUrl}
        >
          Your browser does not support the video tag.
        </video>
      </div>
      
      <div className="video-actions">
        <a 
          href={downloadUrl}
          className="btn btn-primary"
          download={videoFilename}
        >
          ⬇️ Download Video
        </a>
        
        <button 
          className="btn btn-secondary"
          onClick={onRegenerate}
          disabled={isLoading}
        >
          {isLoading ? '⏳ Regenerating...' : '🔄 Regenerate'}
        </button>
      </div>
    </div>
  );
};

export default VideoPlayer;