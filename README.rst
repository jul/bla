=======================
BLA : Brutal LDAP Admin
=======================

Trying to obtain a decent openLDAP shell with scripting abilities by piggybacking IPython bringing history and documentation as a bonus,
as well as python module to have an easy installation.

This project is a Dirty Hack.


How it works
============

All required files (including the tls pem/key for localhost at 127.0.0.1) are available
`here <https://github.com/jul/bla>`_


example:

.. code-block:: bash

    # activate your virtual env
    python3 -mpip install blabing
    # standalone ldap server for tests
    standalone_ldap.sh slap
    # calling bla with credentials for this server, and calling test.bla  
    # which creates ou=people,dc=home and create 3 users there
    cat bla.test
     ldap.add("dc=home", [ "dcObject", "organization", "top"], dict(dc="home", o="home"))
     ldap.add("ou=people,dc=home",  'organizationalUnit', dict(ou="people"))
     [ user_add(i) for i in ( "boss", "manager", "louis" ) ]
     ldap.add("ou=group,dc=home",  'organizationalUnit', dict(ou="group"))
     ldap.add("cn=staff,ou=group,dc=home",  ['top', "groupOfNames"],attributes= dict(member=["uid=boss,ou=people,dc=home" ]))
     search("(uid=boss)", attributes="memberOf")
     list(walk("dc=home",lambda e:e.entry_dn))
     pe(get("uid=boss,ou=people,dc=home"))
     password("uid=boss,ou=people,dc=home")
     pe(get("uid=boss,ou=people,dc=home"))

    bla bla.no_tls.json test.bla

    # fill in a password has demanded
    # try ldapvi("uid=boss") in the IPython shell
    # exit
    
    # browse the tree
    lhl bla.no_tls.json
    firefox http://127.0.0.1:5001


.. image:: ./img/screenshot.png

You should be focusing on the tree not on the options of the command line tools.

Synopsis
========

LDAP is a great extensible key/value storage with security in mind. It's a great tool with a terrible User Experience when it comes to the tooling especially with openLDAP.


Why people (as I) are reluctant to use it ?

First problem CLI: tools
************************

- without kerberos CLI tools implies either to type password **for every
  operations (search, add modify)** or have it in
  seeable in history (if you don't use *secrets* my bash tool to solve this
  problem);
- who can remember what **-b, -x, -W, -w, -s** means ? CLI becames unreadable.

Why not have create a DSL? (Domain specific language)

We also want history since we often make the same operation over and over again.


BLA is an experimentation at brewing your own tooling for openLDAP
==================================================================

*standalone_ldap.sh* a standalone LDAP server to experiment locally.
*bla* a CLI tools using ipython for history, completion and documentation
*lhl* a web explorer

Design choices
**************

- GCU style to make a usable prototype illustrating the indented behaviour fast;
- using an implicit local or global configuration to setup the ldap 
  access/options;
- helpers to recursively search for any entries bypassing the 500 items limits
- *COLORS* because life is too short to have a monotone CLI (but actually
  does have it has a fallback mode)


