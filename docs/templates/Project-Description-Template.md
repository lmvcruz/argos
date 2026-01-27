# Project Description Template

Use this template to create clean, concise project documentation. Fill in each section with specific details for your project.

---

## Instructions for Use

1. **Be decisive**: Choose specific technologies, don't list options
2. **Be concise**: Focus on what will be built, not what might be built later
3. **Text only**: Describe schemas, APIs, and code integration in words, not code blocks
4. **No phases**: Don't separate MVP from future features - describe the complete application
5. **Be specific**: Include actual tech stack, module responsibilities, data structures

---

# [PROJECT NAME]

## Project Description

[2-3 sentences describing what the application does and its purpose]

### Key Features

- **Feature 1**: [Brief description]
- **Feature 2**: [Brief description]
- **Feature 3**: [Brief description]
- **Feature 4**: [Brief description]
- **Feature 5**: [Brief description]

---

## Technology Stack

### Core Technologies

**[Primary Language]:**
- [Framework/Library 1]: [What it does]
- [Framework/Library 2]: [What it does]
- [Library 3]: [What it does]

**[Secondary Language if applicable]:**
- [Framework/Library 1]: [What it does]
- [Tool/Library 2]: [What it does]

### Data Storage (if applicable)

**[Database/File Format]:**
- [What data it stores]
- [Why this choice]
- [Key characteristics]

### UI/Frontend (if applicable)

- **[UI Framework]**: [Why chosen]
- **[Graphics/Rendering Library]**: [What it renders]
- **[Component Library]**: [UI components]

### Infrastructure (if applicable)

- **[Deployment method]**: [How it's deployed]
- **[Build tools]**: [What they do]

---

## System Modules

### 1. [Module Name]

**Responsibilities:**
- [What this module does - bullet point 1]
- [What this module does - bullet point 2]
- [What this module does - bullet point 3]

**Components:**

**[Component 1 Name]:**
- [Component responsibility and how it works]
- [Key features or behaviors]
- [Technologies used]

**[Component 2 Name]:**
- [Component responsibility and how it works]
- [Key features or behaviors]

**[Component 3 Name (if applicable)]:**
- [Component responsibility and how it works]

---

### 2. [Module Name]

**Responsibilities:**
- [What this module does]
- [What this module does]

**Components:**

**[Component Name]:**
- [Description]
- [Key features]

---

### 3. [Module Name]

[Continue for all major modules - typically 4-8 modules total]

---

## Data Structures (if applicable)

### [Data Structure 1]

**Purpose**: [What this stores]

**Fields/Properties:**
- [Field name]: [Type and description]
- [Field name]: [Type and description]
- [Field name]: [Type and description]

**Storage**: [Where and how it's persisted]

### [Data Structure 2]

[Continue for all major data structures]

---

## Application Flow

### [Main Workflow 1]
1. [Step 1 description]
2. [Step 2 description]
3. [Step 3 description]
4. [Step 4 description]

### [Main Workflow 2]
1. [Step 1 description]
2. [Step 2 description]
3. [Step 3 description]

### [Main Workflow 3 if applicable]

---

## Non-Functional Requirements

**Performance:**
- [Performance metric 1]: [Target value and description]
- [Performance metric 2]: [Target value and description]
- [Performance metric 3]: [Target value and description]

**User Experience:**
- [UX requirement 1]
- [UX requirement 2]

**Reliability:**
- [Reliability requirement 1]
- [Reliability requirement 2]

**Platform Support:**
- [Supported platforms and versions]

---

## Integration Points (if applicable)

### [External System/Service 1]

[How this application integrates with it, what data is exchanged, communication protocol]

### [External System/Service 2]

[Description of integration]

---

**Last Updated:** [Date]

---

## Example: How to Apply This Template

**Bad** (what to avoid):
```
Frontend: React or Vue (TBD)
Phase 1: Basic rendering
Phase 2: Add physics engine
MVP: Simple controls
Future: Advanced features (maybe WebGL, possibly multiplayer)
```

**Good** (follow this style):
```
Frontend:
- React with TypeScript for component-based UI
- Three.js for 3D terrain rendering
- Bootstrap 5 for control panels

The rendering engine uses Three.js to display heightmap-based terrain with real-time camera controls. User can pan, zoom, and rotate the view using mouse and keyboard. The physics simulation calculates erosion and deposition in background threads, updating the mesh every frame. Control panels built with Bootstrap allow adjusting simulation parameters like water flow rate and soil properties.
```

---

## Key Principles Recap

1. **Decisive**: "We use TypeScript" not "TypeScript or JavaScript"
2. **Descriptive**: Explain what components do and how they interact
3. **Text-based**: Describe schemas, APIs, and code in prose, not code blocks
4. **Complete**: This is the full application description, not a phased plan
5. **Focused**: Only describe what's being built, not what might be added someday
6. **Specific**: Name actual libraries, frameworks, and technologies
7. **Realistic**: Match scope to available time and resources
