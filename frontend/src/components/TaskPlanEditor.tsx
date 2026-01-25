import React, { useState, useEffect } from 'react';
import { TaskPlan, Step } from '../types';

interface Props {
  taskPlan: TaskPlan;
  onSave: (plan:  TaskPlan) => void;
  onExecute: () => void;
  isLoading: boolean;
}

const TaskPlanEditor: React. FC<Props> = ({ taskPlan, onSave, onExecute, isLoading }) => {
  const [plan, setPlan] = useState<TaskPlan>(taskPlan);
  const [editingStep, setEditingStep] = useState<number | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    setPlan(taskPlan);
    setHasChanges(false);
  }, [taskPlan]);

  const updateStep = (index: number, field: keyof Step, value: string) => {
    const newSteps = [...plan.steps];
    newSteps[index] = { ...newSteps[index], [field]: value };
    setPlan({ ...plan, steps: newSteps });
    setHasChanges(true);
  };

  const deleteStep = (index: number) => {
    const newSteps = plan.steps.filter((_, i) => i !== index);
    // Renumber steps
    newSteps.forEach((step, i) => step.id = i + 1);
    setPlan({ ...plan, steps: newSteps });
    setHasChanges(true);
  };

  const addStep = () => {
    const newStep: Step = {
      id:  plan.steps.length + 1,
      action: "click",
      target: "",
      value: null,
      description: "New step description",
      expected_result: "Action executed"
    };
    setPlan({ ...plan, steps: [...plan.steps, newStep] });
    setEditingStep(plan.steps.length);
    setHasChanges(true);
  };

  const handleSave = () => {
    onSave(plan);
    setHasChanges(false);
  };

  const actionOptions = [
    "click", "double_click", "right_click", "type_text",
    "key_press", "key_combination", "scroll", "wait",
    "open_application", "close_application"
  ];

  return (
    <div className="plan-editor">
      <div className="plan-header">
        <h2>📋 Task Plan</h2>
        <div className="plan-meta">
          <p><strong>Goal:</strong> {plan.goal}</p>
          <p><strong>Steps:</strong> {plan.steps.length}</p>
        </div>
      </div>

      <div className="steps-list">
        {plan. steps.map((step, index) => (
          <div key={step.id} className={`step-item ${editingStep === index ? 'editing' : ''}`}>
            <div className="step-header">
              <span className="step-number">{step.id}</span>
              <span className="step-action">{step.action. toUpperCase()}</span>
              <div className="step-actions">
                <button 
                  className="btn-icon"
                  onClick={() => setEditingStep(editingStep === index ? null : index)}
                >
                  ✏️
                </button>
                <button 
                  className="btn-icon btn-danger"
                  onClick={() => deleteStep(index)}
                >
                  🗑️
                </button>
              </div>
            </div>
            
            {editingStep === index ?  (
              <div className="step-edit-form">
                <div className="form-row">
                  <label>Action:</label>
                  <select
                    value={step.action}
                    onChange={(e) => updateStep(index, 'action', e.target.value)}
                  >
                    {actionOptions.map(action => (
                      <option key={action} value={action}>{action}</option>
                    ))}
                  </select>
                </div>
                
                <div className="form-row">
                  <label>Target:</label>
                  <input
                    type="text"
                    value={step.target}
                    onChange={(e) => updateStep(index, 'target', e.target.value)}
                    placeholder="Element the action targets"
                  />
                </div>
                
                <div className="form-row">
                  <label>Value:</label>
                  <input
                    type="text"
                    value={step.value || ''}
                    onChange={(e) => updateStep(index, 'value', e.target.value)}
                    placeholder="Value (for type_text, wait, etc.)"
                  />
                </div>
                
                <div className="form-row">
                  <label>Description:</label>
                  <input
                    type="text"
                    value={step.description}
                    onChange={(e) => updateStep(index, 'description', e.target.value)}
                  />
                </div>
              </div>
            ) : (
              <div className="step-preview">
                <p><strong>Target:</strong> {step.target}</p>
                {step.value && <p><strong>Value:</strong> {step. value}</p>}
                <p className="step-description">{step. description}</p>
              </div>
            )}
          </div>
        ))}
      </div>

      <button className="btn btn-secondary add-step-btn" onClick={addStep}>
        ➕ Add Step
      </button>

      <div className="plan-actions">
        {hasChanges && (
          <button className="btn btn-secondary" onClick={handleSave}>
            💾 Save Changes
          </button>
        )}
        
        <button 
          className="btn btn-primary"
          onClick={onExecute}
          disabled={isLoading || hasChanges}
        >
          {isLoading ? '⏳ Executing...' : '▶️ Create Video'}
        </button>
        
        {hasChanges && (
          <p className="warning-text">⚠️ Save changes before creating the video</p>
        )}
      </div>
    </div>
  );
};

export default TaskPlanEditor;