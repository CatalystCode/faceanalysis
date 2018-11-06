const fs = require('fs');
const path = require('path');

const metadataFile = './gui/server/data/ttf-meta.json';

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