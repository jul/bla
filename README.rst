=======================
BLA : Brutal LDAP Admin
=======================


Synopsis
========

LDAP is a great extensible Entity Value (key/value storage) with security in mind. It's a great tool with a terrible User Experience when it comes to the tooling.


Why people (as I) are reluctant to use it ?


First problem CLI tools
***********************

- without kerberos CLI tools implies either to type password **for every
  operations (search, add modify)** or have it in
  seeable in history (if you don't use *secrets* my bash tool to solve this
  problem);
- who can remember what **-b, -x, -W, -w, -s** means ? CLI becames unreadable.

WE NEED A GOOD DSL (Domain specific language)

We also want history since we often make the same operation over and over again.



Second Problem
**************

LDAP is a NoSQL without fixed schema, but STRONGLY TYPED and with non intuitive behaviour:

Indexes behaviour
-----------------

unless explicitly told by default *description* fields and *aRecord*
(ip address) can only be searched on the base of exact value. For aRecord
it makes sense in terms of performance and use case (DNS backend), for 
descriptions it does not.

So how do you search for all descriptions were sysadmins lovingly put
informations about for whom a field was created in which context ?



Default settings
----------------

The size limits of 500 entries. Searching in the whole tree for one entry
if you don't exactly know what kind of object to search for will hit this limit.

Infuriating. Especially that permissions are in LDIF format and pretty hard to 
grock.

BLA is a path towards this
==========================

*brutal* a lib that intends to be usable out of the box to help develop tools.
*bla* a CLI tools using ipython for history, completion and documentation
*lhl* a web explorer

Design choices
**************

- GCU style to make a usable prototype to show the behaviour;
- except for ldap3 the cli tool uses only stdlib;
- using an implicit local or global configuration to setup the ldap 
  access/options;
- a templating tool to insert default on the fly that the library does not 
  support in order to easily craft your own request
- helpers to recursively search for any entries bypassing the 500 items limits
- *COLORS* because life is too short to have a monotone CLI (but actually
  does have it has a fallback mode)


Demo
====

example:

.. code-block:: bash

    # activate your virtual env
    python3 -mpip install .
    # standalone ldap server for tests
    ./bootstrap.sh slapd
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

    bla bla.json test.bla
    # fill in a password has demanded
    # exit
    # browse the tree
    lhl
    firefox http://127.0.0.1:5001


.. image:: ./img/screenshot.png

