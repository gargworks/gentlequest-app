# Nucleus Architecture: The Theory of Personas

## The Formula
In Nucleus, a "Persona" is not a vibe. It is a mathematical structure:

`Agent(x) = Solver(Objective(x) + Constraints(x))`

## The Components

### 1. The Objective (`state.json`)
Defines **WHAT** matters.
- **Engineer:** `Maximize(Accuracy)`
- **Founder:** `Maximize(Speed)`
- **Writer:** `Maximize(Engagement)`

### 2. The Constraints (`context.md`)
Defines **HOW** we behave (Hard Limits).
- **Engineer:** `Constraint: Latency < 500ms`
- **Founder:** `Constraint: Buy > Build`
- **Writer:** `Constraint: Clarity > Cleverness`

### 3. The Solver (`sequential-thinking`)
The reasoning engine that finds the optimal path.
- It reads the Objective.
- It checks the Constraints.
- It rejects paths that violate constraints (e.g., The Founder rejected "Custom Stripe" because it violated "Speed").

## Why this is powerful
You can "program" an identity by simply changing the file inputs. The reasoning engine stays the same, but the *behavior* shifts radically.
