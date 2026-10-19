# STAGE - One User, One Agent

## Run from project root
Activate your existing virtual environment first.

### Replay
```powershell
python -m src.replay_engine --pack one_user_one_agent_pack --out submission\sample_run
```

### Simulate outcomes
```powershell
python one_user_one_agent_pack\simulator\simulate_outcomes.py --pack one_user_one_agent_pack --actions submission\sample_run\actions.jsonl --out submission\sample_run\sim
```

### Evaluate goals
```powershell
python -m src.goal_outcome_evaluator --pack one_user_one_agent_pack --run submission\sample_run
```

### Impact report
```powershell
python -m src.impact_report --pack one_user_one_agent_pack --run submission\sample_run
```

### Tests
```powershell
Push-Location .\submission; python -m unittest discover -s tests -v; Pop-Location
```

### Limitations
Results are simulated and descriptive, not proof of causal impact. Viewer state is replay-derived file-backed persistence, not a transactional production database. Some reliability scenarios need deeper integration testing.
