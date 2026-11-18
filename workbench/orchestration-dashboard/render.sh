#!/bin/sh
# Re-render Thrum's dashboard into the workbench for preview.
here="$(cd "$(dirname "$0")" && pwd)"
cd "$here/../../skills/orchestration/build/scripts" && python3 -c "
import sys; sys.path.insert(0,'.')
import delivery_history as h; from pathlib import Path
h.render(Path.home()/'.orchestrate/history/thrum-54a0cc', Path('$here/preview.html'), meta={'project':'thrum','version':'2.5.0'})"
