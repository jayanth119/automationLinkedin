from typing import List, TypedDict


# =====================
# STATE DEFINITION
# =====================
class ExtractState(TypedDict):
    url: str
    text: str
    images: List[str]
    documents: List[str]
    videos: List[str]
    notes: str



