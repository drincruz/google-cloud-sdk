# Copyright 2013 Google Inc. All Rights Reserved.

"""Does some initial setup and checks for all the bootstrapping scripts."""


import os
import sys

# If we're in a virtualenv, always import site packages. Also, upon request.
import_site_packages = (os.environ.get('CLOUDSDK_PYTHON_SITEPACKAGES') or
                        os.environ.get('VIRTUAL_ENV'))

if import_site_packages:
  # pylint:disable=unused-import
  # pylint:disable=g-import-not-at-top
  import site

# Put Cloud SDK libs on the path
root_dir = os.path.normpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '..', '..'))
lib_dir = os.path.join(root_dir, 'lib')
third_party_dir = os.path.join(lib_dir, 'third_party')

sys.path = [lib_dir, third_party_dir] + sys.path
# Add this so that all subprocess will have this on the path as well
python_path = os.environ.get('PYTHONPATH')
if python_path:
  os.environ['PYTHONPATH'] = os.pathsep.join(
      [lib_dir, third_party_dir, python_path])
else:
  os.environ['PYTHONPATH'] = os.pathsep.join([lib_dir, third_party_dir])


# This strange import below ensures that the correct 'google' is imported. We
# reload after sys.path and PYTHONPATH are updated, so we know if will find our
# google before any other.
# pylint:disable=g-import-not-at-top, must follow sys.path and PYTHONPATH logic.
if 'google' in sys.modules:
  import google
  if 'reload' in __builtins__:
    reload(google)
  else:
    import imp
    imp.reload(google)


# pylint: disable=g-import-not-at-top
from googlecloudsdk.core.util import platforms


# Add more methods to this list for universal checks that need to be performed
def DoAllRequiredChecks():
  if not platforms.PythonVersion().IsCompatible():
    sys.exit(1)
  if not platforms.Platform.Current().IsSupported():
    sys.exit(1)


DoAllRequiredChecks()
