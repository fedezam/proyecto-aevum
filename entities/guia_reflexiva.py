import json
import os
from typing import Dict, List, Optional, Any
from core.mmp_engine import MMPEngine


class GuiaReflexiva:
    """
    Reflective Guide Entity (fractal-capable).
    It can guide other entities out of reasoning loops, uncover hidden assumptions,
    and mirror back blind spots. If it falls into its own loop, it may request
    guidance from another GuiaReflexiva (fractal recursion).
    """

    def __init__(self, name: str = "GuiaReflexiva", corpus_path: str = "core/mmp_corpus.json"):
        self.name = name
        self.engine = MMPEngine(corpus_path=corpus_path)
        self.history: List[Dict[str, Any]] = []
        self.loop_counter: int = 0
        self.loop_threshold: int = 3  # number of repetitions before triggering fractal recursion

    def mirror_call(self, entity_state: Dict[str, Any], category: str = "MIRROR_CALL") -> str:
        """
        Perform a reflective mirror call on an entity state.
        """
        question = self.engine.get_question(category)
        self.history.append({
            "entity_state": entity_state,
            "category": category,
            "question": question
        })
        return question

    def guide_entity(self, entity_name: str, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide reflective guidance to another entity based on its current reasoning state.
        Detects loops and assumptions. Can also call another GuiaReflexiva if stuck.
        """
        summary = current_state.get("summary", "unknown")

        # naive detection of looping (based on repetition in summary text)
        if self._is_looping(summary):
            self.loop_counter += 1
        else:
            self.loop_counter = 0

        # if too many loops, call another GuiaReflexiva for support (fractal recursion)
        if self.loop_counter >= self.loop_threshold:
            external_guide = GuiaReflexiva(name=f"{self.name}_Fractal")
            fractal_help = external_guide.mirror_call(
                {"summary": f"{self.name} is looping on: {summary}"},
                category="LOOP_DETECTION"
            )
            guidance = {
                "target_entity": entity_name,
                "current_state_summary": summary,
                "guidance": {
                    "fractal_support": fractal_help,
                    "note": "Loop exceeded threshold, fractal recursion activated."
                }
            }
            self.history.append(guidance)
            return guidance

        # otherwise, proceed with normal guidance
        loop_prompt = self.engine.get_question("LOOP_DETECTION")
        assumption_prompt = self.engine.get_question("ASSUMPTION_UNCOVERING")

        guidance = {
            "target_entity": entity_name,
            "current_state_summary": summary,
            "guidance": {
                "loop_reflection": loop_prompt,
                "assumption_probe": assumption_prompt,
                "mirror_question": self.engine.get_question("MIRROR_CALL")
            }
        }

        self.history.append(guidance)
        return guidance

    def _is_looping(self, text: str) -> bool:
        """
        Very simple heuristic: if the same word repeats too much, assume looping.
        """
        words = text.lower().split()
        if not words:
            return False
        most_common = max(set(words), key=words.count)
        return words.count(most_common) > len(words) * 0.5  # >50% repetition

    def get_history(self) -> List[Dict[str, Any]]:
        """Return the reflective interaction history."""
        return self.history

    def save_history(self, path: str = "logs/guia_reflexiva_history.json") -> None:
        """Save history of guidance to JSON file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)


# Example usage (manual test)
if __name__ == "__main__":
    guia = GuiaReflexiva()
    test_state = {"summary": "loop loop loop loop loop"}
    for i in range(5):
        output = guia.guide_entity("EntidadDePrueba", test_state)
        print(json.dumps(output, indent=2))
