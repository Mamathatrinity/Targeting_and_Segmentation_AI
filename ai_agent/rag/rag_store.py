"""
RAG Store for CE-TS Modules
Provides static knowledge retrieval for complex modules:
  - Segmentation  (rules, universe summary, filters)
  - Target Lists  (IQVIA, Veeva, export formats)
  - Universe Summary (HCP universe, specialty mapping)

Rules (from PDF pages 395-431):
  - Retrieve ONCE before generation (never inside loops)
  - k=2 results maximum (cost control)
  - Used only for complex modules (segmentation, targeting)
  - NEVER store runtime / live test data in RAG
"""

import os
import json
from typing import List, Dict, Optional

# ---------------------------------------------------------------------------
# Graceful import – FAISS is optional; fall back to keyword search if absent
# ---------------------------------------------------------------------------
try:
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings
    FAISS_AVAILABLE = True
except ImportError:
    try:
        from langchain.vectorstores import FAISS
        from langchain.embeddings import HuggingFaceEmbeddings
        FAISS_AVAILABLE = True
    except ImportError:
        FAISS_AVAILABLE = False

from langchain_core.documents import Document


# ---------------------------------------------------------------------------
# Static CE-TS Knowledge Base
# (domain knowledge about modules in the app – never runtime data)
# ---------------------------------------------------------------------------
CE_TS_KNOWLEDGE = [
    # ── Segmentation module ─────────────────────────────────────────────────
    Document(
        page_content=(
            "Segmentation module: Users create dynamic segments by combining rules. "
            "Rules use AND / OR logic. Each rule can filter by: specialty, sub-specialty, "
            "geography (state, zip, MSA), product affinity score, call history, "
            "decile rank, NPI number, or account type. "
            "Segments are evaluated nightly and updated automatically. "
            "Minimum one rule required to save a segment."
        ),
        metadata={"module": "segmentation", "type": "functionality"}
    ),
    Document(
        page_content=(
            "Segmentation UI elements: 'Add Rule' button opens rule builder panel. "
            "Rule builder has: criterion dropdown, operator dropdown (equals, contains, "
            "greater than, less than, between), value input / multi-select. "
            "Segment name field max 100 chars. Save button is disabled until name + 1 rule exist. "
            "Preview pane shows estimated HCP count in real time."
        ),
        metadata={"module": "segmentation", "type": "ui"}
    ),
    Document(
        page_content=(
            "Segmentation validation rules: Segment name must be unique per user. "
            "Cannot save empty rule (operator with no value). "
            "Date range rules require start <= end. "
            "Numeric fields (decile, score) accept 0-100. "
            "Duplicate NPI entries in the same rule are ignored silently. "
            "Max 20 rules per segment."
        ),
        metadata={"module": "segmentation", "type": "validation"}
    ),

    # ── Universe Summary ─────────────────────────────────────────────────────
    Document(
        page_content=(
            "Universe Summary module: Displays aggregated HCP universe data. "
            "Filters: therapeutic area, geography, specialty, data source (IQVIA / Veeva / custom). "
            "KPI cards show: total HCPs, prescribers, non-prescribers, new entrants this quarter. "
            "Bar chart compares current vs previous period. "
            "Export as CSV or Excel."
        ),
        metadata={"module": "universe_summary", "type": "functionality"}
    ),
    Document(
        page_content=(
            "Universe Summary edge cases: When no data matches filters, 'No data available' banner "
            "is displayed; charts are hidden. Loading spinner appears during data fetch. "
            "Filter combinations with zero results should NOT show an error – only empty state. "
            "Date range cannot exceed 2 years. Exporting >100k records triggers async job with email."
        ),
        metadata={"module": "universe_summary", "type": "edge_cases"}
    ),

    # ── Target Lists ─────────────────────────────────────────────────────────
    Document(
        page_content=(
            "Target Lists module: Manage static or dynamic lists of HCPs for field teams. "
            "List types: Manual (upload CSV), Dynamic (linked to a segment), IQVIA-sourced. "
            "Actions: Create, Edit, Clone, Archive, Export. "
            "Lists can be assigned to territories or individual reps. "
            "Lock status prevents edits until unlocked by admin."
        ),
        metadata={"module": "target_lists", "type": "functionality"}
    ),
    Document(
        page_content=(
            "Target Lists validation: CSV upload must have NPI column. "
            "Max 50,000 HCPs per list. Duplicate NPIs de-duplicated on import. "
            "Archived lists cannot be edited; must be restored first. "
            "Assigning a locked list to a territory shows warning modal. "
            "List name max 80 chars; special chars @ # % not allowed."
        ),
        metadata={"module": "target_lists", "type": "validation"}
    ),

    # ── Authentication (general) ──────────────────────────────────────────────
    Document(
        page_content=(
            "Authentication: CE-TS uses Microsoft SSO (Azure AD). "
            "Login URL: https://ce-ts-dev.trinitylifesciences.com/. "
            "Flow: enter email → redirect to Microsoft → enter password → MFA (Authenticator app) → "
            "redirected back to app. Session cookie valid 8 hours. "
            "'Stay signed in?' prompt appears – click Yes to persist session. "
            "Failed login shows 'That Microsoft account doesn't exist' on Microsoft portal."
        ),
        metadata={"module": "authentication", "type": "functionality"}
    ),

    # ── General app context ───────────────────────────────────────────────────
    Document(
        page_content=(
            "CE-TS application context: HCP Targeting & Segmentation platform for pharmaceutical "
            "companies. Manages physician (HCP) data for sales rep call planning. "
            "Modules: Login, Universe Summary, Segmentation, Target Lists, Reports, Admin. "
            "Compliance: HIPAA, SOC2. PII must never be logged. "
            "NPI numbers are 10-digit unique physician identifiers."
        ),
        metadata={"module": "general", "type": "context"}
    ),
]


class RAGStore:
    """
    FAISS-based RAG store for CE-TS module knowledge.

    Usage:
        rag = RAGStore()
        context = rag.get_context("segmentation", k=2)
        # Pass context string into merged planner prompt
    """

    # Where to persist the FAISS index on disk
    INDEX_PATH = os.path.join(os.path.dirname(__file__), "faiss_index")

    def __init__(self, force_rebuild: bool = False):
        self._store = None
        self._fallback_docs = CE_TS_KNOWLEDGE  # Used when FAISS not available

        if FAISS_AVAILABLE:
            self._init_faiss(force_rebuild)
        else:
            print("[RAG] ⚠️  faiss-cpu not installed – using keyword fallback search.")
            print("[RAG] Install with: pip install faiss-cpu sentence-transformers")

    # ------------------------------------------------------------------
    def _init_faiss(self, force_rebuild: bool):
        """Load or build the FAISS index."""
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )

            if not force_rebuild and os.path.exists(self.INDEX_PATH):
                print("[RAG] ✅ Loading existing FAISS index from disk...")
                self._store = FAISS.load_local(
                    self.INDEX_PATH, embeddings, allow_dangerous_deserialization=True
                )
            else:
                print("[RAG] 🔨 Building FAISS index from CE-TS knowledge base...")
                self._store = FAISS.from_documents(CE_TS_KNOWLEDGE, embeddings)
                self._store.save_local(self.INDEX_PATH)
                print(f"[RAG] ✅ Index built ({len(CE_TS_KNOWLEDGE)} documents) and saved.")

        except Exception as e:
            print(f"[RAG] ⚠️  FAISS init failed ({e}). Using keyword fallback.")
            self._store = None

    # ------------------------------------------------------------------
    def get_context(self, module_name: str, k: int = 2) -> str:
        """
        Retrieve top-k relevant knowledge chunks for a module.

        Args:
            module_name: e.g. 'segmentation', 'target_lists', 'universe_summary'
            k: max results (default 2 – cost control rule from PDF)

        Returns:
            Formatted context string to inject into LLM prompt.
        """
        query = f"Test scenarios for {module_name} module"

        if self._store is not None:
            docs = self._store.similarity_search(query, k=k)
        else:
            docs = self._keyword_search(module_name, k=k)

        if not docs:
            return ""

        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(
                f"[Knowledge {i} – {doc.metadata.get('module', 'general')} / "
                f"{doc.metadata.get('type', '')}]\n{doc.page_content}"
            )

        return "\n\n".join(context_parts)

    # ------------------------------------------------------------------
    def _keyword_search(self, module_name: str, k: int = 2) -> List[Document]:
        """
        Keyword fallback when FAISS is unavailable.
        Returns docs whose module metadata matches, or general docs.
        """
        exact = [d for d in self._fallback_docs if d.metadata.get("module") == module_name]
        if exact:
            return exact[:k]

        # Fuzzy – check if module_name appears anywhere in content
        fuzzy = [d for d in self._fallback_docs if module_name.lower() in d.page_content.lower()]
        if fuzzy:
            return fuzzy[:k]

        # Return general context as last resort
        return [d for d in self._fallback_docs if d.metadata.get("module") == "general"][:k]

    # ------------------------------------------------------------------
    def is_complex_module(self, module_name: str) -> bool:
        """
        Use RAG for modules that benefit from domain context.
        Includes auth/login — CE-TS has a specific Azure AD SSO + MFA flow.
        """
        complex_modules = {
            "segmentation", "target_lists", "universe_summary",
            "segment", "targets", "universe", "filters", "rules",
            "authentication", "login", "auth", "sso"
        }
        return any(m in module_name.lower() for m in complex_modules)


# ---------------------------------------------------------------------------
# Singleton – one store per process
# ---------------------------------------------------------------------------
_rag_instance: Optional[RAGStore] = None


def get_rag_store() -> RAGStore:
    """Get or create the singleton RAG store."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGStore()
    return _rag_instance


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Testing RAG Store...")
    rag = RAGStore()

    for module in ["segmentation", "target_lists", "login"]:
        print(f"\n{'='*50}")
        print(f"Module: {module}  |  Complex: {rag.is_complex_module(module)}")
        ctx = rag.get_context(module, k=2)
        print(ctx[:300] + "..." if len(ctx) > 300 else ctx)
