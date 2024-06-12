cat <<EOF > cn\=config.ldif
dn: cn=config
cn: config
objectClass: olcGlobal

olcDatabase={0}config,cn=config
objectClass: olcDatabaseConfig
olcAccess: {-1}to * by * write by * read by * search ;
olcRootDN: cn=admin,cn=config
olcRootPW: aucun
olcDatabase: bdb
olcDbDirectory: ` pwd `/$1
olcSuffix: dc=here
EOF

/usr/sbin/slapd -d -1 -F $1 -u $USER -h ldap://127.0.0.1:6666 

