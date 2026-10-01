# Software Re-engineering: HTTPie Case Study

## Project Overview
This repository contains a software re-engineering project based on a fork of the popular open-source CLI HTTP client, **HTTPie**. 

The goal of this project was to analyze a mature, real-world Python codebase, identify hidden architectural flaws and code smells, and systematically refactor the software to improve its maintainability, testability, and overall code quality.

* **Academic Context:** Completed as a group project for the module **COM3523/6523 (Software Re-engineering)** at the **University of Sheffield**.
* **Target System:** [HTTPie](https://github.com/httpie/cli) (Python)
* **Core Focus:** Structural analysis, code smell detection and refactoring and architectural refactoring. Improving the HTTPie client by reducing bloat, God classes and class complexity.

## Reengineering Process & Tools Used
To analyze and improve the codebase, our team utilized:
* **Static & Dynamic Analysis:** [PyDriller, psutil, and own methods] to detect code smells and other issues. Including cyclomatic complexity, LCOM, fan-in and fan-out of classes, runtime data and method calls
* **Testing Frameworks:** [Pytest, Coverage.py] to ensure refactoring did not introduce regressions.
* **Refactoring Techniques:** [e.g., Extract Method, Breaking down God Classes, Reducing Cyclomatic Complexity].

## My Individual Contributions
*While this was a collaborative team effort, my specific engineering contributions included:*
* **Session Layout Refactoring:** Refactored and re-engineered (alongside Cristian) the `cli-master/httpie/manager/tasks/sessions.py` file to handle session layout processing natively rather than relying on formatters to access session data, effectively eliminating a critical circular dependency.
* **Enforcing Single Responsibility Principle:** Removed layout fixing logic from the formatters in `cli-master/httpie/legacy/v3_1_0_session_cookie_format.py` and `.../v3_2_0_session_header_format.py`. Moved layout fixing directly into the update logic, ensuring formatting is handled inline and strictly separating formatting from data migration logic.
* **Decoupling Legacy Systems:** Ensured legacy cookies were handled natively within `cli-master/httpie/sessions.py`, completely decoupling it from the formatters system.
* **Static Analysis Pipeline:** Co-developed static analysis techniques to identify prime candidates for refactoring based on fan-in/fan-out, LCOM, Lines of Code (LOC), and complex class relationships.
* **Dynamic Analysis Diagnostics:** Executed dynamic analysis tracking to map frequent file dependencies and method call chains. Successfully diagnosed that the `Sessions` module was structurally tightly coupled with formatting files, guiding our refactoring roadmap. Further identified `argparser.py`, `models.py` and `core.py` as candidates for refactoring and reengineering.

## This was a collaborative project as part of a team
* **Pijus Lucinskas**: [@PigeonSpy](https://github.com)
* **Cristian Razvan Popa**: [@CristianRazvanPopa](https://github.com/CristianRazvanPopa)
* **Frederico Ferri**: [@FredericoFerri](https://github.com/FredericoFerri)
* **Ethan Pinkerton**: [@EthanPinkerton](https://github.com/EthanPinkerton)
* **Joel Matthews**: [@mrjm0](https://github.com/mrjm0)
* **Abdelrhman Badr**: [@Aca21ab](https://github.com/Aca21ab)

## Outcomes
Our re-engineering efforts successfully reduced formatter complexity and reinstated the **Single Responsibility Principle** across Sessions, Models, and the Argparser. We significantly lowered the internal complexity of Models and the Argparser, improved overall module cohesion, and verified that zero regressions were introduced to the core system.

### Academic Integrity Notice
This repository is published strictly as a portfolio piece for demonstration purposes.
