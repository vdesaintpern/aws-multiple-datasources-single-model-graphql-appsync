var AWS = require('aws-sdk');
var mysql = require('mysql');

var client = new AWS.SecretsManager({
  region: process.env.AWS_REGION
});

var connection = null;

async function connectToDb() {

  return client.getSecretValue({SecretId: process.env.SECRET_ARN}).promise()
    .then(function(data) {

      var secret= "{}";
    
      if ('SecretString' in data) {
          secret = data.SecretString;
      } 
    
      var secretParsed = JSON.parse(secret);
      password = secretParsed['password'];
      username = secretParsed['username'];
      host = secretParsed['host'];
      database = secretParsed['dbname'];
      port = secretParsed['port'];
    
      console.log("port" + port);

      connection = mysql.createConnection({
        user: username,
        host: host,
        database: database,
        password: password,
        port: port,
      });

      console.log(connection);

      return new Promise((resolve,reject) => {
        console.log("connecting");
        connection.connect(function(err){
          if(!err) {
            console.log("Database is connected ... nn");
            return resolve("")
          }
          else {
            console.log("Error connecting database ... ");
            console.log(err);
            return reject(err)
          }
        });
      });

    }, 
    function(error) {
      console.log(error);
    });

}

function executeSQL(connection, sql) {
  
  return new Promise((resolve,reject) => {
    connection.query(sql, (err, data) => {
      if (err) {
        console.log("********ERROR*******")
        console.log(err);
        return reject(err)
      }
      return resolve(data)
    } )
  })
}

function populateAndSanitizeSQL(sql, variableMapping, connection) {
  Object.entries(variableMapping).forEach(([key, value]) => {
    const escapedValue = value; // TODO: escape with connection
    sql = sql.replace(key, escapedValue);
  });

  return sql;
}

initDB = connectToDb();

exports.handler = async (event) => {

  // this resolves instantly the second time (promised is resolved)
  // TODO : is there to remove this call from the handler completely ?
  await initDB;

  console.log('Received event', JSON.stringify(event, null, 3));
  console.log(connection);

  const inputSQL = populateAndSanitizeSQL(event.sql, event.variableMapping, connection);
  let result = await executeSQL(connection, inputSQL);
  
  console.log(JSON.stringify(result, null, 3));

  console.log(result);

  return result;
};