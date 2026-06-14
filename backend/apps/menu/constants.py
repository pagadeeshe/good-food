from datetime import time

MEAL_LUNCH = 'lunch'
MEAL_DINNER = 'dinner'

MEAL_TYPE_CHOICES = [
    (MEAL_LUNCH, 'Lunch'),
    (MEAL_DINNER, 'Dinner'),
]

MEAL_TYPES = [MEAL_LUNCH, MEAL_DINNER]

# Order deadline: 10:00 AM on the menu date (the day food is served)
ORDER_DEADLINE_TIME = time(10, 0)
ORDER_DEADLINE_DISPLAY = '10:00 AM'

# Legacy display labels (meal type names only)
CUTOFF_DISPLAY = {
    MEAL_LUNCH: ORDER_DEADLINE_DISPLAY,
    MEAL_DINNER: ORDER_DEADLINE_DISPLAY,
}

DEFAULT_CUTOFF_TIME = {
    MEAL_LUNCH: ORDER_DEADLINE_TIME,
    MEAL_DINNER: ORDER_DEADLINE_TIME,
}


def is_valid_meal_type(value):
    return value in MEAL_TYPES


def cutoff_for_meal(meal_type):
    return DEFAULT_CUTOFF_TIME.get(meal_type, ORDER_DEADLINE_TIME)


def cutoff_display_for_meal(meal_type):
    return CUTOFF_DISPLAY.get(meal_type, '')
