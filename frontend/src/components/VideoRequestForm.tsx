import React, { useState } from 'react';

interface Props {
  onSubmit: (instruction: string) => void;
  isLoading: boolean;
}

const VideoRequestForm: React.FC<Props> = ({ onSubmit, isLoading }) => {
  const [instruction, setInstruction] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (instruction.trim()) {
      onSubmit(instruction.trim());
    }
  };

  const examples = [
    "Napravi C# konzolnu aplikaciju u Visual Studio koja ispisuje Hello World",
    "Otvori Notepad, napisi Hello World i sacuvaj fajl",
    "Otvori Chrome i idi na google.com"
  ];

  return (
    <div className="form-section">
      <h2>📝 New Video Tutorial</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <label htmlFor="instruction">Describe what you want to be done:</label>
          <textarea
            id="instruction"
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="E.g.: Create a C# console application in Visual Studio that prints Hello World"
            rows={4}
            disabled={isLoading}
          />
        </div>
        
        <div className="examples">
          <span>Examples:</span>
          {examples.map((ex, idx) => (
            <button
              key={idx}
              type="button"
              className="example-btn"
              onClick={() => setInstruction(ex)}
              disabled={isLoading}
            >
              {ex. substring(0, 40)}...
            </button>
          ))}
        </div>
        
        <button 
          type="submit" 
          className="btn btn-primary"
          disabled={isLoading || !instruction.trim()}
        >
          {isLoading ? '⏳ Generating plan...' : '🚀 Generate Plan'}
        </button>
      </form>
    </div>
  );
};

export default VideoRequestForm;