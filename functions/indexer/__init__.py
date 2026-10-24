from functions.indexer.index_review_flow import register_index_review_handler

# This file is intentionally kept lightweight so the review flow can be registered
# from the main startup sequence without changing the existing indexer logic.

__all__ = ["register_index_review_handler"]
