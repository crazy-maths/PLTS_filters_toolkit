from parser.formula_parser import FormulaParser
from services.logging_service import get_logger

logger = get_logger("EvaluationService")

class EvaluationService:
    @staticmethod
    def _check_membership(val, twist_filter) -> bool:
        if not twist_filter:
            return False
        try:
            if val in twist_filter.filter_elements:
                return True

            candidates = set()
            if isinstance(val, tuple):
                candidates.add(val)
                candidates.add(tuple(str(x) for x in val))
                try:
                    candidates.add(tuple(int(x) if str(x).isdigit() else x for x in val))
                except ValueError:
                    pass
            elif isinstance(val, str):
                cleaned = val.strip("() ")
                parts = [p.strip("' \"") for p in cleaned.split(",")]
                t_str = tuple(parts)
                candidates.add(t_str)
                try:
                    t_int = tuple(int(p) if p.isdigit() else p for p in parts)
                    candidates.add(t_int)
                except ValueError:
                    pass

            for cand in candidates:
                if cand in twist_filter.filter_elements:
                    return True

            return False
        except Exception:
            return False

    @staticmethod
    def evaluate(f_str: str, model, world, twist_filter=None) -> str:
        """Parses and evaluates a single formula."""
        try:
            parser = FormulaParser(f_str)
            root = parser.parse()
            
            unknown = [a for a in root.get_atoms() if a not in world.assignments and a not in ('0', '1', 'TOP', 'BOT')]
            if unknown:
                msg = f"Missing assignments in state '{world.name_short}' for: {', '.join(unknown)}"
                logger.warning(msg)
                raise ValueError(msg)

            res = root.evaluate(model, world, model.twist_structure)
            res_str = str(res).replace("'", "")
            
            if twist_filter is not None:
                in_filter = EvaluationService._check_membership(res, twist_filter)
                status = "Yes" if in_filter else "No"
                return f"{res_str} | [In Filter: <b>{status}</b>]"

            return res_str
        except ValueError as ve:
            logger.error(f"Validation error for formula '{f_str}': {str(ve)}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error evaluating formula '{f_str}': {str(e)}")
            raise

    @staticmethod
    def check_validity(f_str: str, model, twist_filter=None):
        try:
            parser = FormulaParser(f_str)
            root = parser.parse()
            
            result_worlds = []
            result_for_calculation = []

            for world in sorted(model.worlds, key=lambda w: w.name_long):
                if [a for a in root.get_atoms() if a not in world.assignments and a not in ('0', '1', 'TOP', 'BOT')]:
                    msg = f"State '{world.name_short}' is missing assignments required by formula."
                    logger.error(msg)
                    raise ValueError(msg)
                
                res = root.evaluate(model, world, model.twist_structure)
                res_str = str(res).replace("'", "")
                result_for_calculation.append(res)
                
                def format_membership(raw_res):
                    if not twist_filter: return ""
                    in_f = EvaluationService._check_membership(raw_res, twist_filter)
                    return f" [In Filter: <b>{'Yes' if in_f else 'No'}</b>]"

                formatted_res = res_str + format_membership(res)
                result_worlds.append((world.name_long, formatted_res))
            
            meet_all = model.twist_structure.weak_meet_set(result_for_calculation)
            meet_all_str = str(meet_all).replace("'", "")
            
            if twist_filter:
                in_f = EvaluationService._check_membership(meet_all, twist_filter)
                meet_all_str += f" [In Filter: <b>{'Yes' if in_f else 'No'}</b>]"

            return result_worlds, meet_all_str
            
        except ValueError as ve:
            logger.error(f"Validity check validation error: {str(ve)}")
            raise
        except Exception as e:
            logger.exception("Validity check failed due to unexpected error.")
            raise