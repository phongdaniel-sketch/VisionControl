# Start with the Desktop

Add a Windows-only Settings checkbox with this exact label. Use the current
user Run registry entry named VisionControl; never request administrator rights
or touch other applications. Registry presence is the source of truth. Apply only
when saving a changed selection, not when opening Settings or cancelling.
Support packaged executable and source pythonw launch using absolute paths,
independent of current directory. Honor the existing Always start paused choice.
Read errors disable the checkbox with an explanation; write errors keep Settings
open. Tests mock registry operations and must not enable real login persistence.
