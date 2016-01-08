#!/bin/bash -e

# Script based upon mongodb installation at
# https://docs.mongodb.org/manual/tutorial/install-mongodb-on-ubuntu/

sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10

echo "deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.0.list

sudo apt-get update

sudo apt-get install -y -f mongodb-org=3.0.8 mongodb-org-shell=3.0.8 \
    mongodb-org-server=3.0.8 mongodb-org-mongos=3.0.8 mongodb-org-tools=3.0.8

echo "mongodb-org hold" | sudo dpkg --set-selections
echo "mongodb-org-server hold" | sudo dpkg --set-selections
echo "mongodb-org-shell hold" | sudo dpkg --set-selections
echo "mongodb-org-mongos hold" | sudo dpkg --set-selections
echo "mongodb-org-tools hold" | sudo dpkg --set-selections

sudo service mongod stop

mongod -f ./services/core/MongodbHistorian/tests/mongod.conf --auth --dbpath /tmp/data --bind_ip 127.0.0.1  &> /dev/null &
#sudo cp ./services/core/MongodbHistorian/tests/mongod.conf /etc/mongod.conf
#sudo chown root.root /etc/mongod.conf

#sudo service mongod restart
# Create users for the database.
mongo admin --eval 'db.createUser( {user: "mongodbadmin", pwd: "V3admin", roles: [ { role: "userAdminAnyDatabase", db: "admin" }]});'
mongo mongo_test -u mongodbadmin -p V3admin --authenticationDatabase admin --eval 'db.createUser( {user: "test", pwd: "test", roles: [ { role: "readWrite", db: "mongo_test" }]});'
