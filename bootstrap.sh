[ -z $1 ] && {
    echo please give a dir for slapd standalone DB
    exit 1
}
echo F*ck apparmor prevents standalone slapd please install apparmor-utils
doas aa-disable slapd
USER=${USER:-openldap}
PASSWD=${PASSWD:-secret}

BASEDN="dc=home"
kill $( cat "`pwd`/$1/slapd.pid" )
rm $1 -rf 
[ -d $1 ] ||  mkdir $1
chmod 700 $1
cat <<SLAP > `pwd`/$1/slap.ldif
SLAP

cat << CONFIG > "`pwd`/config.ldif"
dn: cn=config
objectClass: olcGlobal
olcArgsFile: `pwd`/$1/slapd.args
olcPidFile: `pwd`/$1/slapd.pid

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


dn: olcDatabase=mdb,cn=config
objectClass: olcDatabaseConfig
objectClass: olcMdbConfig
olcDatabase: mdb
OlcDbMaxSize: 1073741824
olcSuffix: dc=home
olcRootDN: cn=root,dc=home
olcRootPW: `slappasswd -h {SHA} -s $PASSWD`
olcDbDirectory: `pwd`/$1
olcDbIndex: objectClass eq
olcDbIndex: uid pres,eq
olcDbIndex: mail pres,sub,eq
olcDbIndex: cn,sn pres,sub,eq
olcDbIndex: dc eq
olcAccess: to *
  by dn.exact=gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth manage
  by * break

dn: olcDatabase=config,cn=config
objectClass: olcDatabaseConfig
olcDatabase: config
#
# Define the root account of the config database
olcRootDN: cn=admin,cn=config
olcRootPW: secret
#
# The olcAccess rules do not apply to the rootDN.
# This line means that ONLY the rootDN will be allowed to connect to the database.
CONFIG
#cp config.ldif $1/cn=config.ldif
/usr/sbin/slapadd  -d 1 -n 0 -F $1  -l `pwd`/config.ldif
#/usr/sbin/slapadd  -d 1 -n 0 -F $1  -l `pwd`/config.ldif

echo $USER
/usr/sbin/slapd -u $USER  -F $1  -h ldap://127.0.0.1:6666 

