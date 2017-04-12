from os.path import dirname, join
from mock import patch, Mock
from StringIO import StringIO
from sys import getfilesystemencoding
from twisted.trial import unittest
from allmydata.scripts import runner
from allmydata.scripts.tahoe_daemonize import identify_node_type
from allmydata.scripts.tahoe_daemonize import DaemonizeTahoeNodePlugin
from allmydata.scripts.tahoe_daemonize import DaemonizeOptions


class Util(unittest.TestCase):

    def test_node_type_nothing(self):
        tmpdir = self.mktemp()
        base = dirname(tmpdir).decode(getfilesystemencoding())

        t = identify_node_type(base)

        self.assertIs(None, t)

    def test_node_type_introducer(self):
        tmpdir = self.mktemp()
        base = dirname(tmpdir).decode(getfilesystemencoding())
        with open(join(dirname(tmpdir), 'introducer.tac'), 'w') as f:
            f.write("test placeholder")

        t = identify_node_type(base)

        self.assertEqual(u"introducer", t)

    def test_daemonize(self):
        tmpdir = self.mktemp()
        plug = DaemonizeTahoeNodePlugin('client', tmpdir)

        with patch('twisted.internet.reactor') as r:
            def call(fn, *args, **kw):
                fn()
            r.callWhenRunning = call
            service = plug.makeService(None)
            service.parent = Mock()
            service.startService()

        self.assertTrue(service is not None)

    def test_daemonize_no_keygen(self):
        tmpdir = self.mktemp()
        plug = DaemonizeTahoeNodePlugin('key-generator', tmpdir)

        with patch('twisted.internet.reactor') as r:
            def call(fn, *args, **kw):
                fn()
            r.callWhenRunning = call
            service = plug.makeService(None)
            service.parent = Mock()
            with self.assertRaises(ValueError) as ctx:
                service.startService()
            self.assertIn(
                "key-generator support removed",
                str(ctx.exception)
            )

    def test_daemonize_unknown_nodetype(self):
        tmpdir = self.mktemp()
        plug = DaemonizeTahoeNodePlugin('an-unknown-service', tmpdir)

        with patch('twisted.internet.reactor') as r:
            def call(fn, *args, **kw):
                fn()
            r.callWhenRunning = call
            service = plug.makeService(None)
            service.parent = Mock()
            with self.assertRaises(ValueError) as ctx:
                service.startService()
            self.assertIn(
                "unknown nodetype",
                str(ctx.exception)
            )

    def test_daemonize_options(self):
        parent = runner.Options()
        opts = DaemonizeOptions()
        opts.parent = parent
        opts.parseArgs()

        # just gratuitous coverage, ensureing we don't blow up on
        # these methods.
        opts.getSynopsis()
        opts.getUsage()

    def test_daemonize_defaults(self):
        with patch('allmydata.scripts.tahoe_daemonize.twistd'):
            config = runner.parse_or_exit_with_explanation([
                'daemonize',
            ])
            i, o, e = StringIO(), StringIO(), StringIO()
            with patch('allmydata.scripts.runner.sys') as s:
                exit_code = [None]
                def _exit(code):
                    exit_code[0] = code
                s.exit = _exit
                runner.dispatch(config, i, o, e)

                self.assertEqual(0, exit_code[0])
