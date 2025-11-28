import os
import asyncio
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.functions import KernelArguments

class Analyst:
    def __init__(self):
        """Initializes the Semantic Kernel ONCE."""
        self.kernel = sk.Kernel()
        
        # Load Env Vars
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")

        if not all([self.deployment, self.endpoint, self.api_key]):
            raise ValueError("CRITICAL: Missing Azure OpenAI environment variables.")

        self.service_id = "analyst"
        
        # Add Service (One-time setup)
        self.kernel.add_service(
            AzureChatCompletion(
                service_id=self.service_id,
                deployment_name=self.deployment,
                endpoint=self.endpoint,
                api_key=self.api_key
            )
        )
        
        # Configure Function
        self._configure_function()

    def _configure_function(self):
        """Sets up the persona and high-temp settings."""
        # High temperature (0.8) to drive stochastic proposal generation
        req_settings = AzureChatPromptExecutionSettings(service_id=self.service_id)
        req_settings.temperature = 0.8
        req_settings.top_p = 0.95

        prompt_template = """
        SYSTEM ROLE:
        You are a Senior Python Engineer. You act as 'The Analyst'.
        Your goal is to write functional, efficient Python code to solve the user's problem.
        Do not explain the code excessively. Provide the code block clearly.
        
        USER REQUEST:
        {{$input}}
        """

        self.analyst_function = self.kernel.add_function(
            plugin_name="AnalystPlugin",
            function_name="generate_code",
            prompt=prompt_template,
            prompt_execution_settings=req_settings
        )

    async def generate(self, user_request: str) -> str:
        """Invokes the kernel with the user request."""
        print(f"--- Analyst (High Temp) Generating Solution for: '{user_request}' ---")
        
        result = await self.kernel.invoke(
            self.analyst_function,
            KernelArguments(input=user_request)
        )
        return str(result)

# --- BACKWARD COMPATIBILITY WRAPPER ---
# This ensures run_day4.py and run_day5.py still work without modification.
_global_analyst = None

async def generate_code(user_request: str):
    global _global_analyst
    if _global_analyst is None:
        _global_analyst = Analyst()
    return await _global_analyst.generate(user_request)

if __name__ == "__main__":
    # Test the class directly
    analyst = Analyst()
    print(asyncio.run(analyst.generate("Write a hello world function.")))