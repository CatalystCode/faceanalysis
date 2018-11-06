const fs = require('fs');
const path = require('path');
const metadataFile = path.join(__basedir, 'data/ttf-meta.json');

let provider = {}

module.exports = provider;

provider.getmetadata = function (callback) {
  fs.readFile(metadataFile, 'utf8', (err, fileContent) => {
    let metadata = {};
    if (!err) {
      metadata = JSON.parse(fileContent.toString());
      if (!metadata) {
        err = 'no metadata retrieved';
      }
    }
    callback(err, metadata);
  })
}

provider.getmetadatabyid = function (id, callback) {
  fs.readFile(metadataFile, 'utf8', (err, fileContent) => {
    let metadata = {};
    if (!err) {
      metadata = (JSON.parse(fileContent.toString())).metadata
        .filter(item => item.id === id);

      if (!metadata) {
        // return an error
        err = 'item not found';
      }
    }
    callback(err, { metadata });
  })
}
