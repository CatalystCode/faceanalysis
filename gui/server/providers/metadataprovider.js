const fs = require('fs');
const path = require('path');
const csv = require('csvtojson');
const metadataFile = path.join(__basedir, 'data/ttf_records.csv');

module.exports.getmetadata = function(callback) {
    fs.readFile(metadataFile, 'utf8',(err, fileContent) => {
        if( err ) {
        } else {
            data = JSON.parse(fileContent.toString());
            metadata = data.metadata;

            if(metadata == ''){
                // return an error
                err = '';
            }
        
            callback(err, metadata);
        }
    })
}

module.exports.getmetadatabyid = function(id, callback) {
    fs.readFile(metadataFile, 'utf8',(err, fileContent) => {
        if( err ) {
        } else {
            data = JSON.parse(fileContent.toString());
            metadata = '';
            for(i = 0; i < data.metadata.length; i++)
            {
                row = data.metadata[i];
                if(row.id == id)
                metadata = row;
            }

            if(metadata == ''){
                // return an error
                err = '';
            }
        
            callback(err, metadata);
        }
    })
}
module.exports.getmetadata2 = function (callback) {
  let metadata = {}
  let error = ''

  if(path.extname(metadataFile) === '.json'){
    readJSONFile(metadataFile, (err, res) => {
      if(err) error = err;
      else
      callback(error, res);
    })
  } else if(path.extname(metadataFile) === '.csv') {
    readCSVFile(metadataFile, (err, res) => {
      if(err) error = err;
      else
      callback(error, res);
    })
  }
}

module.exports.getmetadatabyid2 = function (id, callback) {
  let metadata = {}
  let error = ''

  if(path.extname(metadataFile) === '.json'){
    readJSONFile(metadataFile, (err, res) => {
      if(err) error = err;
      else
      callback(error, res.filter(item => item.id === id));
    })
  } else if(path.extname(metadataFile) === '.csv') {
    readCSVFile(metadataFile, (err, res) => {
      if(err) error = err;
      else
      callback(error, res.filter(item => item.ImagePath === id));
    })
  }
}

function readJSONFile(filePath, callback){
  fs.readFile(filePath, 'utf8', (err, fileContent) => {
    let metadata = {};
    if (!err) {
      metadata = JSON.parse(fileContent.toString());
      if (!metadata) {
        err = 'data could not be parsed from file';
      }
    }
    callback(err, metadata);
  })
}

function readCSVFile(filePath, callback){
  let error = '';
  csv()
  .on('error',(err)=>{
    error = err;
  }) 
  .fromFile(filePath)
  .then((jsonObj)=>{
      callback(error, jsonObj); 
  })
}
