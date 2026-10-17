from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).resolve().with_name('build_v5_walkthroughs.py')))
