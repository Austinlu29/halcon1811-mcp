# Testing

## Unit tests

Install the package, then run:

```powershell
python -m unittest discover -s tests -v
```

Nine tests cover parameter validation, independent HDevelop/XML escaping, completion marker ordering,
unique task directories, path validation and program version/source/analysis preservation.
These tests do not require a HALCON installation.

## HALCON 18.11 validation

The original implementation was tested on Windows with Python 3.13.6 and HALCON 18.11 on 2026-10-09:

| Case | Observed result |
|---|---|
| Grayscale threshold demo | 2 objects |
| RGB threshold demo | 2 objects, same area/center results |
| Empty area selection | 0 objects and a CSV containing only its header |
| Keyboard execution | F5 was sent to the task's HDevelop window; execution completed |
| Invalid image data | HALCON error 5580, failure recorded without completion |
| Real stdio MCP workflow | Tools discovered; code saved/loaded; execution completed with 2 objects |

Runtime images, screenshots and machine-specific paths are intentionally excluded from the repository.
HALCON itself must be installed separately to reproduce integration checks.

## Reproduce an integration check

1. Configure `HALCON_HDEVELOP_EXE` and connect an MCP client.
2. Call `halcon_environment` and `halcon_operator_help` for `threshold`.
3. Call `generate_threshold_program` without an image path to create the demo image and source.
4. Save the generated source through `halcon_save_program` and inspect the `.hdev` in HDevelop.
5. Execute via `halcon_run_program`; query `halcon_execution_status` until completion or a failure.
6. Test a real RGB image, zero-region selection and invalid image data.

Interactive operators such as ROI drawing can stay waiting for user input. Syntax-loading errors must be inspected in HDevelop.
