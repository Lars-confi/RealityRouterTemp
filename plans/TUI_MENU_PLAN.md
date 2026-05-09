# TUI Menu Implementation Plan

## 1. Library Selection: `inquirer`

After evaluating options like `inquirer`, `prompt_toolkit`, and `blessed`, **`inquirer`** (Python package) is the recommended choice for this implementation.

*   **Ease of Use:** `inquirer` abstracts away all the raw terminal state management and input handling. It natively provides high-level objects like `List`, `Checkbox`, and `Text` which perfectly correspond to single-choice, multiple-choice, and text-input menus.
*   **Features:** It features built-in scrolling for long lists, color support, and arrow-key navigation. This fulfills the requirement for a fully interactive menu without writing custom cursor-tracking code.
*   **Maintainability:** The declarative nature of defining questions (e.g., `inquirer.List(...)`) will replace complex `while` loops, input validation, and print-paged logic found in `start_router.py`, making the code significantly more readable and easier to extend.

*(Alternative runner-up: `questionary`, which is an updated wrapper around `prompt_toolkit` acting as an `inquirer` substitute, but `inquirer` is sufficient and directly requested).*

---

## 2. Design Implementation for `start_router.py`

The objective is to replace the print-and-input-based `wizard_*` functions with interactive `inquirer` prompts.

### Necessary Code Changes

1.  **Imports:** Add `import inquirer` at the top of the file.
2.  **Refactoring Prompts:** 
    *   The `prompt()` helper function can be updated to use `inquirer.Text()` under the hood, or we can replace its usage entirely with inline `inquirer.prompt()` calls.
3.  **Refactoring `wizard_routing_strategy`:**
    *   Replace the manual print options with an `inquirer.List`:
      ```python
      questions = [
          inquirer.List(
              'strategy',
              message="Select Routing Strategy",
              choices=[
                  ('Expected Utility (Single-shot, Fast)', 'expected_utility'),
                  ('Tiered Assessment (Sequential, Verified)', 'tiered_assessment')
              ],
              default='expected_utility' if env_vars.get("DEFAULT_STRATEGY") != "tiered_assessment" else 'tiered_assessment'
          )
      ]
      answers = inquirer.prompt(questions)
      env_vars["DEFAULT_STRATEGY"] = answers['strategy']
      ```
4.  **Refactoring `wizard_providers` (Interactive Menu):**
    *   Instead of prompting for an action via typed keys ("c", "1", "2"), wrap the provider list in an `inquirer.List`.
    *   Dynamically generate the `choices` array by checking `env_vars` to affix `✓` or `✗` next to each provider name.
    *   Add a "Continue to Model Selection" choice at the bottom.
    *   Place this in a `while True` loop so the user can select a provider, enter their keys (using `inquirer.Text`), and be returned to the updated visual menu until they select "Continue".
5.  **Refactoring `wizard_model_management`:**
    *   Currently, this page uses complex custom pagination (`page = 0`, `PAGE_SIZE = 10`, etc.). `inquirer` gracefully handles long lists with native scrolling.
    *   We can split this into two clean TUI steps:
        *   **Step A (Toggle Models):** Pass all discovered models to an `inquirer.Checkbox` where users press `Space` to toggle and `Enter` to confirm. 
        *   **Step B (Select Sentiment Model):** Pass the active models to an `inquirer.List` to select the sentiment model.
    *   This eliminates the entire manual pagination and nested key commands logic.

### Passing the Provider List & Capturing Selections
*   **Passing to TUI:** Create a list of tuples formatted as `("Display Text", "Return_Value")` and feed it into `choices=...` in `inquirer.List` or `inquirer.Checkbox`. 
*   **Capturing Selection:** The `inquirer.prompt(questions)` method synchronously renders the TUI, waits for the user to make a final selection with the Enter key, and returns a dictionary with the selected key map (e.g., `{'provider_action': 'openai'}`).

---

## 3. Dependency Management

The `inquirer` library needs to be added so that developers and users have it installed when running `start_router.py`.

*   **Location:** Add the dependency to `reality-router/requirements.txt`.
*   **Addition:** 
    ```text
    # UI Tools
    inquirer>=3.4.0
    ```
*   *(Optional but Recommended)*: Update `start.sh` or the environment setup instructions in `README.md` to ensure `pip install -r reality-router/requirements.txt` runs before `start_router.py` executes, preventing `ModuleNotFoundError` for users starting fresh.