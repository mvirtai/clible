"""
Menu definitions for clible CLI.

Constants: MAIN_MENU, API_MENU, ANALYTICS_MENU, EXPORTS_MENU,
SESSION_MENU, HISTORY_MENU. Used by menu_utils and menu runners.
"""

MAIN_MENU = {
    "title": "=== clible menu ===",
    "options": [
        "Fetch from API",
        "Show all saved verses",
        "Analytic tools",
        "Exports menu",
        "Session management"
    ],
    "footer": "Exit",
}

API_MENU = {
    "title": "=== fetch from API menu ===",
    "options": [
        "Fetch verse by reference",
        "Fetch chapter by reference",
        "Fetch random verse",
        "Fetch multiple books"
    ],
    "footer": "Return to main menu"
}

ANALYTICS_MENU = {
    "title": "=== analytic tools ===",
    "options": [
        "Search word",
        "Translation comparison",
        "Word frequency analysis",
        "Phrase analysis",
        "Analyze current session",
        "Analyze multiple queries",
        "Analyze by book",
        "View analysis history"
    ],
    "footer": "Return to main menu",
}

EXPORTS_MENU = {
    "title": "=== exports menu ===",
    "options": [
        "Export verses to markdown",
        "Export verses to text"
    ],
    "footer": "Return to main menu"
}

SESSION_MENU = {
    "title": "=== session management ===",
    "options": [
        "Start new session",
        "Resume session",
        "End current session",
        "Save current session (make permanent)",
        "List all sessions",
        "Delete session",
        "Clear session cache",
    ],
    "footer": "Return to main menu"
}

HISTORY_MENU = {
    "title": "=== analysis history ===",
    "options": [
        "View all analyses",
        "Filter by type",
        "Toggle current session filter",
        "View specific analysis",
    ],
    "footer": "Return to analytics menu"
}