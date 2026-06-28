import json
import logging
import google.generativeai as genai
from pydantic import BaseModel, ValidationError
from typing import Type, TypeVar, Optional, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class GeminiService:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not set.")
        else:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
        self.fast_model_name = settings.GEMINI_MODEL_FAST
        self.reasoning_model_name = settings.GEMINI_MODEL_REASONING
        self.default_model_name = settings.GEMINI_MODEL_DEFAULT

    def _get_model(self, model_name: str, response_schema: Optional[Type[BaseModel]] = None) -> genai.GenerativeModel:
        # In this SDK, we set response_mime_type to json.
        # We can also pass response_schema if supported, but to be robust, we rely on prompt + mime_type
        # and validate with pydantic manually.
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
        return genai.GenerativeModel(model_name=model_name, generation_config=generation_config)

    def extract_structured(self, prompt: str, schema: Type[T], require_reasoning: bool = False, trace_logger=None) -> T:
        """
        Extract structured data using Gemini with a 1-retry repair loop on validation failure.
        """
        model_name = self.reasoning_model_name if require_reasoning else self.fast_model_name
        
        try:
            if trace_logger:
                trace_logger.log("gemini_extraction_started", {"model": model_name})
            
            resp = self._call_and_parse(prompt, schema, model_name, trace_logger)
            
            if trace_logger:
                trace_logger.log("gemini_extraction_completed")
            return resp
            
        except ValidationError as e:
            logger.warning(f"Validation failed on first attempt. Attempting repair with reasoning model. Error: {str(e)}")
            if trace_logger:
                trace_logger.log("validation_failed", {"errors": e.errors()})
                trace_logger.log("repair_attempted")
                
            # Try repair loop, forcing the reasoning model for better capability
            repair_prompt = (
                f"You previously generated a JSON response that failed validation.\n"
                f"Original Prompt: {prompt}\n\n"
                f"Validation Errors:\n{e.json()}\n\n"
                f"Please correct the JSON to strictly adhere to the required schema."
            )
            try:
                resp = self._call_and_parse(repair_prompt, schema, self.reasoning_model_name, trace_logger)
                if trace_logger:
                    trace_logger.log("gemini_extraction_completed", {"repaired": True})
                return resp
            except ValidationError as final_e:
                logger.error(f"Repair attempt failed. Error: {str(final_e)}")
                if trace_logger:
                    trace_logger.log("validation_failed", {"errors": final_e.errors(), "fatal": True})
                raise ValueError(f"Failed to extract structured data matching schema: {str(final_e)}")
        except Exception as ex:
            logger.error(f"Gemini API error: {str(ex)}")
            raise

    def _call_and_parse(self, prompt: str, schema: Type[T], model_name: str, trace_logger=None) -> T:
        schema_json = schema.model_json_schema()
        full_prompt = (
            f"{prompt}\n\n"
            f"You MUST return a raw JSON object that conforms exactly to this JSON schema:\n"
            f"{json.dumps(schema_json, indent=2)}\n"
            f"Do not include markdown blocks like ```json."
        )
        
        model = self._get_model(model_name)
        response = model.generate_content(full_prompt)
        text_resp = response.text
        
        # Strip potential markdown formatting if model ignored instruction
        if text_resp.startswith("```json"):
            text_resp = text_resp[7:]
        if text_resp.startswith("```"):
            text_resp = text_resp[3:]
        if text_resp.endswith("```"):
            text_resp = text_resp[:-3]
            
        text_resp = text_resp.strip()
        
        if trace_logger:
            trace_logger.log("validation_started")
            
        validated = schema.model_validate_json(text_resp)
        
        if trace_logger:
            trace_logger.log("validation_succeeded")
            
        return validated

gemini_service = GeminiService()
