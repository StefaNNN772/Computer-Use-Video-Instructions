export interface Step {
  id: number;
  action: string;
  target: string;
  value: string | null;
  description: string;
  expected_result: string;
}

export interface TaskPlan {
  original_instruction: string;
  goal: string;
  prerequisites: string[];
  steps: Step[];
  success_criteria: string;
}

export interface JobStatus {
  id: string;
  status: 'pending' | 'generating_plan' | 'plan_ready' | 'executing' | 'recording' | 'converting' | 'completed' | 'failed';
  message: string;
  instruction: string;
  task_plan: TaskPlan | null;
  video_url: string | null;
  video_filename: string | null;
  results: {
    successful_steps: number;
    failed_steps: number;
    total_steps: number;
  } | null;
  error: string | null;
  created_at: string;
}