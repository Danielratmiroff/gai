"""
Gemini API client implementation using LangChain.
"""

from typing import Optional, List, Dict, Any
from gai_tool.src.utils import validate_messages
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.callbacks import CallbackManager
from langchain_core.outputs import ChatResult
import os


class GeminiClient:
    """A client for interacting with Google's Gemini model via LangChain."""

    def __init__(
        self,
        model: str = "gemini-pro",
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40,
        max_output_tokens: int = 8000,
        callback_manager: Optional[CallbackManager] = None,
    ):
        """
        Initialize the Gemini client.

        Args:
            model: The name of the Gemini model to use
            temperature: Controls randomness in responses
            top_p: Nucleus sampling parameter
            top_k: Number of tokens to consider for sampling
            max_output_tokens: Maximum number of tokens to generate
            callback_manager: Optional callback manager for logging and monitoring
        """
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google API key must be provided through the GOOGLE_API_KEY environment variable"
            )

        self.llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=self.api_key,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_output_tokens,
            callback_manager=callback_manager,
        )

    def get_chat_completion(
        self,
        user_message: List[Dict[str, str]],
        # system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Chat method.

        Args:
            user_message: The user's message to send to the model
            system_prompt: Optional system prompt to set context
            **kwargs: Additional keyword arguments to pass to the model

        Returns:
            ChatResult containing the model's response
        """
        # messages = []
        # if system_prompt:
        #     messages.append(SystemMessage(content=system_prompt))
        # messages.append(HumanMessage(content=user_message))

        validate_messages(messages=user_message)

        try:
            response = self.llm.invoke(
                user_message,
                **kwargs,
            )
            return response.content
        except Exception as e:
            raise Exception(f"Error while communicating with Gemini: {str(e)}")
