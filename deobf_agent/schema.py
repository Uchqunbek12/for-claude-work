"""LLM javobining sxemasi (tuzilmasi).

Nima uchun sxema kerak: agar LLM'dan "erkin matn" so'rasak, javobni dastur
o'qishi qiyin bo'ladi (kod qayerda, izoh qayerda?). Claude API'ning "structured
outputs" imkoniyati bilan javob AYNAN shu tuzilmada keladi va pydantic uni
avtomatik tekshiradi. Offline rejim ham aynan shu tuzilmani qaytaradi, shuning
uchun qolgan modullar (hisobot, Web UI) natija qayerdan kelganini bilishi shart emas.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Block(BaseModel):
    title: str = Field(description="Short human-readable name of the block, in the requested language")
    original_lines: str = Field(description="Line range in the numbered input pseudocode, e.g. '12-18'")
    original_code: str = Field(description="The obfuscated pseudocode fragment this block covers (verbatim, may be shortened with ...)")
    simplified_code: str = Field(description="The equivalent fragment of the clean C code")
    explanation: str = Field(description="Explanation for an analyst: what this block does and what obfuscation was removed, in the requested language")
    simple: str = Field(description="The same block explained for a complete beginner with an everyday-life analogy (no jargon), 1-3 sentences, in the requested language")


class Rename(BaseModel):
    old: str = Field(description="Original identifier from the pseudocode (e.g. v3, a1, param_1, local_10)")
    new: str = Field(description="New meaningful name used in c_code")
    reason: str = Field(description="Why this name was chosen, in the requested language")


class DeobfResult(BaseModel):
    function_name: str = Field(description="Original function name, exactly as in the input")
    suggested_name: str = Field(description="Suggested meaningful name for the function (snake_case)")
    summary: str = Field(description="2-5 sentences for an analyst: what the function does, in the requested language")
    simple_summary: str = Field(description="3-6 sentences explaining the whole function to a person with no computer knowledge, using everyday analogies (market, kitchen, recipe), in the requested language")
    techniques: list[str] = Field(description="Obfuscation techniques found, using ids: mba, opaque_predicate, "
                                              "control_flow_flattening, encoded_strings, encoded_constants, dead_code, other")
    c_code: str = Field(description="Complete, compilable, simplified C function. MUST keep the original function "
                                    "name and the exact parameter list (count, order, types). Locals may be renamed.")
    blocks: list[Block] = Field(description="Block-by-block mapping from obfuscated pseudocode to clean code, in execution order")
    renames: list[Rename] = Field(description="Identifier renames applied in c_code")
    confidence: Literal["low", "medium", "high"] = Field(description="Confidence that c_code is semantically equivalent")
    notes: str = Field(description="Caveats, assumptions or uncertain parts, in the requested language (empty if none)")
