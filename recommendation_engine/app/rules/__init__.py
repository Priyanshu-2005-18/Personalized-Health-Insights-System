from app.rules.sleep_rules import SLEEP_RULES
from app.rules.activity_rules import ACTIVITY_RULES
from app.rules.hydration_rules import HYDRATION_RULES
from app.rules.stress_rules import STRESS_RULES
from app.rules.nutrition_rules import NUTRITION_RULES
from app.rules.heart_rate_rules import HEART_RATE_RULES

ALL_RULE_SETS = {
    "sleep":      SLEEP_RULES,
    "activity":   ACTIVITY_RULES,
    "hydration":  HYDRATION_RULES,
    "stress":     STRESS_RULES,
    "nutrition":  NUTRITION_RULES,
    "heart_rate": HEART_RATE_RULES,
}
