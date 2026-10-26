"""Build F1_Strategy_Intelligence_Suite.ipynb from the files in cells/.

    python notebook/build_notebook.py

Files are taken in name order. A .md file becomes a Markdown cell. A .py file becomes a
code cell; its leading lines that start with `#>` become a Markdown cell placed above it.
"""
from pathlib import Path
import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

HERE = Path(__file__).parent
OUT = HERE / 'F1_Strategy_Intelligence_Suite.ipynb'


def split_header(src):
    lines = src.splitlines()
    head = []
    while lines and lines[0].startswith('#>'):
        head.append(lines.pop(0)[2:].removeprefix(' '))
    return '\n'.join(head), '\n'.join(lines).strip('\n')


def build():
    nb = new_notebook()
    for f in sorted((HERE / 'cells').iterdir()):
        src = f.read_text(encoding='utf-8')
        if f.suffix == '.md':
            nb.cells.append(new_markdown_cell(src.strip()))
        elif f.suffix == '.py':
            head, code = split_header(src)
            if head:
                nb.cells.append(new_markdown_cell(head))
            cell = new_code_cell(code)
            if '#@param' in code:
                cell.metadata['cellView'] = 'form'
            nb.cells.append(cell)
    nb.metadata = {'colab': {'provenance': [], 'toc_visible': True},
                   'kernelspec': {'name': 'python3', 'display_name': 'Python 3'},
                   'language_info': {'name': 'python'}}
    nbformat.write(nb, OUT)
    code = sum(c.cell_type == 'code' for c in nb.cells)
    print(f'{OUT.name}: {len(nb.cells)} cells ({code} code)')


if __name__ == '__main__':
    build()
