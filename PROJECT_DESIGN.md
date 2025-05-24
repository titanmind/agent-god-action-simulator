## Agent World Simulator - Pragmatic Python Architecture v3

### Core Philosophy
- **Python-only** monolithic application
- **Self-hosted** personal project (no enterprise security/compliance)
- **Modular** but not microservices
- **Practical** over perfect - ship it, don't architect it to death

### 1. **Simplified Runtime Architecture**

**Single Process, Multiple Threads:**
```
main.py
├── Main Thread: Game loop, physics, world updates
├── LLM Thread Pool (4-8 threads): Agent reasoning
├── Persistence Thread: Periodic saves
└── Angel Thread: Ability generation when needed
```

**Time System (Simple but Effective):**
```python
TimeManager:
  - tick_rate: 10Hz (configurable)
  - tick_counter: global tick number
  - pause_state: for ability generation
  - soft_tick_budget: 100ms target
  - deferred_actions: queue for slow LLM responses
```

**LLM Latency Handling:**
- Agents get 50ms to respond
- If no response, use cached behavior
- Late responses applied next tick
- "Thinking" state for agents awaiting LLM

### 2. **Simplified ECS in Pure Python**

**Entity Storage:**
```python
# Simple dict-based ECS
entities = {
    entity_id: {
        'components': {
            'position': Position(x, y),
            'health': Health(100, 100),
            'inventory': Inventory(capacity=20),
            'ai_state': AIState(personality="aggressive")
        }
    }
}

# Spatial index for fast lookups
spatial_grid = defaultdict(set)  # (x,y) -> {entity_ids}
```

**Core Systems (Python functions):**
```python
def movement_system(entities, spatial_grid, tick):
def combat_system(entities, events, tick):
def perception_system(entities, spatial_grid):
def ai_reasoning_system(entities, llm_queue):
def ability_system(entities, abilities):
```

### 3. **Practical LLM Integration**

**Simple LLM Manager:**
```python
class LLMManager:
    def __init__(self):
        self.client = OpenRouterClient()
        self.request_queue = Queue()
        self.response_cache = LRUCache(1000)
        self.workers = [LLMWorker() for _ in range(8)]
    
    def request_action(self, agent_id, world_view, urgency='normal'):
        # Check cache first
        # Queue if miss
        # Return cached behavior if timeout
```

**Determinism Solution:**
- Store LLM responses in event log
- Replay uses stored responses, not new LLM calls
- Each tick's decisions saved with frame

### 4. **File-Based Persistence**

**Simple Save System:**
```python
# saves/world_001/
├── world_state.json      # Current state snapshot
├── events/              # Event log by tick range
│   ├── 0000000-0010000.jsonl
│   ├── 0010001-0020000.jsonl
├── abilities/           # Generated ability code
│   ├── fireball.py
│   ├── telepathy.py
└── memories/            # Agent memories (optional)
    ├── agent_001.json
```

**Save Format:**
- JSON for readability/debugging
- JSONL for event streams
- Gzip compression for older files
- SQLite for indexes if needed

### 5. **Dynamic Ability System (Simplified)**

**Ability Structure:**
```python
# abilities/base.py
class Ability:
    def can_use(self, agent, world): pass
    def execute(self, agent, world, **kwargs): pass

# Generated ability example
class Fireball(Ability):
    energy_cost = 10
    cooldown = 5
    
    def execute(self, agent, world, target_pos):
        # Angel-generated code here
        # Sandboxed with resource limits
```

**Simple Sandboxing:**
- Use `RestrictedPython` library
- Timeout via `signal` module
- Memory limit via `resource` module
- No network access in abilities

### 6. **Monolithic Module Structure**

```
agent_world/
├── main.py              # Entry point, game loop
├── config.py            # Simple config file
├── core/
│   ├── world.py         # World grid, spatial index
│   ├── entities.py      # Entity management
│   ├── components.py    # Component definitions
│   └── systems.py       # Game systems
├── ai/
│   ├── llm_manager.py   # LLM integration
│   ├── prompts.py       # Prompt templates
│   ├── behaviors.py     # Fallback behaviors
│   └── angel.py         # Ability generator
├── abilities/
│   ├── base.py          # Base ability class
│   ├── builtin.py       # Core abilities
│   └── generated/       # Runtime-generated abilities
├── persistence/
│   ├── save_load.py     # World serialization
│   └── replay.py        # Replay system
└── utils/
    ├── sandbox.py       # Code execution sandbox
    └── observer.py      # Debug/monitoring
```

### 7. **Practical Observability**

**Simple Debug Tools:**
```python
class WorldObserver:
    def __init__(self):
        self.tick_times = deque(maxlen=1000)
        self.entity_counts = {}
        self.llm_stats = LLMStats()
    
    def dump_state(self, filepath):
        # Dump current world state for debugging
    
    def replay_from_log(self, event_log):
        # Replay specific tick range
```

**Console Commands:**
- `/pause` - Pause simulation
- `/step` - Single tick
- `/spawn <entity>` - Debug spawning
- `/debug <agent_id>` - Show agent state
- `/save` - Force save

### 8. **Simplified Game Systems**

**Core Mechanics Only:**
```python
# Just the essentials
InteractionSystem:
  - pickup/drop items
  - attack/defend
  - trade/steal
  - use objects

PropertySystem:
  - ownership tracking
  - reputation (simple numeric)
  - relationships (dict of agent->value)

EconomySystem:
  - simple item values
  - basic supply/demand
```

### 9. **Configuration**

**Simple YAML Config:**
```yaml
# config.yaml
world:
  size: [100, 100]
  tick_rate: 10

llm:
  provider: "openrouter"
  api_key: "your-key"
  model: "gpt-4"
  max_concurrent: 10
  timeout: 2.0
  cache_behaviors: true

game:
  starting_agents: 20
  item_spawn_rate: 0.1
  combat_damage_multiplier: 1.0

paths:
  saves: "./saves"
  abilities: "./abilities/generated"
```

### 10. **Main Loop Example**

```python
async def main():
    world = World(config.world.size)
    llm_manager = LLMManager(config.llm)
    save_manager = SaveManager(config.paths.saves)
    
    # Spawn initial agents
    for i in range(config.game.starting_agents):
        agent = create_agent(f"agent_{i}")
        world.add_entity(agent)
    
    # Main game loop
    last_save = time.time()
    while True:
        tick_start = time.time()
        
        # Process systems
        movement_system(world)
        perception_system(world)
        
        # Queue AI decisions (non-blocking)
        ai_reasoning_system(world, llm_manager)
        
        # Execute ready actions
        action_system(world)
        combat_system(world)
        
        # Periodic save
        if time.time() - last_save > 60:
            save_manager.save_world(world)
            last_save = time.time()
        
        # Maintain tick rate
        tick_duration = time.time() - tick_start
        sleep_time = (1.0 / config.world.tick_rate) - tick_duration
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)
```

### Key Simplifications

1. **No Microservices**: Everything in one Python process
2. **No Docker/K8s**: Just `python main.py`
3. **No Kafka/RabbitMQ**: Python Queue/asyncio only
4. **No Complex Databases**: Files + optional SQLite
5. **No Security Theater**: It's your personal sandbox
6. **Practical LLM Integration**: Timeouts and caching
7. **Simple Persistence**: JSON files, not 3 databases
8. **Basic Observability**: Print statements and simple stats

### Getting Started

```bash
# Install dependencies
pip install pyyaml aiohttp restrictedpython

# Configure
cp config.example.yaml config.yaml
# Edit config.yaml with your OpenRouter API key

# Run
python main.py

# In another terminal, watch the world
tail -f logs/world.log
```
