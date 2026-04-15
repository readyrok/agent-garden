from fastapi import APIRouter, Depends
from api.dependencies import get_prompt_library, get_current_user
from infrastructure.llm.prompt_library import PromptLibrary

router = APIRouter(prefix="/prompts", tags=["Prompts"])


@router.get("")
async def list_prompts(
    current_user: str = Depends(get_current_user),
    prompt_library: PromptLibrary = Depends(get_prompt_library),
):
    return {"templates": prompt_library.list_templates()}