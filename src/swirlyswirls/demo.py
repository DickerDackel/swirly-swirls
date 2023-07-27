import sys
import os.path
import argparse
import pygame

from importlib import import_module
from importlib.resources import contents
from types import SimpleNamespace

from pygamehelpers.framework import App

TITLE = 'swirlyswirls Demos'
SCREEN = pygame.rect.Rect(0, 0, 1024, 768)
FPS = 60


def main():
    cmdline = argparse.ArgumentParser(description='swirlyswirls demo runner')
    cmdline.add_argument('demo', type=str, nargs='?', help='Demo name.  Leave out to get list of demos.')
    opts = cmdline.parse_args(sys.argv[1:])

    if opts.demo is None:
        print('Available demos:')
        demos = [os.path.splitext(f)[0] for f in contents('swirlyswirls.demos') if not f.startswith('__')]
        for demo in demos:
            print(f'    {demo}')
        sys.exit(0)

    fullname = f'swirlyswirls.demos.{opts.demo}'
    try:
        imp = import_module(fullname)
    except ModuleNotFoundError as e:
        sys.exit(e)

    cls = getattr(imp, 'Demo')

    app = App(TITLE, SCREEN, FPS)

    persist = SimpleNamespace(
        font=pygame.Font(None),
    )

    states = { 'demo': cls(app, persist) }

    app.run('demo', states)


if __name__ == '__main__':
    main()
