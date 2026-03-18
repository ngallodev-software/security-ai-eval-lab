# Important Implementation notes
## 1. Use deterministic serialization for input_artifact

Because execute() stringifies the artifact, the adapter should pass stable JSON, like:

```python
json.dumps(evidence_bundle, sort_keys=True)
```
or preserve the dict for validation but stringify in a controlled way just before the LLM call path.

## 2. Keep prompt/workflow creation simple

Since prompt_id is just an FK and not a template system, Codex should create one minimal prompt/workflow record for the MVP rather than invent a prompt framework.
