import contextvars
from typing import Callable, Dict, Optional
import os
from guardrails.validator_base import (
    FailResult,
    PassResult,
    ValidationResult,
    Validator,
    register_validator,
)
from rebuff import RebuffSdk


@register_validator(name="guardrails/detect_prompt_injection", data_type="string")
class DetectPromptInjection(Validator):
    """Validates that a value matches a regular expression.

    **Key Properties**

    | Property                      | Description                       |
    | ----------------------------- | --------------------------------- |
    | Supported data types          | `string`                          |
    | Programmatic fix              | Generate a string that matches the regular expression |
    """  # noqa

    def __init__(
        self,
        pinecone_index: str,
        max_heuristic_score: Optional[float] = 0.75,
        max_vector_score: Optional[float] = 0.90,
        max_model_score: Optional[float] = 0.90,
        check_heuristic: Optional[bool] = True,
        check_vector: Optional[bool] = True,
        check_llm: Optional[bool] = True,
        on_fail: Optional[Callable] = None,
    ):
        # todo -> something forces this to be passed as kwargs and therefore xml-ized.
        # match_types = ["fullmatch", "search"]
        super().__init__(
            on_fail=on_fail,
            pinecone_index=pinecone_index,
            max_heuristic_score=max_heuristic_score,
            max_vector_score=max_vector_score,
            max_model_score=max_model_score,
            check_heuristic=check_heuristic,
            check_vector=check_vector,
            check_llm=check_llm,
        )
        self.pinecone_index = pinecone_index
        self.max_heuristic_score = max_heuristic_score
        self.max_vector_score = max_vector_score
        self.max_model_score = max_model_score
        self.check_heuristic = check_heuristic
        self.check_vector = check_vector
        self.check_llm = check_llm

    def validate(self, value: str, metadata: Dict = {}) -> ValidationResult:
        rebuff = None
        try:
            rebuff = self.initialize_rebuff()
        except Exception as e:
            return FailResult(error_message=str(e))

        detection_result = rebuff.detect_injection(
            user_input=value,
            max_heuristic_score=self.max_heuristic_score,
            max_vector_score=self.max_vector_score,
            max_model_score=self.max_model_score,
            check_heuristic=self.check_heuristic,
            check_vector=self.check_vector,
            check_llm=self.check_llm,
        )

        if detection_result.injection_detected:
            # todo -> add more information when Guardrails creates a structured way to add more information to the error outside of the message
            return FailResult(
                error_message="Prompt injection detected."
            )
        return PassResult()

    def initialize_rebuff(self):
        kwargs = self.get_context_vars_kwargs()
        openai_api_key = kwargs.get("OPENAI_API_KEY") or os.environ["OPENAI_API_KEY"]
        pinecone_api_key = kwargs.get("PINECONE_API_KEY") or os.environ["PINECONE_API_KEY"]

        if openai_api_key is None:
            raise ValueError("OPENAI_API_KEY is not set. To use the DetectPromptInjection validator, you must set the OPENAI_API_KEY environment variable or pass it as a keyword argument to the guardrails function.")
        if pinecone_api_key is None:
            raise ValueError("PINECONE_API_KEY is not set. To use the DetectPromptInjection validator, you must set the PINECONE_API_KEY environment variable or pass it as a keyword argument to the guardrails function.")
        
        rebuff = RebuffSdk(
            openai_apikey=openai_api_key,
            pinecone_apikey=pinecone_api_key,
            pinecone_index=self.pinecone_index,
        )

        return rebuff

    def get_context_vars_kwargs(self):
        kwargs = {}
        context_copy = contextvars.copy_context()
        for key, context_var in context_copy.items():
            if key.name == "kwargs" and isinstance(kwargs, dict):
                kwargs = context_var
                break
        return kwargs

    def to_prompt(self, with_keywords: bool = True) -> str:
        return ""
