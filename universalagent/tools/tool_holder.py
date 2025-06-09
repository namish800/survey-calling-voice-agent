from typing import Callable, Optional
from livekit.agents import function_tool


class ToolHolder:
    def __init__(self, fnc: Callable, 
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 usage_instructions_llm: str = ""):
        self.fnc = fnc
        if name is None:
            self.name = fnc.__name__
        else:
            self.name = name
        if description is None:
            self.description = fnc.__doc__
        else:
            self.description = description

        self._usage_instructions_llm = usage_instructions_llm


    @property
    def livekit_tool(self):
        return function_tool(
            self.fnc,
            name=self.name,
            description=self.description,
        )

    @property
    def usage_instructions_llm(self):
        return self._usage_instructions_llm
