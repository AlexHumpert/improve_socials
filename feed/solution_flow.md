# Combined AI Interview and Generative Agent Flow

This diagram illustrates the interconnected flow between an AI Interviewer system and a Generative Agent, with enhanced contrast for better readability.

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'fontSize': '16px', 'fontFamily': 'arial', 'lineColor': '#000000', 'textColor': '#000000' }}}%%
graph LR
    %% AI Interviewer Flow
    U["Participant's Utterance"] --> M["AI Interviewer Memory"]
    S["Interview Script"] --> M
    M <--> R["Expert Reflection"]
    M --> Q["Next Question"]
    
    %% Generative Agent Flow
    Q2["Question"] --> GM["Generative Agent Memory With Interview Transcript"]
    R --> GM
    GM --> P["Prediction"]

    %% Styling with high contrast
    classDef default fill:#FFFFFF,stroke:#000000,stroke-width:2px,color:#000000
    classDef memory fill:#E6E6E6,stroke:#000000,stroke-width:3px,color:#000000
    classDef reflection fill:#FFFFFF,stroke:#000000,stroke-width:2px,color:#000000
    class M,GM memory
    class R reflection
```

## Components

### AI Interviewer Flow
- **Participant's Utterance**: Input from the interview participant
- **Interview Script**: Predefined interview structure and questions
- **AI Interviewer Memory**: System memory storing interview context and responses
- **Next Question**: Generated follow-up question based on the conversation

### Shared Component
- **Expert Reflection**: Reflection mechanism that bridges both systems

### Generative Agent Flow
- **Question**: Input query to the generative system
- **Generative Agent Memory**: System memory incorporating interview transcript
- **Prediction**: Generated output based on memory and reflection