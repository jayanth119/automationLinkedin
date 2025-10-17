from typing import List, TypedDict


class ExtractState(TypedDict):
    url: str
    text: str
    images: List[str]
    documents: List[str]
    videos: List[str]
    notes: str
    email: str
    password: str
    saved_posts: List[dict]          
    classified_posts: dict           




