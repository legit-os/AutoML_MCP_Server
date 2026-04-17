from pathlib import Path
import sys
import os

# Add src to sys.path
sys.path.append(os.path.join(os.getcwd(), "src"))

from dist_automl.working_dir.dir_class import WorkingDirectory

def test_notebook():
    test_root = Path("test_project_root").resolve()
    if test_root.exists():
        import shutil
        shutil.rmtree(test_root)
    test_root.mkdir()
    
    wd = WorkingDirectory(project_root=test_root)
    
    # 1. Add a markdown cell
    print("Adding markdown cell...")
    res = wd.manage_notebook_cell(action="add", content="# Test Notebook", cell_type="markdown")
    print(res)
    
    # 2. Add a code cell
    print("Adding code cell...")
    res = wd.manage_notebook_cell(action="add", content="print('hello world')", cell_type="code")
    print(res)
    
    # 3. Read cells
    print("Reading cells...")
    cells = wd.manage_notebook_cell(action="read")
    for cell in cells:
        print(f"[{cell['index']}] {cell['type']}: {cell['source']}")
        
    # 4. Edit cell
    print("Editing cell 1...")
    res = wd.manage_notebook_cell(action="edit", index=1, content="print('hello universe')")
    print(res)
    
    # 5. Delete cell
    print("Deleting cell 0...")
    res = wd.manage_notebook_cell(action="delete", index=0)
    print(res)
    
    # 6. Read again
    print("Reading final cells...")
    cells = wd.manage_notebook_cell(action="read")
    for cell in cells:
        print(f"[{cell['index']}] {cell['type']}: {cell['source']}")

if __name__ == "__main__":
    test_notebook()
