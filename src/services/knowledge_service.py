"""
MynEra Aira - Domain Knowledge Service
Queries the DIM education system knowledge base (dim_knowledge.json).
Decouples facts from prompts for maintainability.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class KnowledgeService:
    """
    Service to query domain-specific knowledge about:
    - DIM groups and majors
    - Universities and requirements
    - Education system rules
    
    This decouples hard facts from the LLM prompt, making it easy
    to update data without changing code.
    """

    def __init__(self):
        """Load knowledge base from JSON."""
        self.knowledge_path = Path(__file__).parent.parent / "data" / "dim_knowledge.json"
        self.knowledge = self._load_knowledge()
        
        if self.knowledge:
            logger.info("✅ Knowledge base loaded successfully")
        else:
            logger.error("❌ Failed to load knowledge base")

    def _load_knowledge(self) -> Dict[str, Any]:
        """Load JSON knowledge base."""
        try:
            if not self.knowledge_path.exists():
                logger.error(f"Knowledge file not found: {self.knowledge_path}")
                return {}
            
            with open(self.knowledge_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded knowledge base with {len(data.get('groups', {}))} groups")
                return data
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            return {}

    def lookup_term(self, query: str) -> str:
        """
        Lookup a term in the knowledge base.
        
        Args:
            query: User's question (e.g., "Economics", "Group 3", "UFAZ")
        
        Returns:
            Formatted answer with facts from knowledge base
        """
        if not self.knowledge:
            return "⚠️ Bilik bazası əlçatan deyil."
        
        query_lower = query.lower()
        
        # Check major/subject queries
        major_result = self._search_major(query_lower)
        if major_result:
            return major_result
        
        # Check group queries
        group_result = self._search_group(query_lower)
        if group_result:
            return group_result
        
        # Check university queries
        uni_result = self._search_university(query_lower)
        if uni_result:
            return uni_result
        
        # Check quick facts
        quick_result = self._search_quick_facts(query_lower)
        if quick_result:
            return quick_result
        
        return f"ℹ️ '{query}' haqqında bilik bazasında məlumat tapılmadı. search_web istifadə edin."

    def _search_major(self, query: str) -> Optional[str]:
        """Search for a major/subject."""
        groups_data = self.knowledge.get("groups", {})
        
        for group_id, group_info in groups_data.items():
            # Check allowed majors
            for major in group_info.get("allowed_majors", []):
                if query in major.lower():
                    group_name = group_info['name']
                    forbidden = group_info.get('forbidden_majors', [])
                    unis = group_info.get('universities', [])
                    
                    result = f"📚 **{major}**\n\n"
                    result += f"✅ Qrup: {group_name}\n"
                    result += f"🎓 Universitetlər: {', '.join(unis[:3])}\n"
                    result += f"\n⚠️ **DİQQƏT:** Bu ixtisas {group_name} ilə daxil olunur.\n"
                    if forbidden:
                        result += f"❌ Bu ixtisas üçün QADAĞAN qruplar: {', '.join([f['name'] if isinstance(f, dict) else f for f in forbidden[:3]])}\n"
                    
                    return result
            
            # Check forbidden majors (important for negative constraints!)
            for forbidden_major in group_info.get("forbidden_majors", []):
                if query in forbidden_major.lower():
                    group_name = group_info['name']
                    return f"❌ **{forbidden_major}** {group_name} ilə QƏBUL OLUNMUR!\n\nDüzgün qrupu tapmaq üçün digər qruplara baxın."
        
        return None

    def _search_group(self, query: str) -> Optional[str]:
        """Search for group information."""
        groups_data = self.knowledge.get("groups", {})
        
        # Extract group number
        group_id = None
        if "qrup 1" in query or "i qrup" in query or "group 1" in query:
            group_id = "1"
        elif "qrup 2" in query or "ii qrup" in query or "group 2" in query:
            group_id = "2"
        elif "qrup 3" in query or "iii qrup" in query or "group 3" in query:
            group_id = "3"
        elif "qrup 4" in query or "iv qrup" in query or "group 4" in query:
            group_id = "4"
        elif "qrup 5" in query or "v qrup" in query or "group 5" in query:
            group_id = "5"
        
        if group_id and group_id in groups_data:
            group_info = groups_data[group_id]
            
            result = f"## 📋 {group_info['name']}\n\n"
            result += f"**Fənlər:** {group_info['description']}\n\n"
            result += f"✅ **İCAZƏLİ İXTİSASLAR:**\n"
            for major in group_info['allowed_majors'][:8]:
                result += f"  • {major}\n"
            
            result += f"\n❌ **QADAĞAN İXTİSASLAR:**\n"
            for major in group_info['forbidden_majors'][:5]:
                result += f"  • {major}\n"
            
            result += f"\n🎓 **UNİVERSİTETLƏR:**\n"
            for uni in group_info['universities']:
                result += f"  • {uni}\n"
            
            if group_info.get('notes'):
                result += f"\n💡 **QEYD:** {group_info['notes']}\n"
            
            return result
        
        return None

    def _search_university(self, query: str) -> Optional[str]:
        """Search for university information."""
        unis_data = self.knowledge.get("universities", {})
        
        for uni_key, uni_info in unis_data.items():
            if uni_key.lower() in query or uni_info['full_name'].lower() in query:
                result = f"## 🎓 {uni_info['full_name']}\n\n"
                
                if uni_info['status'] == "CLOSED":
                    result += f"🚫 **STATUS: BAĞLIDIR!**\n\n"
                    result += f"{uni_info['notes']}\n"
                    return result
                
                result += f"✅ Status: {uni_info['status']}\n"
                result += f"📚 Tip: {uni_info['type']}\n"
                result += f"📊 Qruplar: {', '.join(uni_info['groups'])}\n"
                result += f"💰 Təhsil haqqı: {uni_info['tuition']}\n"
                result += f"📈 2024 keçid balı: {uni_info.get('passing_score_2024', 'N/A')}\n"
                result += f"\n⚙️ **Tələblər:** {uni_info['requirements']}\n"
                
                if uni_info.get('notes'):
                    result += f"\n💡 **Qeyd:** {uni_info['notes']}\n"
                
                return result
        
        return None

    def _search_quick_facts(self, query: str) -> Optional[str]:
        """Search quick facts."""
        quick_facts = self.knowledge.get("quick_facts", {})
        
        for key, value in quick_facts.items():
            if any(term in query for term in key.split('_')):
                return f"💡 {value}"
        
        return None

    def get_group_for_major(self, major: str) -> Optional[str]:
        """Get which group a major belongs to."""
        groups_data = self.knowledge.get("groups", {})
        
        for group_id, group_info in groups_data.items():
            for allowed_major in group_info.get("allowed_majors", []):
                if major.lower() in allowed_major.lower():
                    return group_info['name']
        
        return None

    def is_major_forbidden_in_group(self, major: str, group_id: str) -> bool:
        """Check if a major is explicitly forbidden in a group."""
        groups_data = self.knowledge.get("groups", {})
        
        if group_id in groups_data:
            forbidden = groups_data[group_id].get("forbidden_majors", [])
            return any(major.lower() in f.lower() for f in forbidden)
        
        return False


# Singleton instance
knowledge_service = KnowledgeService()
