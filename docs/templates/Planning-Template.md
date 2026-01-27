# Iterative Planning Template

This template is designed for planning projects in small, verifiable iterations. The goal is to ensure that each phase of development produces a concrete, testable outcome, minimizing risk and providing clear markers of progress.

---

## Guiding Principles

1.  **Small Iterations**: Each iteration should be short (e.g., 1-2 weeks) and have a single, clear goal.
2.  **Verifiable Steps**: Every step within an iteration must have a clear, objective validation criterion. Avoid vague goals like "code cleanup" and prefer specific outcomes like "reduce function complexity from 25 to 10."
3.  **Build on Success**: Each iteration should build directly upon the validated success of the previous one.
4.  **Headless-First**: Whenever possible, validate core logic and backend functionality through APIs or command-line tools before building a UI.

---

# Project Plan: [PROJECT NAME]

## Iteration 1: [Name of the Iteration, e.g., "Core Logic & Headless Validation"]

**Goal:** [A brief description of the primary objective for this iteration. e.g., "To validate that the core data processing logic works correctly without a user interface."]

### Steps

#### Step 1.1: [Name of the first step, e.g., "Define Data Schemas"]
-   **Description:** [Describe the task. e.g., "Define the Pydantic or SQL schemas for the `User` and `Project` models."]

#### Step 1.2: [Name of the second step, e.g., "Build the 'Create Project' API Endpoint"]
-   **Description:** [e.g., "Implement a `POST /projects` endpoint that accepts a project name and owner ID."]

#### Step 1.3: [Name of the third step, e.g., "Implement Core Processing Logic"]
-   **Description:** [e.g., "Create a function `process_data(project_id)` that performs the core business logic."]

### Success Criteria

-   **Criterion 1.1:** [How to verify Step 1.1 is successful. e.g., "The schema definitions are committed to the repository and pass linting checks."]
-   **Criterion 1.2:** [How to verify Step 1.2 is successful. e.g., "The `POST /projects` endpoint can be called via Swagger, a new record appears in the database, and it returns a 201 status code."]
-   **Criterion 1.3:** [How to verify Step 1.3 is successful. e.g., "Unit tests for the `process_data` function pass with 90%+ code coverage."]
-   **Overall:** [A summary of the iteration's success. e.g., "A project can be created via an API call, and the core logic is verified through unit tests."]

---

## Iteration 2: [Name of the Iteration, e.g., "Basic Frontend & API Integration"]

**Goal:** [e.g., "To connect a minimal user interface to the validated backend endpoints, allowing a user to perform the core action."]

### Steps

#### Step 2.1: [e.g., "Create Basic UI Layout"]
-   **Description:** [e.g., "Build a simple React component with an input field for the project name and a 'Create' button."]

#### Step 2.2: [e.g., "Connect UI to Backend API"]
-   **Description:** [e.g., "Wire the 'Create' button to call the `POST /projects` endpoint implemented in Iteration 1."]

### Success Criteria

-   **Criterion 2.1:** [e.g., "The React component renders correctly in the browser without any console errors."]
-   **Criterion 2.2:** [e.g., "Clicking the 'Create' button in the UI successfully creates a new project in the database, and the UI displays the new project ID returned from the API."]
-   **Overall:** [e.g., "A user can successfully create a project through the web interface, and the result is correctly persisted in the database."]

---

## Iteration 3: [Name of the Next Iteration]

**(Copy the structure from the previous iterations and continue the plan.)**

---