#!/usr/bin/env bash
:<< =cut

=head1 SYNOPSIS

[USER=$USER] [PORT=6666] [IP=127.0.0.1] [PASSWORD=secret] [BASEDN="dc=home"]  bootstrap.sh DIRECTORY

bootstrap a standalone ldap server on given port and address with all data in DIRECTORY

=head2 OPTIONS

=over

=item USER

User with which slapd runs

=item PORT

Port slapd will listen too

=item IP

IP for slapd

=item PASSWORD

Password for manager with dn cn=root,dc=BASEDN

=item BASEDN

The base DN (distringuished name) you choose for your LDAP configuration

=back

=head1 REFERENCES

This script embed the nuggets of wisdom disseminated there :

=over

=item official openldap "quick"start, lol

L<https://www.openldap.org/doc/admin25/quickstart.html>

=item the always excellent gentoo documentation (read discussion)

L<https://wiki.gentoo.org/wiki/OpenLDAP>

=item the always excellent archlinux documentation

L<https://wiki.archlinux.org/title/openLDAP>

=back

=cut

PORT=${PORT:-6666}
IP=${IP:-127.0.0.1}
PASSWD=${PASSWD:-secret}
BASEDN="dc=home"


[ -z $1 ] && {
    perldoc $0 || head -n 56 $0
    exit 1
}
echo F*ck apparmor prevents standalone slapd please install apparmor-utils
doas aa-disable slapd
kill $( cat "`pwd`/$1/slapd.pid" )
echo last chance to hit ctrl + C before destroying \"$1\"
read -r a
rm "$1" -rf 
[ -d "$1" ] ||  mkdir "$1"
chmod 700 "$1"

cat << CONFIG > "`pwd`/initial.ldif"
dn: cn=config
objectClass: olcGlobal
olcArgsFile: `pwd`/$1/slapd.args
olcPidFile: `pwd`/$1/slapd.pid
olcTLSCACertificateFile: `pwd`/RootCA.pem
olcTLSCertificateFile: `pwd`/localhost.home.crt
olcTLSCertificateKeyFile: `pwd`/localhost.home.key
olcTLSProtocolMin: 3.1

dn: cn=schema,cn=config
objectClass: olcSchemaConfig
cn: schema

include: file:///etc/ldap/schema/core.ldif
# RFC1274: Cosine and Internet X.500 schema
include: file:///etc/ldap/schema/cosine.ldif
# Check RFC2307bis for nested groups and an auxiliary posixGroup objectClass (way easier)
include: file:///etc/ldap/schema/nis.ldif
# RFC2798: Internet Organizational Person
include: file:///etc/ldap/schema/inetorgperson.ldif

dn: cn=module,cn=config
objectClass: olcModuleList
cn: module
olcModulePath: /usr/lib/ldap/
olcModuleLoad: back_mdb.so
olcModuleLoad: memberof.la
olcModuleLoad: ppolicy


dn: olcDatabase=mdb,cn=config
objectClass: olcDatabaseConfig
objectClass: olcMdbConfig
olcDatabase: mdb
OlcDbMaxSize: 1073741824
olcSuffix: dc=home
olcRootDN: cn=root,$BASEDN
olcRootPW: `slappasswd -h {SHA} -s $PASSWD`
olcDbDirectory: `pwd`/$1
olcDbIndex: objectClass eq
olcDbIndex: uid pres,eq
olcDbIndex: mail pres,sub,eq
olcDbIndex: cn,sn pres,sub,eq
olcDbIndex: dc eq
olcAccess: {0}to *
  by dn.exact=gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth manage
  by * break
olcAccess: {1}to dn.children="ou=people,dc=home" attrs=userPassword,shadowExpire,shadowInactive,shadowLastChange,shadowMax,shadowMin,shadowWarning
  by self write
  by anonymous auth


dn: olcOverlay={0}memberof,olcDatabase={1}mdb,cn=config
objectClass: olcConfig
objectClass: olcMemberOf
objectClass: olcOverlayConfig
objectClass: top
olcOverlay: memberof
olcMemberOfDangling: ignore
olcMemberOfRefInt: TRUE
olcMemberOfGroupOC: groupOfNames
olcMemberOfMemberAD: member
olcMemberOfMemberOfAD: memberOf

dn: olcOverlay={1}ppolicy,olcDatabase={1}mdb,cn=config
objectClass: olcOverlayConfig
objectClass: olcPPolicyConfig
olcOverlay: {1}ppolicy
olcPPolicyHashCleartext: TRUE

CONFIG
/usr/sbin/slapadd  -n 0 -F $1  -l `pwd`/initial.ldif

/usr/sbin/slapd  -u $USER  -F $1  -h ldap://$IP:$PORT &

