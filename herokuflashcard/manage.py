#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    #default
    #os.environ.setdefault("DJANGO_SETTINGS_MODULE", "herokuflashcard.settings")

    #prod
    #os.environ.setdefault("DJANGO_SETTINGS_MODULE", "herokuflashcard.settings.prod")

    #dev
    #os.environ.setdefault("DJANGO_SETTINGS_MODULE", "herokuflashcard.settings.dev")

    #test
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "herokuflashcard.settings.test")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
