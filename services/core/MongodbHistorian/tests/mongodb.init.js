var db = db.getSiblingDB('admin')
//db.adminCommand('listDatabases');
db.createUser( {
  user: "mongodbadmin",
  pwd: "V3admin",
  roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
});
db.createUser( {
  user: "test",
  pwd: "mongo_test_pw",
  roles: [ { role: "root", db: "admin" } ]
});
