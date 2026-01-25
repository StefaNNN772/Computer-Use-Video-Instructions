import React from 'react';

interface Props {
  status: string;
  message: string;
  error?: string | null;
}

const StatusIndicator: React.FC<Props> = ({ status, message, error }) => {
  const getStatusInfo = () => {
    switch (status) {
      case 'pending':
        return { icon: '⏳', color:  '#ffc107', text: 'Waiting...' };
      case 'generating_plan':
        return { icon: '📝', color: '#17a2b8', text: 'Generating plan...' };
      case 'plan_ready':
        return { icon: '✅', color: '#28a745', text: 'Plan ready' };
      case 'executing': 
        return { icon: '🤖', color: '#17a2b8', text: 'Executing step...' };
      case 'recording':
        return { icon: '🎥', color:  '#dc3545', text: 'Recording...' };
      case 'converting':
        return { icon: '🔄', color: '#6c757d', text: 'Converting video...' };
      case 'completed':
        return { icon: '🎉', color: '#28a745', text: 'Completed!' };
      case 'failed':
        return { icon: '❌', color: '#dc3545', text: 'Error' };
      default:
        return { icon: '•', color: '#6c757d', text: status };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <div className="status-indicator">
      <div 
        className="status-badge"
        style={{ backgroundColor: `${statusInfo.color}22`, borderColor: statusInfo.color }}
      >
        <span className="status-icon">{statusInfo.icon}</span>
        <span className="status-text" style={{ color: statusInfo.color }}>
          {statusInfo.text}
        </span>
      </div>
      
      {message && status !== 'completed' && status !== 'failed' && (
        <p className="status-message">{message}</p>
      )}
      
      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );
};

export default StatusIndicator;