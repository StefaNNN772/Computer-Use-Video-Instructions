from pydantic import BaseModel
from enum import Enum
from typing import Optional, List


class ActionType(str, Enum):
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    TYPE_TEXT = "type_text"
    KEY_PRESS = "key_press"
    KEY_COMBINATION = "key_combination"
    SCROLL = "scroll"
    WAIT = "wait"
    OPEN_APPLICATION = "open_application"
    CLOSE_APPLICATION = "close_application"
    MOVE_MOUSE = "move_mouse"

class Step(BaseModel):
    id: int
    action: ActionType
    target: str
    value: Optional[str] = None
    description: str
    expected_result:  str
    is_optional: bool = False


class TaskPlan(BaseModel):
    original_instruction: str
    goal: str
    prerequisites: List[str]
    steps: List[Step]
    success_criteria: str

class ParsedInput(BaseModel):
    raw_input: str
    intent: str
    application:  str
    programming_language: Optional[str] = None
    specific_actions: List[str]