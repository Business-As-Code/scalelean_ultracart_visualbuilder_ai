# Evidence model

Every lab observation must have a session identifier, timestamp, test-store
identifier, observer, and one of these classifications:

| Classification | Meaning |
| --- | --- |
| Verified | A controlled test directly supports the stated relationship. |
| Hypothesis | The relationship is plausible but has not passed a controlled test. |
| Unknown | The current evidence cannot establish the relationship. |

## Evidence surfaces

Record the following as independent surfaces:

1. Browser editor state and available controls.
2. JSON or metadata observable through an approved interface.
3. File-transfer listing or downloaded bytes from an approved private capture.
4. Public or test-store rendered HTML and visual output.

Do not put raw captures in this repository. A manifest may include relative
path, byte count, timestamp, and SHA-256 hash when those values do not expose
private source material.
