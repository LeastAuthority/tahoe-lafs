Developer Guide
===============

Continuous Integration
----------------------

Tahoe uses several CI services to avoid regressions.

GitHub Actions
~~~~~~~~~~~~~~

This service is used for Windows and macOS continuous integration.
It runs the test suite and some package building tasks.
It also collects coverage information and reports it to `Coveralls`_.
This service is configured in ``.github/workflows``.

CircleCI
~~~~~~~~

This service is used for Linux continuous integration.
It runs the test suite and some package building tasks as well as some static code analysis checks.
It does not currently collect coverage information due to the difficulty of reporting information to `Coveralls`_ from more than one CI provider.
This service is configured in ``.circleci``.

Coveralls
~~~~~~~~~

This service receives coverage information from CI jobs.
It uses this to create reports and publishes them `on the web <https://coveralls.io/github/tahoe-lafs/tahoe-lafs>`_.

It can also send coverage summaries and statuses to GitHub PRs.
This only seems to work reliably for PRs for in-repo branches.
If your PR is for a branch in a fork you may have to visible the coveralls website.

Pre-commit Checks
-----------------

This project is configured for use with `pre-commit`_ to install `VCS/git hooks`_ which perform some static code analysis checks and other code checks to catch common errors.
These hooks can be configured to run before commits or pushes

For example::

  tahoe-lafs $ pre-commit install --hook-type pre-push
  pre-commit installed at .git/hooks/pre-push
  tahoe-lafs $ echo "undefined" > src/allmydata/undefined_name.py
  tahoe-lafs $ git add src/allmydata/undefined_name.py
  tahoe-lafs $ git commit -a -m "Add a file that violates flake8"
  tahoe-lafs $ git push
  codechecks...............................................................Failed
  - hook id: codechecks
  - exit code: 1

  GLOB sdist-make: ./tahoe-lafs/setup.py
  codechecks inst-nodeps: ...
  codechecks installed: ...
  codechecks run-test-pre: PYTHONHASHSEED='...'
  codechecks run-test: commands[0] | flake8 src/allmydata/undefined_name.py
  src/allmydata/undefined_name.py:1:1: F821 undefined name 'undefined'
  ERROR: InvocationError for command ./tahoe-lafs/.tox/codechecks/bin/flake8 src/allmydata/undefined_name.py (exited with code 1)
  ___________________________________ summary ____________________________________
  ERROR:   codechecks: commands failed

To uninstall::

  tahoe-lafs $ pre-commit uninstall --hook-type pre-push
  pre-push uninstalled



.. _`pre-commit`: https://pre-commit.com
.. _`VCS/git hooks`: `pre-commit`_
.. _`pre-commit configuration`: ../.pre-commit-config.yaml
