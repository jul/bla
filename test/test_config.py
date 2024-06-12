#/usr/bin/env python
from __future__ import print_function
import unittest
from os.path import join
import os
from bla import get_default_config, load_config, save_config


class TestConfig(unittest.TestCase):
    def id(self):
        return "CONFIG"
    def shortDescription(self):
        return self.id()

    def setUp(self):
        self.dir = "here"
        try:
            os.mkdir(self.dir)
        except Exception as e:
            pass
        self.ajson = join(self.dir, "a.json")
        with open(self.ajson, "w") as f:
            f.write("""{
    "ignore_missing": true,
    "debug": true,
    "search_scope": "SUBTREE",
    "auto_bind": true,
    "search_filter": "(objectClass=*)",
    "host": "ldap",
    "sasl_mechanism": "GSSAPI",
    "authentication": "SASL",
    "mail_search" : {
      "search_base" : "ou=People,%(search_base)s",
      "search_filter" : "(uid=*)",
      "attributes" : ["mail", "cn"],
      "search_scope" : "LEVEL"
     }
}
""")
        os.chmod(self.ajson, 0o0600)


    def test_load_config(self):
        os.chmod(self.ajson, 0o0660)
        with self.assertRaises(OSError):
            load_config(self.ajson)
        os.chmod(self.ajson, 0o0600)
        config = load_config(self.ajson)
        self.assertEqual(config["sasl_mechanism"], "GSSAPI")

    def test_save_yaml(self):
        config = load_config(self.ajson)
        yam = join(self.dir, "this.yaml")
        save_config(yam, config)
        config2 = load_config(yam)
        self.assertEqual(len(config), len(config2))
        for k, v in config.items():
            self.assertEqual(config2[k], v)


if __name__ == '__main__':
    unittest.main(verbosity=2)
